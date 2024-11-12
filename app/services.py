from .models import Customer, Account
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload
from app.database import db
import logging
logger = logging.getLogger(__name__)

def get_customer_id(email):
    try:
        logger.info(f"Attempting to retrieve customer ID for email: {email}")
        customer = Customer.query.filter_by(email=email).one()
        logger.info(f"Customer ID for email {email} found: {customer.customer_id}")
        return customer.customer_id
    except NoResultFound:
        logger.error(f"No customer found with email: {email}")
        return None
    except Exception as e:
        logger.exception(f"Error while retrieving customer ID for email {email}: {e}")
        return None


def get_customer_accounts(email):
    try:
        logger.info(f"Attempting to retrieve accounts for customer with email: {email}")
        customer = Customer.query.filter_by(email=email).options(joinedload(Customer.accounts)).first()
        
        if not customer:
            logger.warning(f"No customer found with email: {email}")
            return None
        
        accounts_info = {
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
        
        logger.info(f"Successfully retrieved accounts for email: {email}")
        return accounts_info
    except Exception as e:
        logger.exception(f"Error while retrieving accounts for customer with email {email}: {e}")
        return None


def get_account_by_id(account_id):
    try:
        logger.info(f"Attempting to retrieve account by account_id: {account_id}")
        account = Account.query.filter_by(account_id=account_id).one()
        logger.info(f"Account found for account_id {account_id}")
        return account
    except NoResultFound:
        logger.error(f"No account found with account_id: {account_id}")
        return None
    except Exception as e:
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

