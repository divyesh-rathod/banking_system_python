from .models import Customer, Account
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload
from app.database import db

def get_customer_id(email):
    try:
        customer = Customer.query.filter_by(email=email).one()
        return customer.customer_id
    except NoResultFound:
        return None


def get_customer_accounts(email):
    # Retrieve the customer along with all their accounts in a single query
    customer = Customer.query.filter_by(email=email).options(joinedload(Customer.accounts)).first()
    if not customer:
        return None

    # Structure the output to include customer and account details
    return {
        "customer": {
            "customer_id": customer.customer_id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "date_of_birth": customer.date_of_birth,
            "address": customer.address,
            "phone_number": customer.phone_number,
            "email": customer.email,
            "role": customer.role.name,
            "created_at": customer.created_at
        },
        "accounts": [
            {
                "account_id": account.account_id,
                "account_type": account.account_type.name,
                "balance": account.balance,
                "created_at": account.created_at,
                "status": account.status
            }
            for account in customer.accounts
        ]
    }
def get_account_by_id(account_id):
    try:
        # Query the Account table for the account with the given account_id
        account = Account.query.filter_by(account_id=account_id).one()
        return account
    except NoResultFound:
        # If no account is found, return None
        return None
    
def update_account_balance(account_id, new_balance):
    try:
        # Query the Account table for the account with the given account_id
        account = Account.query.filter_by(account_id=account_id).one()
        
        # Update the balance field
        account.balance = new_balance
        
        # Commit the change to the database
        db.session.commit()
        
        return True  # Indicate success
    except NoResultFound:
        # If no account is found, return False
        return False
    except Exception as e:
        # Handle any other exception, rollback in case of an error
        db.session.rollback()
        print(f"Error updating account balance: {e}")
        return False

