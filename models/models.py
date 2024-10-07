# models/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    type = db.Column(db.String(10), nullable=False)  # 'Income' or 'Expense'

    def __repr__(self):
        return f'<Category {self.name}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    description = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f'<Transaction {self.amount} on {self.date}>'

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: 'YYYY-MM'

    category = db.relationship('Category', backref=db.backref('budgets', lazy=True))

    def __repr__(self):
        return f'<Budget {self.amount} for {self.category.name} in {self.month}>'

class RecurringTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # e.g., 'Monthly', 'Weekly'
    next_date = db.Column(db.Date, nullable=False)

    category = db.relationship('Category', backref=db.backref('recurring_transactions', lazy=True))

    def __repr__(self):
        return f'<RecurringTransaction {self.amount} {self.frequency} on {self.next_date}>'
