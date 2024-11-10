from flask import Flask, render_template, request, flash, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.exc import NoResultFound
from flask_migrate import Migrate
import enum
import uuid
import json
import os.path

app = Flask(__name__)
app.secret_key = '4u8a4ut5au1te51uea6u81e5a1u6d54n65at4y'

acc_num_global = {}
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+pg8000://postgres:postgres@localhost:5432/dummy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(200), nullable=False)

class UserRole(enum.Enum):
    CUSTOMER = "Customer"
    ADMIN = "Admin"
    MANAGER = "Manager"
    EMPLOYEE = "Employee"

class Customer(db.Model):
    __tablename__ = 'customers'
    customer_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    address = db.Column(db.Text)
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True)
    role = db.Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class AccountType(enum.Enum):
    SAVINGS = "Savings"
    CHECKING = "Checking"
    CURRENT = "Current"

class Account(db.Model):
    __tablename__ = 'accounts'
    account_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(UUID(as_uuid=True), ForeignKey('customers.customer_id'), nullable=False)
    account_type = db.Column(Enum(AccountType), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.Boolean, default=True)  # True for Active, False for Inactive

class TransactionType(enum.Enum):
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER = "Transfer"

class TransactionStatus(enum.Enum):
    COMPLETED = "Completed"
    PENDING = "Pending"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    transaction_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    to_account_id = db.Column(UUID(as_uuid=True), ForeignKey('accounts.account_id'), nullable=False)
    from_account_id = db.Column(UUID(as_uuid=True), ForeignKey('accounts.account_id'), nullable=False)
    transaction_type = db.Column(Enum(TransactionType), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(Enum(TransactionStatus), nullable=False)

def get_customer_id(email):
    try:
        customer = Customer.query.filter_by(email=email).one()  # Fetch the customer by email
        return customer.customer_id
    except NoResultFound:
        return None  # If customer not found, return None
def get_customer_accounts(email):
    try:
        customer_id = get_customer_id(email)
        if customer_id is None:
            return None  # No customer found with this email
        # Correct query to filter accounts by customer_id
        all_accounts = Account.query.filter_by(customer_id=customer_id).all()
        return all_accounts if all_accounts else None
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        return None
    

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/new-user')
def new_user():
    return render_template('new_user.html')


@app.route('/existing-user')
def existing_user():
    return render_template('existing_user.html')

@app.route('/check', methods=['POST'])
def check():
    data = request.get_json()

    # Get name and password from the request
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify({'error': 'Name and password are required.'}), 400

    # Create a new user and add to the database
    new_user = User(name=name, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully.'}), 201


@app.route('/customer-details', methods=['GET','POST'])
def customer_details():
    if request.method=='POST':
       form_data = request.form

       # Create a new Customer instance
       new_customer = Customer(
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            password=form_data['password'],  # Ideally, hash the password before storing
            date_of_birth=datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date(),
            address=form_data.get('address'),  # Address is optional
            phone_number=form_data.get('phone_number'),
            email=form_data.get('email'),
            role=UserRole.CUSTOMER,  # Or set from form_data if it's dynamic
            created_at=datetime.now(timezone.utc)
        )

        # Add and commit the new customer to the database
       try:
            db.session.add(new_customer)
            db.session.commit()
            flash('Customer registered successfully!', 'success')
            return redirect(url_for('customer_details.html'))  # Redirect to the transaction page
       except Exception as e:
            print(e)
            db.session.rollback()
            flash('Error registering customer: ' + str(e), 'danger')
            return render_template('customer_details.html')

    else:
        return render_template('home.html')


@app.route('/new-customer')
def new_customer():
    return render_template('new_customer.html')


@app.route('/existing-customer')
def existing_customer():
    return render_template('existing_customer.html')

@app.route('/do-transciction',methods=['GET','POST'])
def transaction101():
    if request.method=='Get':
        form_data = request.form
        email=form_data['email']
        all_acc= get_customer_accounts(email)
        if not all_acc:
            # Flash message and redirect to an HTML page suggesting account creation
            flash("Please create an account to do transactions.", "error")
            return render_template('customer_details.html')
        else:
            print(all_acc)
            return render_template('transaction.html',all_acc)



@app.route('/transaction', methods=['GET','POST'])
def transaction():
    global acc_num_global
    if request.method=='POST':
        customer={}
        if os.path.exists('customer.json'):
            with open('customer.json') as customer_file:
                customer=json.load(customer_file)
        if request.form['type'] == 'new':
            customer[request.form['acc_num']] = {'name' : request.form['name'],
                                                 'number' : request.form['acc_num'], 'balance' : request.form['balance']}
            with open('customer.json','w') as customer_file:
                json.dump(customer,customer_file)
        if request.form['type'] == 'existing':
            if request.form['acc_num'] not in customer:
                flash('Access Denied!!')
                flash('Incorrect Account Number')
                return render_template('existing_customer.html')
        acc_num_global = request.form['acc_num']
        return render_template('transaction.html',name=customer[acc_num_global]['name'],
                               number=customer[acc_num_global]['number'],balance=customer[acc_num_global]['balance'])
    else:
        return render_template('home.html')

@app.route('/add-account',methods=['GET','POST'])
def createAccount():
        if request.method=='POST':
            form_data = request.form
            email=form_data['email']
            customer_id = get_customer_id(email)
            if not customer_id:
               return {"success": False, "message": "Customer not found"}
            new_account = Account(
                    account_id=uuid.uuid4(),
                    customer_id=customer_id,
                    account_type=form_data['account_type'],
                    balance=form_data['balance'],
                    created_at=datetime.now(timezone.utc),
                    status=True
                    )

               # Add and commit to the database
            db.session.add(new_account)
            db.session.commit()
            return render_template('customer_details.html')
        else:
            return render_template('add_account.html')





@app.route('/transactions', methods=['GET','POST'])
def transactions():
    global acc_num_global
    if request.method == 'POST':
        customer = {}
        if os.path.exists('customer.json'):
            with open('customer.json','r') as customer_file:
                customer = json.load(customer_file)
        if request.form['option']=='deposit':
            customer[acc_num_global]['balance'] = str(int(customer[acc_num_global]['balance']) + int(request.form['amount']))
            flash('TRANSACTION SUCCESSFUL!!')
            flash('Amount Deposited: Rs. ' + str(request.form['amount']))
        if request.form['option']=='withdraw':
            if (int(customer[acc_num_global]['balance']) - int(request.form['amount'])) > 0:
                customer[acc_num_global]['balance'] = str(int(customer[acc_num_global]['balance']) - int(request.form['amount']))
                flash('TRANSACTION SUCCESSFUL!!')
                flash('Amount Withdrawn: Rs. ' + str(request.form['amount']))
            else:
                flash('TRANSACTION FAILED!!')
                flash('Insufficient Balance')
        with open('customer.json','w') as customer_file:
            json.dump(customer,customer_file)
        return render_template('transaction.html', name=customer[acc_num_global]['name'],
                               number=customer[acc_num_global]['number'], balance=customer[acc_num_global]['balance'])
    else:
        return render_template('home.html')


with app.app_context():
    db.create_all()

app.run(port=5055)