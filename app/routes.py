from flask import Blueprint, request, render_template, flash, redirect, url_for,jsonify
from .database import db
from .models import  Customer, UserRole, Account
from .services import get_customer_id, get_customer_accounts,update_account_balance,get_account_by_id,hash_password,calculate_mtbf,encrypt_password,decrypt_password
from datetime import datetime, timezone
from datetime import datetime, timedelta 
import uuid
import logging
import hashlib
from .secure_log import tamper_proof_log
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
                tamper_proof_log(logger, 'warning', "Duplicate email entered.")
                flash("This email is already registered. Please use a different email.", "danger")
                return render_template("new_user.html")

            # Log the action of creating a new customer
            hashed_password = encrypt_password(form_data['password'])
            tamper_proof_log(logger, 'info', f"Plain password: {form_data['password']}")
            tamper_proof_log(logger, 'info', f"Hashed password: {hashed_password}")
            tamper_proof_log(logger, 'info', "Starting process to create a new customer.")

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
                tamper_proof_log(logger, 'info', "Customer added to database successfully.")
                flash('Customer registered successfully!', 'success')
                return render_template('customer_details.html')  # Redirect to the transaction page
            except Exception as e:
                # Log the exception and rollback
                tamper_proof_log(logger, 'exception', f"Error occurred while registering new customer: {str(e)}")
                db.session.rollback()
                flash('Error registering customer: ' + str(e), 'danger')
                return render_template('new_user.html')

        else:
            # Log an info message when an existing customer attempts to log in
            tamper_proof_log(logger, 'info', "Attempting to log in existing customer.")
            email = request.form.get('email')
            password = request.form.get('password')
            customer = Customer.query.filter_by(email=email).first()

            if customer and form_data['password'] == decrypt_password(password):
                tamper_proof_log(logger, 'info', "Customer login successful.")
                return render_template('customer_details.html')
            else:
                # Log a warning if login fails
                tamper_proof_log(logger, 'warning', "Customer login failed due to incorrect email or password.")
                flash('User password or email is incorrect', 'danger')
                return render_template('existing_user.html')

    else:
        # Log an info message if the request method is not POST
        tamper_proof_log(logger, 'info', "GET request received, redirecting to home page.")
        return render_template('home.html')


@main.route('/new-customer')
def new_customer():
    return render_template('new_customer.html')


@main.route('/existing-customer')
def existing_customer():
    return render_template('existing_customer.html')


