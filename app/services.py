from .models import Customer, Account
from sqlalchemy.exc import NoResultFound


def get_customer_id(email):
    try:
        customer = Customer.query.filter_by(email=email).one()
        return customer.customer_id
    except NoResultFound:
        return None


def get_customer_accounts(email):
    customer_id = get_customer_id(email)
    if customer_id is None:
        return None
    all_accounts = Account.query.filter_by(customer_id=customer_id).all()
    return all_accounts if all_accounts else None
