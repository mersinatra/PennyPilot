# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, send_file, make_response
from config import Config
from models.models import db, Transaction, Category, Budget, RecurringTransaction
from forms.forms import TransactionForm, BudgetForm, ImportForm
from utils.helpers import process_recurring_transactions
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import os
import csv
import json
import pandas as pd
from io import StringIO, BytesIO

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=process_recurring_transactions, trigger="interval", days=1)
scheduler.start()

# Ensure scheduler is shut down when exiting the app
import atexit
atexit.register(lambda: scheduler.shutdown())

# Create database tables and default categories
with app.app_context():
    db.create_all()
    # Initialize default categories if not present
    if not Category.query.first():
        default_categories = [
            Category(name='Salary', type='Income'),
            Category(name='Freelance', type='Income'),
            Category(name='Food', type='Expense'),
            Category(name='Rent', type='Expense'),
            Category(name='Utilities', type='Expense'),
            Category(name='Entertainment', type='Expense')
        ]
        db.session.add_all(default_categories)
        db.session.commit()

@app.route('/')
def dashboard():
    # Process recurring transactions before displaying dashboard
    process_recurring_transactions()

    # Fetch total income and expenses
    total_income = db.session.query(db.func.sum(Transaction.amount)).join(Category).filter(Category.type=='Income').scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).join(Category).filter(Category.type=='Expense').scalar() or 0
    balance = total_income - total_expense

    # Fetch expenses by category for visualization
    expenses = db.session.query(Category.name, db.func.sum(Transaction.amount)).join(Transaction).filter(Category.type=='Expense').group_by(Category.name).all()
    categories = [e[0] for e in expenses]
    amounts = [e[1] for e in expenses]

    # Fetch recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()

    # Fetch recurring transactions for the calendar
    recurring_transactions = RecurringTransaction.query.all()
    calendar_events = []
    for rt in recurring_transactions:
        event = {
            'title': f"{rt.description or 'Recurring Transaction'} - ${rt.amount}",
            'start': rt.next_date.strftime('%Y-%m-%d'),
            'category': rt.category.name
        }
        calendar_events.append(event)

    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        categories=categories,
        amounts=amounts,
        recent_transactions=recent_transactions,
        calendar_events=calendar_events
    )

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        # Create a new transaction
        transaction = Transaction(
            amount=form.amount.data,
            date=form.date.data,
            description=form.description.data,
            category_id=form.category.data
        )
        db.session.add(transaction)
        db.session.commit()

        flash('Transaction added successfully!', 'success')

        # If the transaction is recurring, create a RecurringTransaction entry
        if form.is_recurring.data:
            frequency = form.frequency.data
            next_date = form.next_date.data
            if frequency and next_date:
                recurring_txn = RecurringTransaction(
                    amount=form.amount.data,
                    description=form.description.data,
                    category_id=form.category.data,
                    frequency=frequency,
                    next_date=next_date
                )
                db.session.add(recurring_txn)
                db.session.commit()
                flash('Recurring transaction added successfully!', 'success')
            else:
                flash('Please provide frequency and next date for recurring transactions.', 'warning')

        return redirect(url_for('dashboard'))
    return render_template('add_transaction.html', form=form)

@app.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    form = TransactionForm(obj=transaction)
    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.date = form.date.data
        transaction.description = form.description.data
        transaction.category_id = form.category.data
        db.session.commit()

        flash('Transaction updated successfully!', 'success')

        # Check if this transaction has an associated recurring transaction
        recurring_txn = RecurringTransaction.query.filter_by(
            amount=transaction.amount,
            description=transaction.description,
            category_id=transaction.category_id
        ).first()

        if form.is_recurring.data:
            frequency = form.frequency.data
            next_date = form.next_date.data
            if frequency and next_date:
                if recurring_txn:
                    # Update existing recurring transaction
                    recurring_txn.frequency = frequency
                    recurring_txn.next_date = next_date
                else:
                    # Create new recurring transaction
                    new_recurring = RecurringTransaction(
                        amount=form.amount.data,
                        description=form.description.data,
                        category_id=form.category.data,
                        frequency=frequency,
                        next_date=next_date
                    )
                    db.session.add(new_recurring)
            else:
                flash('Please provide frequency and next date for recurring transactions.', 'warning')
        else:
            if recurring_txn:
                db.session.delete(recurring_txn)
        
        db.session.commit()

        return redirect(url_for('dashboard'))
    return render_template('edit_transaction.html', form=form, transaction=transaction)

