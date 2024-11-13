from flask import Blueprint, request, render_template, flash, redirect, url_for,jsonify
from .database import db
from .models import  Customer, UserRole, Account
from .services import get_customer_id, get_customer_accounts,update_account_balance,get_account_by_id,hash_password
from datetime import datetime, timezone
from datetime import datetime, timedelta 
import uuid
import logging
import re
import os
main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)



@main.route('/')
def home():
    return render_template('home.html')


@main.route('/new-user')
def new_user():
    return render_template('new_user.html')


@main.route('/existing-user')
def existing_user():
    return render_template('existing_user.html')

@main.route('/customer-details', methods=['GET', 'POST'])
def customer_details():
    if request.method == 'POST':
        form_data = request.form
        type_value = form_data.get('type')
        
        if type_value == 'new':
            existing_customer = Customer.query.filter_by(email=form_data.get('email')).first()
            if existing_customer:
                logger.warning("duplicate email enterd")
                flash("This email is already registered. Please use a different email.", "danger")
                return render_template("new_user.html")
            # Log the action of creating a new customer
            # Hash the password before storing
            hashed_password = hash_password(form_data['password'])
            logger.info("Starting process to create a new customer.")
            
            # Create a new Customer instance
            new_customer = Customer(
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                password=hashed_password,  # hash the password before storing
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
                logger.info("Customer added to database successfully.")
                flash('Customer registered successfully!', 'success')
                return render_template('customer_details.html')  # Redirect to the transaction page
            except Exception as e:
                # Log the exception and rollback
                logger.exception("Error occurred while registering new customer.")
                db.session.rollback()
                flash('Error registering customer: ' + str(e), 'danger')
                return render_template('new_user.html')
        
        else:
            # Log an info message when an existing customer attempts to log in
            logger.info("Attempting to log in existing customer.")
            email = request.form.get('email')
            password = request.form.get('password')
            customer = Customer.query.filter_by(email=email).first()
            hashed_password = hash_password(password)
            
            if customer and customer.password == hashed_password:
                logger.info("Customer login successful.")
                return render_template('customer_details.html')
            else:
                # Log a warning if login fails
                logger.warning("Customer login failed due to incorrect email or password.")
                flash('User password or email is incorrect')
                return render_template('existing_user.html')
    
    else:
        # Log an info message if the request method is not POST
        logger.info("GET request received, redirecting to home page.")
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
            logger.error("Email is required for transactions but was not provided.")
            flash("Email is required to do transactions.", "error")
            return redirect(url_for('main.customer_details'))
        
        logger.info(f"Fetching accounts for email: {email}")
        all_acc = get_customer_accounts(email)
        
        if not all_acc:
            logger.warning(f"No accounts found for email: {email}. Suggesting account creation.")
            flash("Please create an account to do transactions.", "error")
            return render_template('customer_details.html')
        else:
            all_acc1 = all_acc['accounts']
            logger.debug(f"Accounts retrieved for email {email}: {all_acc1}")
            return render_template('transaction.html', all_acc1=all_acc1)
    
    else:
        form_data = request.form
        logger.debug(f"Form data received: {form_data}")
        
        account_id = form_data.get('account')
        amount = float(form_data.get('amount'))
        option = form_data.get('option')
        email = form_data['email']
        
        logger.info(f"Processing transaction for email: {email}, account: {account_id}, amount: {amount}, option: {option}")
        
        all_acc = get_customer_accounts(email)
        if not all_acc:
            logger.warning(f"No accounts found for email: {email}. Suggesting account creation.")
            flash("Please create an account to do transactions.", "error")
            return render_template('customer_details.html')
        else:
            all_acc1 = all_acc['accounts']
        
        account = get_account_by_id(account_id)
        if not account:
            logger.error(f"Account with ID {account_id} not found.")
            flash("Account not found.", "error")
            return render_template('transaction.html', all_acc1=all_acc1)
        
        # Perform deposit or withdrawal based on option
        if option == 'deposit':
            account.balance += amount
            logger.info(f"Deposited Rs. {amount} to {account.account_type} account with ID {account_id}. New balance: {account.balance}")
            flash(f"Deposited $. {amount} to {account.account_type} account.", "success")
        
        elif option == 'withdraw':
            if account.balance >= amount:
                account.balance -= amount
                logger.info(f"Withdrew $. {amount} from {account.account_type} account with ID {account_id}. New balance: {account.balance}")
                flash(f"Withdrew Rs. {amount} from {account.account_type} account.", "success")
            else:
                logger.warning(f"Insufficient balance for withdrawal from account ID {account_id}. Balance: {account.balance}, Attempted withdrawal: {amount}")
                flash("Insufficient balance for withdrawal.", "error")
                return render_template('transaction.html', all_acc1=all_acc1)
        
        # Update account balance in the database
        update_account_balance(account_id, account.balance)
        logger.info(f"Updated balance for account ID {account_id} to {account.balance}")
        
        # Get the updated accounts for this email
        all_acc = get_customer_accounts(email)
        all_acc1 = all_acc['accounts']
        
        return render_template('transaction.html', all_acc1=all_acc1)



@main.route('/add-account', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        form_data = request.form
        email = form_data['email']
        
        logger.info(f"Attempting to create a new account for customer with email: {email}")
        
        customer_id = get_customer_id(email)
        if not customer_id:
            logger.error(f"Customer with email {email} not found. Account creation failed.")
            return {"success": False, "message": "Customer not found"}
        
        # Create new account
        new_account = Account(
            account_id=uuid.uuid4(),
            customer_id=customer_id,
            account_type=form_data['account_type'],
            balance=form_data['balance'],
            created_at=datetime.now(timezone.utc),
            status=True
        )

        try:
            # Add and commit to the database
            db.session.add(new_account)
            db.session.commit()
            logger.info(f"Account successfully created for customer {email}. Account ID: {new_account.account_id}")
            return render_template('customer_details.html')
        except Exception as e:
            logger.exception(f"Error occurred while creating account for customer {email}: {e}")
            db.session.rollback()
            return {"success": False, "message": "Error creating account. Please try again."}
    else:
        logger.info("Rendering account creation form")
        return render_template('add_account.html')
    
@main.route('/report',methods=['POST'])
def generate_report():
    logger.info("Starting report generation.")
    
    total_downtime = timedelta(0)
    failure_count = 0
    previous_timestamp = None
    log_file_path = os.path.join(os.path.dirname(__file__), '../app.log')
    
    # Define a regular expression to extract timestamps from each line
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    
    # Read and parse the log file
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                # Extract timestamp from each line
                match = timestamp_pattern.match(line)
                if match:
                    timestamp_str = match.group(0)
                    current_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    if previous_timestamp:
                        # Calculate the time difference
                        time_difference = current_timestamp - previous_timestamp
                        
                        # If downtime (failure) is more than 2 minutes, record it
                        if time_difference > timedelta(minutes=2):
                            total_downtime += time_difference
                            failure_count += 1
                            logger.debug(f"Downtime detected. Time difference: {time_difference}")
                    
                    # Update the previous timestamp
                    previous_timestamp = current_timestamp
    except FileNotFoundError:
        logger.error("Log file not found. Ensure 'app.log' exists in the correct directory.")
        return jsonify({"error": "Log file not found"}), 404
    except Exception as e:
        logger.exception("An error occurred during log file parsing.")
        return jsonify({"error": "Error generating report"}), 500

    # Calculate MTBF (in minutes)
    if failure_count > 0:
        mtbf = total_downtime / failure_count
        mtbf = mtbf.total_seconds() / 60  # Convert to minutes
        logger.info(f"MTBF calculated successfully. MTBF: {mtbf} minutes.")
    else:
        mtbf = "No failures found"
        logger.info("No failures found in log file; MTBF calculation skipped.")

    return jsonify({"MTBF": mtbf})




