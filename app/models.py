from .database import db
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.database import db
from datetime import datetime, timezone
import uuid
from sqlalchemy.dialects.postgresql import UUID


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
    accounts = relationship("Account", back_populates="customer")


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
    customer = relationship("Customer", back_populates="accounts")


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
