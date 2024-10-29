# models/models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import date, datetime
from enum import Enum

db = SQLAlchemy()

class FrequencyEnum(Enum):
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'
    YEARLY = 'Yearly'    

class PeriodType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'Income' or 'Expense'

    # Relationship to Budget and Transaction
    budgets = db.relationship('Budget', backref='category', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship('Transaction', backref='category', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Category {self.name} - {self.type}>'


class RecurringTransaction(db.Model):
    __tablename__ = 'recurring_transaction'
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.Enum(FrequencyEnum), nullable=False)
    next_date = db.Column(db.Date, nullable=False, default=date.today)  # Next occurrence date
    description = db.Column(db.String(100), nullable=True)
    amount = db.Column(db.Float, nullable=False)

    # Relationship to Transaction
    transactions = db.relationship('Transaction', backref='recurring_transaction', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<RecurringTransaction {self.description} - {self.frequency}>'


class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'Income' or 'Expense'
    recurring = db.Column(db.Boolean, default=False)

    # Foreign keys with named constraints
    category_id = db.Column(
        db.Integer, 
        db.ForeignKey('category.id', ondelete='CASCADE', name='fk_transaction_category'),
        nullable=False
    )
    recurring_transaction_id = db.Column(
        db.Integer,
        db.ForeignKey('recurring_transaction.id', ondelete='SET NULL', name='fk_transaction_recurring'),
        nullable=True
    )

    def __repr__(self):
        return f'<Transaction {self.id} - {self.amount} on {self.date}>'


class Budget(db.Model):
    __tablename__ = 'budget'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: 'YYYY-MM'

    # Foreign key to Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f'<Budget {self.amount} for {self.category.name} in {self.month}>'
    

class SavingsAccount(db.Model):
    __tablename__ = 'savings_accounts'

    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)  # Default balance is 0.0

    def __repr__(self):
        return f'<SavingsAccount {self.account_name}, Balance: {self.balance}>'