@app.route('/delete/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    # Also delete associated recurring transaction if exists
    recurring_txn = RecurringTransaction.query.filter_by(
        amount=transaction.amount,
        description=transaction.description,
        category_id=transaction.category_id
    ).first()
    if recurring_txn:
        db.session.delete(recurring_txn)
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

# Budget Routes (Unchanged)

@app.route('/budgets')
def view_budgets():
    current_month = datetime.now().strftime('%Y-%m')
    budgets = Budget.query.filter_by(month=current_month).all()
    budget_data = []
    for budget in budgets:
        spent = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.category_id == budget.category_id,
            db.func.strftime('%Y-%m', Transaction.date) == budget.month
        ).scalar() or 0
        budget_data.append({
            'id': budget.id,
            'category': budget.category.name,
            'budget': budget.amount,
            'spent': spent,
            'remaining': budget.amount - spent
        })
    return render_template('view_budgets.html', budgets=budget_data, month=current_month)

@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    form = BudgetForm()
    if form.validate_on_submit():
        # Check if a budget for the category and month already exists
        existing_budget = Budget.query.filter_by(
            category_id=form.category.data,
            month=form.month.data
        ).first()
        if existing_budget:
            flash('A budget for this category and month already exists.', 'warning')
            return redirect(url_for('view_budgets'))
        budget = Budget(
            category_id=form.category.data,
            amount=form.amount.data,
            month=form.month.data
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget added successfully!', 'success')
        return redirect(url_for('view_budgets'))
    return render_template('add_budget.html', form=form)

@app.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
def edit_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    form = BudgetForm(obj=budget)
    if form.validate_on_submit():
        # Check if updating the budget would cause a duplicate
        existing_budget = Budget.query.filter_by(
            category_id=form.category.data,
            month=form.month.data
        ).first()
        if existing_budget and existing_budget.id != budget.id:
            flash('Another budget for this category and month already exists.', 'warning')
            return redirect(url_for('view_budgets'))
        budget.category_id = form.category.data
        budget.amount = form.amount.data
        budget.month = form.month.data
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('view_budgets'))
    return render_template('edit_budget.html', form=form, budget=budget)

@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully!', 'success')
    return redirect(url_for('view_budgets'))

# Removed Recurring Transactions Routes

# Data Export Routes (Unchanged)

@app.route('/export/<string:export_format>')
def export_data(export_format):
    transactions = Transaction.query.all()
    if export_format.lower() == 'csv':
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Amount', 'Date', 'Description', 'Category'])
        for txn in transactions:
            cw.writerow([txn.id, txn.amount, txn.date.strftime('%Y-%m-%d'), txn.description, txn.category.name])
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    elif export_format.lower() == 'json':
        data = []
        for txn in transactions:
            data.append({
                'id': txn.id,
                'amount': txn.amount,
                'date': txn.date.strftime('%Y-%m-%d'),
                'description': txn.description,
                'category': txn.category.name
            })
        output = make_response(json.dumps(data, indent=4))
        output.headers["Content-Disposition"] = "attachment; filename=transactions.json"
        output.headers["Content-type"] = "application/json"
        return output
    else:
        flash('Unsupported export format!', 'danger')
        return redirect(url_for('dashboard'))

# Data Import Route (Unchanged)

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename
        if filename.endswith('.csv'):
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            header = next(csv_input)
            for row in csv_input:
                if len(row) != 5:
                    continue  # Skip invalid rows
                _, amount, date_str, description, category_name = row
                category = Category.query.filter_by(name=category_name).first()
                if not category:
                    continue  # Skip if category does not exist
                transaction = Transaction(
                    amount=float(amount),
                    date=datetime.strptime(date_str, '%Y-%m-%d'),
                    description=description,
                    category_id=category.id
                )
                db.session.add(transaction)
            db.session.commit()
            flash('CSV data imported successfully!', 'success')
            return redirect(url_for('dashboard'))
        elif filename.endswith('.json'):
            data = json.load(file)
            for item in data:
                category = Category.query.filter_by(name=item['category']).first()
                if not category:
                    continue
                transaction = Transaction(
                    amount=float(item['amount']),
                    date=datetime.strptime(item['date'], '%Y-%m-%d'),
                    description=item['description'],
                    category_id=category.id
                )
                db.session.add(transaction)
            db.session.commit()
            flash('JSON data imported successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Unsupported file format!', 'danger')
            return redirect(url_for('import_data'))
    return render_template('import_data.html', form=form)

# Home route redirects to dashboard
@app.route('/home')
def home():
    return redirect(url_for('dashboard'))

# Error Handlers (Unchanged)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

# Ensure the app runs only if executed directly
if __name__ == '__main__':
    app.run(debug=True)
