# app.py
import logging
from logging.handlers import RotatingFileHandler
from flask_migrate import Migrate
from flask import (Flask, render_template, redirect, url_for, flash, request, send_file, make_response, jsonify)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from config import Config
from models.models import db, Transaction, Category, Budget, RecurringTransaction
from forms.forms import TransactionForm, BudgetForm, ImportForm
from utils.helpers import process_recurring_transactions
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import extract
import os
import csv
import json
import pandas as pd
from io import StringIO, BytesIO
import atexit
import traceback

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
csrf = CSRFProtect(app)

migrate = Migrate(app, db)

# -------------------- Logging Configuration -------------------- #

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for comprehensive logging

# Create log directory if it doesn't exist
if not os.path.exists('logs'):
    os.mkdir('logs')

# File handler with rotation
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10*1024*1024, backupCount=5)
file_handler.setLevel(logging.INFO)  # File handler logs INFO and above

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Console handler logs DEBUG and above

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Application startup initiated.")

# -------------------- Scheduler Setup -------------------- #

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=process_recurring_transactions,
    trigger="interval",
    days=1,
    id='process_recurring_transactions',
    name='Process recurring transactions daily',
    replace_existing=True
)
scheduler.start()
logger.info("Background scheduler started.")

# Ensure scheduler is shut down when exiting the app
atexit.register(lambda: shutdown_scheduler())

def shutdown_scheduler():
    try:
        scheduler.shutdown()
        logger.info("Background scheduler shut down successfully.")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")
        logger.debug(traceback.format_exc())

# -------------------- Database Initialization -------------------- #

with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully.")
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
            logger.info("Default categories initialized.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        logger.debug(traceback.format_exc())

# -------------------- Routes -------------------- #

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

@app.route('/')
def dashboard():
    logger.debug("Accessed dashboard route.")
    try:
        # Removed: process_recurring_transactions()
        logger.debug("Skipped processing recurring transactions here.")

        # Fetch total income and expenses
        total_income = db.session.query(
            db.func.sum(Transaction.amount)
        ).join(Category).filter(Category.type == 'Income').scalar() or 0
        total_expense = db.session.query(
            db.func.sum(Transaction.amount)
        ).join(Category).filter(Category.type == 'Expense').scalar() or 0
        balance = total_income - total_expense
        logger.debug(f"Total income: {total_income}, Total expense: {total_expense}, Balance: {balance}")

        # Fetch expenses by category for visualization
        expenses = db.session.query(
            Category.name,
            db.func.sum(Transaction.amount)
        ).join(Transaction).filter(
            Category.type == 'Expense'
        ).group_by(Category.name).all()
        categories = [e[0] for e in expenses]
        amounts = [e[1] for e in expenses]
        logger.debug(f"Expenses by category: {dict(zip(categories, amounts))}")

        # Fetch recent transactions
        recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()
        logger.debug(f"Fetched {len(recent_transactions)} recent transactions.")

        # Fetch recurring transactions
        recurring_transactions = RecurringTransaction.query.all()
        calendar_events = []
        for rt in recurring_transactions:
            event = {
                'title': f"{rt.description} - ${rt.amount}",
                'start': rt.next_date.strftime('%Y-%m-%d'),
                'allDay': True
            }
            calendar_events.append(event) 
        logger.debug(f"Fetched {len(recurring_transactions)} recurring transactions for calendar events.")

        # Prepare data for the expenses chart
        categories = [category for category, amount in expenses]
        amounts = [amount for category, amount in expenses]

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
    except Exception as e:
        logger.error(f"Error in dashboard route: {e}")
        logger.debug(traceback.format_exc())
        flash('An error occurred while loading the dashboard.', 'danger')
        return render_template('500.html'), 500
    
# Transaction Routes

@app.route('/transactions', methods=['GET'])
def view_transactions():
    logger.debug("Accessed view_transactions route.")
    try:
        # Get the 'month' from query parameters, default to current month
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        # Validate 'month' format
        try:
            datetime.strptime(month_str, '%Y-%m')
            month = month_str
        except ValueError:
            logger.warning(f"Invalid month format received: {month_str}")
            flash('Invalid month format. Please use YYYY-MM.', 'warning')
            month = datetime.now().strftime('%Y-%m')

        # Extract year and month for filtering
        year, month_num = map(int, month.split('-'))

        # Optimize queries to prevent N+1 problem
        transactions = Transaction.query.filter(
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month_num
        ).join(Category).all()

        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'id': transaction.id,
                'date': transaction.date,
                'category': transaction.category.name,
                'description': transaction.description,
                'amount': transaction.amount,
                'type': transaction.type,
                'recurring': transaction.recurring
            })
                
            
        logger.debug(f"Fetched {len(transaction_data)} transactions for month {month}.")

        # Instantiate the TransactionForm to pass to the template
        form = TransactionForm()

        return render_template(
            'view_transactions.html',
            transactions=transaction_data,
            month=month,
            form=form  # Pass the form to the template
        )
    except Exception as e:
        logger.error(f"Error in view_transactions route: {e}")
        logger.debug(traceback.format_exc())
        flash('An error occurred while fetching transactions.', 'danger')
        return render_template('500.html'), 500


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    logger.debug("Accessed add_transaction route.")
    form = TransactionForm()
    if form.validate_on_submit():
        try:
            transaction = Transaction(
                date=form.date.data,
                category_id=form.category.data,
                description=form.description.data,
                amount=form.amount.data,
                type=form.type.data,  # Using 'type' as field name
                recurring=form.recurring.data
            )
            db.session.add(transaction)
            db.session.commit()
            logger.info(f"Added new transaction: {transaction}")
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('view_transactions'))
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            logger.debug(traceback.format_exc())
            db.session.rollback()
            flash('An error occurred while adding the transaction.', 'danger')
    else:
        logger.debug("Form validation failed for adding transaction.")
        # Log the form errors for debugging
        for field, errors in form.errors.items():
            for error in errors:
                logger.debug(f"Error in {getattr(form, field).label.text}: {error}")
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('view_transactions'))