@main.route('/do-transciction', methods=['GET', 'POST'])
def transaction101():
    # Handle GET request
    if request.method == 'GET':
        # Retrieve email from query parameters
        email = request.args.get('email')
        if not email:
            # Log error and redirect if email is missing
            logger.error("Email is required for transactions but was not provided.")
            flash("Email is required to do transactions.", "error")
            return redirect(url_for('main.customer_details'))
        
        logger.info(f"Fetching accounts for email: {email}")
        # Get all accounts for the customer
        all_acc = get_customer_accounts(email)
        
        if not all_acc:
            # Handle case where no accounts are found
            logger.warning(f"No accounts found for email: {email}. Suggesting account creation.")
            flash("Please create an account to do transactions.", "error")
            return render_template('customer_details.html')
        else:
            # Extract accounts from the response
            all_acc1 = all_acc['accounts']
            logger.debug(f"Accounts retrieved for email {email}: {all_acc1}")
            return render_template('transaction.html', all_acc1=all_acc1)
    
    # Handle POST request
    else:
        # Retrieve form data
        form_data = request.form
        logger.debug(f"Form data received: {form_data}")
        
        # Extract transaction details from form data
        account_id = form_data.get('account')
        amount = float(form_data.get('amount'))
        option = form_data.get('option')
        email = form_data['email']
        
        logger.info(f"Processing transaction for email: {email}, account: {account_id}, amount: {amount}, option: {option}")
        
        # Fetch customer accounts again
        all_acc = get_customer_accounts(email)
        if not all_acc:
            # Handle case where no accounts are found
            logger.warning(f"No accounts found for email: {email}. Suggesting account creation.")
            flash("Please create an account to do transactions.", "error")
            return render_template('customer_details.html')
        else:
            all_acc1 = all_acc['accounts']
        
        # Retrieve the specific account for the transaction
        account = get_account_by_id(account_id)
        if not account:
            # Handle case where account is not found
            logger.error(f"Account with ID {account_id} not found.")
            flash("Account not found.", "error")
            return render_template('transaction.html', all_acc1=all_acc1)
        
        # Perform deposit or withdrawal based on option
        if option == 'deposit':
            # Handle deposit
            account.balance += amount
            logger.info(f"Deposited Rs. {amount} to {account.account_type} account with ID {account_id}. New balance: {account.balance}")
            flash(f"Deposited $. {amount} to {account.account_type} account.", "success")
        
        elif option == 'withdraw':
            # Handle withdrawal
            if account.balance >= amount:
                account.balance -= amount
                logger.info(f"Withdrew $. {amount} from {account.account_type} account with ID {account_id}. New balance: {account.balance}")
                flash(f"Withdrew Rs. {amount} from {account.account_type} account.", "success")
            else:
                # Handle insufficient balance
                logger.warning(f"Insufficient balance for withdrawal from account ID {account_id}. Balance: {account.balance}, Attempted withdrawal: {amount}")
                flash("Insufficient balance for withdrawal.", "error")
                return render_template('transaction.html', all_acc1=all_acc1)
        
        # Update account balance in the database
        update_account_balance(account_id, account.balance)
        logger.info(f"Updated balance for account ID {account_id} to {account.balance}")
        
        # Get the updated accounts for this email
        all_acc = get_customer_accounts(email)
        all_acc1 = all_acc['accounts']
        
        # Render the transaction page with updated account information
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
    
    # Initialize variables for tracking downtime and failures
    total_downtime, failure_count, previous_timestamp = timedelta(0), 0, None
    
    # Construct the path to the log file
    log_file_path = os.path.join(os.path.dirname(__file__), '../app.log')
    
    # Regular expression to match timestamp at the beginning of each log line
    timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    
    try:
        # Open and read the log file
        with open(log_file_path, 'r') as file:
            for line in file:
                # Try to match the timestamp pattern at the start of each line
                match = timestamp_pattern.match(line)
                if match:
                    # Parse the timestamp if a match is found
                    current_timestamp = datetime.strptime(match.group(0), '%Y-%m-%d %H:%M:%S')
                    
                    # Check for downtime (gap of more than 2 minutes between log entries)
                    if previous_timestamp and (current_timestamp - previous_timestamp > timedelta(minutes=2)):
                        total_downtime += current_timestamp - previous_timestamp
                        failure_count += 1
                        logger.debug(f"Downtime detected. Time difference: {current_timestamp - previous_timestamp}")
                    
                    # Update the previous timestamp for the next iteration
                    previous_timestamp = current_timestamp
    
    except FileNotFoundError:
        # Handle case where log file is not found
        logger.error("Log file not found. Ensure 'app.log' exists in the correct directory.")
        return jsonify({"error": "Log file not found"}), 404
    
    except Exception as e:
        # Handle any other exceptions that occur during file parsing
        logger.exception("An error occurred during log file parsing.")
        return jsonify({"error": "Error generating report"}), 500

    # Calculate Mean Time Between Failures (MTBF)
    mtbf = (total_downtime / failure_count).total_seconds() / 60 if failure_count > 0 else 'No failures found'
    
    # Log the calculated MTBF
    logger.info(f"MTBF calculated: {mtbf} minutes." if isinstance(mtbf, float) else mtbf)
    
    # Return the calculated MTBF using the calculate_mtbf function
    return calculate_mtbf(total_downtime, failure_count)


# secure_log.py
@main.route('/verify-log',methods=['POST'])
def verify_log_integrity():
    """Verify the integrity of the log file by checking the hash chain."""
    log_file_path = os.path.join(os.path.dirname(__file__), '../app.log')

    # Check if the log file exists
    if not os.path.exists(log_file_path):
        return jsonify({'error': 'Log file not found'}), 404

    try:
        with open(log_file_path, 'r') as f:
            previous_hash = None

            for line_number, line in enumerate(f, start=1):
                # Extract the current log entry and hash from the line
                parts = line.split(' - Hash: ')

                # If the line does not contain ' - Hash:', it is malformed
                if len(parts) != 2:
                    logger.warning(f"Malformed log entry at line {line_number}: {line.strip()}")
                    continue  # Skip this line and move on to the next one

                log_entry = parts[0]
                current_hash = parts[1].strip()

                # If this is not the first entry, verify the previous hash matches
                if previous_hash:
                    calculated_hash = hashlib.sha256(f"{log_entry} - Previous Hash: {previous_hash}".encode('utf-8')).hexdigest()
                    if calculated_hash != current_hash:
                        logger.error(f"Integrity check failed at line {line_number}: {log_entry}")
                        return jsonify({'error': f'Integrity check failed at line {line_number}: {log_entry}'}), 400

                # Update the previous hash to the current hash
                previous_hash = current_hash

            return jsonify({'message': 'Log file integrity verified successfully'}), 200

    except Exception as e:
        logger.exception("Error verifying log file integrity")
        return jsonify({'error': f'An exception occurred: {str(e)}'}), 500





