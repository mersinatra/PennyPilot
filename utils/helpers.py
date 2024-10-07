# utils/helpers.py
from models.models import db, RecurringTransaction, Transaction
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def process_recurring_transactions():
    today = datetime.utcnow().date()
    recurring_transactions = RecurringTransaction.query.filter(RecurringTransaction.next_date <= today).all()
    for rt in recurring_transactions:
        # Create a new transaction based on the recurring transaction
        new_txn = Transaction(
            amount=rt.amount,
            date=rt.next_date,
            description=rt.description,
            category_id=rt.category_id
        )
        db.session.add(new_txn)

        # Update the next_date based on frequency
        if rt.frequency == 'Daily':
            rt.next_date += timedelta(days=1)
        elif rt.frequency == 'Weekly':
            rt.next_date += timedelta(weeks=1)
        elif rt.frequency == 'Monthly':
            try:
                rt.next_date += relativedelta(months=1)
            except ValueError:
                # Handle cases like February 30th by setting to the last day of the next month
                rt.next_date = rt.next_date + relativedelta(months=1, day=31)
        else:
            # If frequency is unrecognized, skip updating
            continue

    db.session.commit()