@app.route('/edit_transaction/<int:transaction_id>', methods=['POST'])
def edit_transaction(transaction_id):
    logger.debug(f"Accessed edit_transaction route for transaction ID: {transaction_id}")
    transaction = Transaction.query.get_or_404(transaction_id)
    form = TransactionForm()
    if form.validate_on_submit():
        try:
            # Update transaction fields
            transaction.date = form.date.data
            transaction.category_id = form.category.data
            transaction.description = form.description.data
            transaction.amount = form.amount.data
            transaction.type = form.type.data
            transaction.recurring = form.recurring.data

            db.session.commit()
            logger.info(f"Updated transaction ID {transaction_id}: {transaction}")
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('view_transactions'))
        except Exception as e:
            logger.error(f"Error editing transaction ID {transaction_id}: {e}")
            logger.debug(traceback.format_exc())
            db.session.rollback()
            flash('An error occurred while editing the transaction.', 'danger')
    else:
        logger.debug(f"Form validation failed for editing transaction ID {transaction_id}.")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('view_transactions'))


@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    logger.debug(f"Accessed delete_transaction route for transaction ID: {transaction_id}")
    transaction = Transaction.query.get_or_404(transaction_id)
    try:
        db.session.delete(transaction)
        db.session.commit()
        logger.info(f"Deleted transaction ID {transaction_id}: {transaction}")
        flash('Transaction deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting transaction ID {transaction_id}: {e}")
        logger.debug(traceback.format_exc())
        db.session.rollback()
        flash('An error occurred while deleting the transaction.', 'danger')
    return redirect(url_for('view_transactions'))

# Budget Routes

@app.route('/budgets', methods=['GET'])
def view_budgets():
    logger.debug("Accessed view_budgets route.")
    try:
        # Get the 'month' from query parameters, default to current month
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        # Validate 'month' format
        try:
            datetime.strptime(month_str, '%Y-%m')
            month = month_str
        except ValueError:
            logger.warning(f"Invalid month format received: {month_str}")
            flash('Invalid month format. Please use YYYY-MM.', 'warning')
            month = datetime.now().strftime('%Y-%m')

        # Optimize queries to prevent N+1 problem
        budgets = Budget.query.filter_by(month=month).join(Category).all()
        budget_ids = [budget.id for budget in budgets]
        category_ids = [budget.category_id for budget in budgets]

        # Aggregate spent amounts per category
        spent_data = db.session.query(
            Transaction.category_id,
            db.func.sum(Transaction.amount).label('spent')
        ).filter(
            Transaction.category_id.in_(category_ids),
            extract('year', Transaction.date) == int(month.split('-')[0]),
            extract('month', Transaction.date) == int(month.split('-')[1])
        ).group_by(Transaction.category_id).all()

        spent_dict = {data.category_id: data.spent for data in spent_data}

        budget_data = []
        for budget in budgets:
            spent = spent_dict.get(budget.category_id, 0)
            remaining = budget.amount - spent
            percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
            budget_data.append({
                'id': budget.id,
                'category': budget.category.name,
                'budget': budget.amount,
                'spent': spent,
                'remaining': remaining,
                'percentage': percentage,
                'month': budget.month
            })
        logger.debug(f"Fetched {len(budget_data)} budgets for month {month}.")

        # Instantiate the BudgetForm to pass to the template
        form = BudgetForm()

        return render_template(
            'view_budgets.html',
            budgets=budget_data,
            month=month,
            form=form  # Pass the form to the template
        )
    except Exception as e:
        logger.error(f"Error in view_budgets route: {e}")
        logger.debug(traceback.format_exc())
        flash('An error occurred while fetching budgets.', 'danger')
        return render_template('500.html'), 500

@app.route('/add_budget', methods=['POST'])
def add_budget():
    logger.debug("Accessed add_budget route.")
    form = BudgetForm()
    if form.validate_on_submit():
        try:
            # Check if a budget for the category and month already exists
            existing_budget = Budget.query.filter_by(
                category_id=form.category.data,
                month=form.month.data
            ).first()
            if existing_budget:
                logger.warning(f"Attempted to add duplicate budget for category ID {form.category.data} and month {form.month.data}.")
                form.category.errors.append('A budget for this category and month already exists.')
                return redirect(url_for('view_budgets'))

            budget = Budget(
                category_id=form.category.data,
                amount=form.amount.data,
                month=form.month.data
            )
            db.session.add(budget)
            db.session.commit()
            logger.info(f"Added new budget: {budget}")
            flash('Budget added successfully!', 'success')
            return redirect(url_for('view_budgets'))
        except Exception as e:
            logger.error(f"Error adding budget: {e}")
            logger.debug(traceback.format_exc())
            db.session.rollback()
            flash('An error occurred while adding the budget.', 'danger')
    else:
        logger.debug("Form validation failed for adding budget.")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('view_budgets'))

