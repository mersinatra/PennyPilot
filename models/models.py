# models/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from enum import Enum

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'Income' or 'Expense'

    def __repr__(self):
        return f'<Category {self.name}>'

class RecurringTransaction(db.Model):
    __tablename__ = 'recurring_transaction'
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String(20), nullable=False)  # e.g., 'Monthly', 'Weekly'
    # Add other recurring-specific fields as necessary

    # Relationship to Transaction
    transactions = db.relationship('Transaction', backref='recurring_transaction', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.String(50))  # e.g., 'Income' or 'Expense'
    recurring = db.Column(db.Boolean, default=False)
    recurring_transaction_id = db.Column(db.Integer, db.ForeignKey('recurring_transaction.id'), nullable=True)  # Corrected ForeignKey

    # Relationship to Category
    category = db.relationship('Category', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f'<Transaction {self.id} - {self.amount} on {self.date}>'

class FrequencyEnum(Enum):
    Weekly = 'Weekly'
    Monthly = 'Monthly'
    Yearly = 'Yearly'    

class PeriodType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Budget(db.Model):
    __tablename__ = 'budget'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: 'YYYY-MM'

    category = db.relationship('Category', backref=db.backref('budgets', lazy=True))

    def __repr__(self):
        return f'<Budget {self.amount} for {self.category.name} in {self.month}>'
