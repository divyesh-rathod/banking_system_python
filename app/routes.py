from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from .database import db
from .models import User, Customer, UserRole, Account
from .services import get_customer_id, get_customer_accounts,update_account_balance,get_account_by_id
from datetime import datetime, timezone
import uuid
import json
import os

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('home.html')


@main.route('/new-user')
def new_user():
    return render_template('new_user.html')


@main.route('/existing-user')
def existing_user():
    return render_template('existing_user.html')


@main.route('/check', methods=['POST'])
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


@main.route('/customer-details', methods=['GET', 'POST'])
def customer_details():
    if request.method == 'POST':
        form_data = request.form
        type_value = form_data.get('type')
        if type_value != 'existing':
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
                return render_template('new_user.html')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            customer = Customer.query.filter_by(email=email).first()
            if customer and customer.password == password:
                return render_template('customer_details.html')
            else:
                flash('User password or email is incorrect')
                return render_template('existing_user.html')

    else:
        return render_template('home.html')


@main.route('/new-customer')
def new_customer():
    return render_template('new_customer.html')


@main.route('/existing-customer')
def existing_customer():
    return render_template('existing_customer.html')


@main.route('/do-transciction', methods=['GET', 'POST'])
def transaction101():
    if request.method == 'GET':
        email = request.args.get('email')
        if not email:
            # Handle missing email scenario
            flash("Email is required to do transactions.", "error")
            return redirect(url_for('main.customer_details'))
        all_acc = get_customer_accounts(email)
        if not all_acc:
            # Flash message and redirect to an HTML page suggesting account creation
            flash("Please create an account to do transactions.", "error")
            return render_template('customer_details.html')
        else:
            all_acc1 = all_acc['accounts']
            print(all_acc1)
            return render_template('transaction.html',all_acc1=all_acc1)
    else:
    
        # Retrieve data from form
        print(request.form)
        account_id = request.form.get('account')
        amount = float(request.form.get('amount'))
        option = request.form.get('option')
        form_data = request.form
        email = form_data['email']
        print(f"Email from form: {email}")
        all_acc = get_customer_accounts(email)
        if not all_acc:
            # Flash message and redirect to an HTML page suggesting account creation
            flash("Please create an account to do transactions.", "error")
            return render_template('customer_details.html')
        else:
            all_acc1 = all_acc['accounts']
        # Retrieve the account from the database using the account_id
        account = get_account_by_id(account_id)  # Define this function to retrieve the account details from the DB
        
        if not account:
            flash("Account not found.", "error")
            return render_template('transaction.html', all_acc1=all_acc1)

        # Perform deposit or withdrawal based on option
        if option == 'deposit':
            account.balance += amount 
            flash(f"Deposited Rs. {amount} to {account.account_type} account.", "success")
        elif option == 'withdraw':
            if account.balance >= amount:
                account.balance -= amount
                flash(f"Withdrew Rs. {amount} from {account.account_type} account.", "success")
            else:
                flash("Insufficient balance for withdrawal.", "error")
                return render_template('transaction.html', all_acc1=all_acc1)
        
        # Update account balance in the database
        update_account_balance(account_id, account.balance)  # Define this function to save the updated balance
        all_acc = get_customer_accounts(email)  # Get the updated accounts for this email
        all_acc1 = all_acc['accounts']
        return render_template('transaction.html', all_acc1=all_acc1)

        


@main.route('/transaction', methods=['GET', 'POST'])
def transaction():
    global acc_num_global
    if request.method == 'POST':
        customer = {}
        if os.path.exists('customer.json'):
            with open('customer.json') as customer_file:
                customer = json.load(customer_file)
        if request.form['type'] == 'new':
            customer[request.form['acc_num']] = {'name': request.form['name'],
                                                 'number': request.form['acc_num'], 'balance': request.form['balance']}
            with open('customer.json', 'w') as customer_file:
                json.dump(customer, customer_file)
        if request.form['type'] == 'existing':
            if request.form['acc_num'] not in customer:
                flash('Access Denied!!')
                flash('Incorrect Account Number')
                return render_template('existing_customer.html')
        acc_num_global = request.form['acc_num']
        return render_template('transaction.html', name=customer[acc_num_global]['name'],
                               number=customer[acc_num_global]['number'], balance=customer[acc_num_global]['balance'])
    else:
        return render_template('home.html')


@main.route('/add-account', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        form_data = request.form
        email = form_data['email']
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


@main.route('/transactions', methods=['GET', 'POST'])
def transactions():
    global acc_num_global
    if request.method == 'POST':
        customer = {}
        if os.path.exists('customer.json'):
            with open('customer.json', 'r') as customer_file:
                customer = json.load(customer_file)
        if request.form['option'] == 'deposit':
            customer[acc_num_global]['balance'] = str(
                int(customer[acc_num_global]['balance']) + int(request.form['amount']))
            flash('TRANSACTION SUCCESSFUL!!')
            flash('Amount Deposited: Rs. ' + str(request.form['amount']))
        if request.form['option'] == 'withdraw':
            if (int(customer[acc_num_global]['balance']) - int(request.form['amount'])) > 0:
                customer[acc_num_global]['balance'] = str(
                    int(customer[acc_num_global]['balance']) - int(request.form['amount']))
                flash('TRANSACTION SUCCESSFUL!!')
                flash('Amount Withdrawn: Rs. ' + str(request.form['amount']))
            else:
                flash('TRANSACTION FAILED!!')
                flash('Insufficient Balance')
        with open('customer.json', 'w') as customer_file:
            json.dump(customer, customer_file)
        return render_template('transaction.html', name=customer[acc_num_global]['name'],
                               number=customer[acc_num_global]['number'], balance=customer[acc_num_global]['balance'])
    else:
        return render_template('home.html')