@app.route('/edit_budget/<int:budget_id>', methods=['POST'])
def edit_budget(budget_id):
    logger.debug(f"Accessed edit_budget route for budget ID: {budget_id}")
    budget = Budget.query.get_or_404(budget_id)
    form = BudgetForm()
    if form.validate_on_submit():
        try:
            # Check for duplicate budget
            existing_budget = Budget.query.filter_by(
                category_id=form.category.data,
                month=form.month.data
            ).first()
            if existing_budget and existing_budget.id != budget.id:
                logger.warning(f"Attempted to edit budget ID {budget_id} to duplicate category ID {form.category.data} and month {form.month.data}.")
                form.category.errors.append('Another budget for this category and month already exists.')
                return redirect(url_for('view_budgets'))

            budget.category_id = form.category.data
            budget.amount = form.amount.data
            budget.month = form.month.data
            db.session.commit()
            logger.info(f"Updated budget ID {budget_id}: {budget}")
            flash('Budget updated successfully!', 'success')
            return redirect(url_for('view_budgets'))
        except Exception as e:
            logger.error(f"Error editing budget ID {budget_id}: {e}")
            logger.debug(traceback.format_exc())
            db.session.rollback()
            flash('An error occurred while editing the budget.', 'danger')
    else:
        logger.debug(f"Form validation failed for editing budget ID {budget_id}.")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('view_budgets'))

