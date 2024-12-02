from .models import Customer, Account
from sqlalchemy.exc import NoResultFound
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

from flask import jsonify
from sqlalchemy.orm import joinedload
import os
from app.database import db
import hashlib
import logging
logger = logging.getLogger(__name__)

PRIVATE_KEY_PATH = os.path.join(os.getcwd(), 'keys', 'private_key.pem')
PUBLIC_KEY_PATH = os.path.join(os.getcwd(), 'keys', 'public_key.pem')

def get_customer_id(email):
    try:
        # Log the attempt to retrieve customer ID
        logger.info(f"Attempting to retrieve customer ID for email: {email}")
        
        # Query the database for a customer with the given email
        # The .one() method ensures we get exactly one result or raise an exception
        customer = Customer.query.filter_by(email=email).one()
        
        # Log successful retrieval of customer ID
        logger.info(f"Customer ID for email {email} found: {customer.customer_id}")
        
        # Return the customer ID
        return customer.customer_id
    
    except NoResultFound:
        # Handle the case where no customer is found with the given email
        logger.error(f"No customer found with email: {email}")
        return None
    
    except Exception as e:
        # Handle any other unexpected errors
        logger.exception(f"Error while retrieving customer ID for email {email}: {e}")
        return None


def get_customer_accounts(email):
    """
    Retrieve account details for a customer using their email address.

    Args:
        email (str): The email address of the customer.

    Returns:
        dict: A dictionary containing customer details and their associated accounts.
        None: If no customer is found or an exception occurs.
    """
    try:
        # Log the beginning of the operation
        logger.info(f"Attempting to retrieve accounts for customer with email: {email}")
        
        # Query the database to find the customer by email and eagerly load their accounts
        customer = Customer.query.filter_by(email=email).options(joinedload(Customer.accounts)).first()
        
        # If no customer is found, log a warning and return None
        if not customer:
            logger.warning(f"No customer found with email: {email}")
            return None
        
        # Prepare customer and account information as a dictionary
        accounts_info = {
            "customer": {
                "customer_id": customer.customer_id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "date_of_birth": customer.date_of_birth,
                "address": customer.address,
                "phone_number": customer.phone_number,
                "email": customer.email,
                "role": customer.role.name,  # Convert enum value to name
                "created_at": customer.created_at
            },
            "accounts": [
                {
                    "account_id": account.account_id,
                    "account_type": account.account_type.name,  # Convert enum value to name
                    "balance": account.balance,
                    "created_at": account.created_at,
                    "status": account.status
                }
                for account in customer.accounts  # Iterate through associated accounts
            ]
        }
        
        # Log successful retrieval of accounts
        logger.info(f"Successfully retrieved accounts for email: {email}")
        return accounts_info
    except Exception as e:
        # Log exception details if an error occurs
        logger.exception(f"Error while retrieving accounts for customer with email {email}: {e}")
        return None



def get_account_by_id(account_id):
    try:
        # Log the attempt to retrieve the account
        logger.info(f"Attempting to retrieve account by account_id: {account_id}")
        
        # Query the database for an account with the given account_id
        # The .one() method ensures we get exactly one result or raise an exception
        account = Account.query.filter_by(account_id=account_id).one()
        
        # Log successful retrieval of the account
        logger.info(f"Account found for account_id {account_id}")
        
        # Return the account object
        return account
    
    except NoResultFound:
        # Handle the case where no account is found with the given account_id
        logger.error(f"No account found with account_id: {account_id}")
        return None
    
    except Exception as e:
        # Handle any other unexpected errors
        logger.exception(f"Error while retrieving account with account_id {account_id}: {e}")
        return None


def update_account_balance(account_id, new_balance):
    try:
        logger.info(f"Attempting to update balance for account_id {account_id} to {new_balance}")
        account = Account.query.filter_by(account_id=account_id).one()
        
        # Update the balance field
        account.balance = new_balance
        
        # Commit the change to the database
        db.session.commit()
        
        logger.info(f"Successfully updated balance for account_id {account_id} to {new_balance}")
        return True  # Indicate success
    except NoResultFound:
        logger.error(f"No account found with account_id: {account_id} for balance update")
        return False
    except Exception as e:
        logger.exception(f"Error updating account balance for account_id {account_id}: {e}")
        db.session.rollback()
        return False
    

def hash_password(password: str) -> str:
# Create a SHA-256 hash object
    sha256 = hashlib.sha256()
    # Update the hash object with the password encoded to bytes
    sha256.update(password.encode('utf-8'))
    # Return the hexadecimal representation of the hashed password
    return sha256.hexdigest()


def calculate_mtbf(total_downtime, failure_count):
    # Check if there were any failures
    if failure_count > 0:
        # Calculate Mean Time Between Failures (MTBF) in minutes
        mtbf_minutes = (total_downtime / failure_count).total_seconds() / 60
        
        # If MTBF is more than 60 minutes, convert to hours
        if mtbf_minutes > 60:
            mtbf_hours = mtbf_minutes / 60
            # Log the MTBF in hours
            logger.info(f"MTBF calculated: {mtbf_hours:.2f} hours.")
            # Return MTBF in hours as JSON
            return jsonify({"MTBF": round(mtbf_hours, 2), "unit": "hours"})
        else:
            # Log the MTBF in minutes
            logger.info(f"MTBF calculated: {mtbf_minutes:.2f} minutes.")
            # Return MTBF in minutes as JSON
            return jsonify({"MTBF": round(mtbf_minutes, 2), "unit": "minutes"})
    else:
        # If no failures occurred, log and return appropriate message
        logger.info("No failures found.")
        return jsonify({"MTBF": "No failures found", "unit": None})
    
def encrypt_password(password: str) -> str:
    # Use the dynamic PUBLIC_KEY_PATH
    with open(PUBLIC_KEY_PATH, "rb") as key_file:
        public_key = load_pem_public_key(key_file.read())

    # Encrypt the password using the public key
    encrypted = public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted.hex()

def decrypt_password(encrypted_password: str) -> str:
    # Use the dynamic PRIVATE_KEY_PATH
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = load_pem_private_key(
            key_file.read(),
            password=None,  # Add a password if your private key is password-protected
        )

    # Convert the encrypted password from hex to bytes
    encrypted_password_bytes = bytes.fromhex(encrypted_password)

    # Decrypt the password using the private key
    decrypted = private_key.decrypt(
        encrypted_password_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted.decode()


   