@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    logger.debug(f"Accessed delete_budget route for budget ID: {budget_id}")
    budget = Budget.query.get_or_404(budget_id)
    try:
        db.session.delete(budget)
        db.session.commit()
        logger.info(f"Deleted budget ID {budget_id}: {budget}")
        flash('Budget deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting budget ID {budget_id}: {e}")
        logger.debug(traceback.format_exc())
        db.session.rollback()
        flash('An error occurred while deleting the budget.', 'danger')
    return redirect(url_for('view_budgets'))

# Reports Routes

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    logger.debug("Accessed reports route.")
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        logger.debug(f"Report request: type={report_type}, start_date={start_date}, end_date={end_date}")
        if not report_type or not start_date or not end_date:
            logger.warning("Incomplete report request received.")
            flash('Please select report type and date range.', 'warning')
            return redirect(url_for('reports'))
        try:
            start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date()
            logger.debug(f"Parsed dates: start_date={start_date_parsed}, end_date={end_date_parsed}")
        except ValueError as ve:
            logger.warning(f"Invalid date format in report request: {ve}")
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('reports'))
        try:
            transactions = Transaction.query.filter(
                Transaction.date >= start_date_parsed,
                Transaction.date <= end_date_parsed
            ).all()
            logger.debug(f"Fetched {len(transactions)} transactions for the report.")

            # Generate summaries based on report_type
            # (Monthly, Quarterly, Yearly)
            # Placeholder for actual report generation logic
            # ...

            return render_template(
                'reports.html',
                transactions=transactions,
                report_type=report_type,
                start_date=start_date_parsed,
                end_date=end_date_parsed
            )
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            logger.debug(traceback.format_exc())
            flash('An error occurred while generating the report.', 'danger')
            return redirect(url_for('reports'))
    return render_template('reports.html')

@app.route('/category_trends')
def category_trends():
    logger.debug("Accessed category trends route.")
    try:
        # Analyze spending trends over time within each category
        categories = Category.query.filter_by(type='Expense').all()
        category_data = []

        for category in categories:
            logger.debug(f"Fetching transactions for category: {category.name}")
            transactions = Transaction.query.filter_by(
                category_id=category.id
            ).order_by(Transaction.date).all()
            
            dates = [t.date.strftime('%Y-%m-%d') for t in transactions]
            amounts = [t.amount for t in transactions]
            
            logger.info(
                f"Category: {category.name} - Transactions: {len(transactions)} - Total Amount: {sum(amounts)}"
            )

            category_data.append({
                'category': category.name,
                'dates': dates,
                'amounts': amounts
            })
        
        logger.info("Category trends data prepared successfully.")
        return render_template('category_trends.html', category_data=category_data)
    
    except Exception as e:
        logger.error(f"Error accessing category trends: {e}")
        logger.debug(traceback.format_exc())
        flash('An error occurred while loading category trends.', 'danger')
        return redirect(url_for('dashboard'))

# -------------------- Data Export Routes -------------------- #

@app.route('/export/<string:export_format>')
def export_data(export_format):
    logger.debug(f"Accessed data export route with format: {export_format}.")
    try:
        transactions = Transaction.query.all()
        if export_format.lower() == 'csv':
            logger.debug("Exporting data as CSV.")
            si = StringIO()
            cw = csv.writer(si)
            cw.writerow(['ID', 'Amount', 'Date', 'Description', 'Category'])
            for txn in transactions:
                cw.writerow([txn.id, txn.amount, txn.date.strftime('%Y-%m-%d'), txn.description, txn.category.name])
            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
            output.headers["Content-type"] = "text/csv"
            logger.info("CSV data exported successfully.")
            return output
        elif export_format.lower() == 'json':
            logger.debug("Exporting data as JSON.")
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
            logger.info("JSON data exported successfully.")
            return output
        else:
            logger.warning(f"Unsupported export format: {export_format}")
            flash('Unsupported export format!', 'danger')
            return redirect(url_for('dashboard'))
    
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        logger.debug(traceback.format_exc())
        flash('An error occurred while exporting data.', 'danger')
        return redirect(url_for('dashboard'))

# -------------------- Data Import Route -------------------- #

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    logger.debug("Accessed data import route.")
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename
        logger.info(f"Starting data import from file: {filename}")
        success_count = 0
        failure_count = 0
        failure_details = []
        
        try:
            if filename.endswith('.csv'):
                logger.debug("Importing CSV file.")
                stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.reader(stream)
                header = next(csv_input, None)
                
                for row in csv_input:
                    try:
                        amount = float(row[1])
                        date_str = row[2]
                        description = row[3]
                        category_name = row[4]
                        category = Category.query.filter_by(name=category_name).first()
                        if not category:
                            raise ValueError('Category not found')
                        transaction = Transaction(
                            amount=amount,
                            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                            description=description,
                            category_id=category.id
                        )
                        db.session.add(transaction)
                        success_count += 1
                    except Exception as row_error:
                        failure_count += 1
                        failure_details.append({'row': row, 'error': str(row_error)})
                        logger.error(f"Error processing row: {row} - {row_error}")
                
                db.session.commit()
                logger.info(f"CSV data import completed: {success_count} successes, {failure_count} failures.")
                flash(f'CSV data imported: {success_count} successes, {failure_count} failures.', 'success')
                return render_template('import_summary.html', success_count=success_count, failure_count=failure_count, failure_details=failure_details)
            
            elif filename.endswith('.json'):
                logger.debug("Importing JSON file.")
                try:
                    data = json.load(file.stream)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON file format.")
                    flash('Invalid JSON file.', 'danger')
                    return redirect(url_for('import_data'))
                
                for item in data:
                    try:
                        amount = float(item['amount'])
                        date_str = item['date']
                        description = item.get('description', '')
                        category_name = item['category']
                        category = Category.query.filter_by(name=category_name).first()
                        if not category:
                            raise ValueError('Category not found')
                        transaction = Transaction(
                            amount=amount,
                            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                            description=description,
                            category_id=category.id
                        )
                        db.session.add(transaction)
                        success_count += 1
                    except Exception as item_error:
                        failure_count += 1
                        failure_details.append({'item': item, 'error': str(item_error)})
                        logger.error(f"Error processing item: {item} - {item_error}")
                
                db.session.commit()
                logger.info(f"JSON data import completed: {success_count} successes, {failure_count} failures.")
                flash(f'JSON data imported: {success_count} successes, {failure_count} failures.', 'success')
                return render_template('import_summary.html', success_count=success_count, failure_count=failure_count, failure_details=failure_details)
            
            else:
                logger.warning(f"Unsupported file format: {filename}")
                flash('Unsupported file format!', 'danger')
                return redirect(url_for('import_data'))
        
        except Exception as e:
            logger.error(f"Error during data import: {e}")
            logger.debug(traceback.format_exc())
            flash('An error occurred during data import.', 'danger')
            return redirect(url_for('import_data'))
    
    return render_template('import_data.html', form=form)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


