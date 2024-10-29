# forms/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, SubmitField, SelectField, DateField,
    FileField, BooleanField, DecimalField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, ValidationError
)
from models.models import Category
from datetime import datetime
from werkzeug.utils import secure_filename

class TransactionForm(FlaskForm):
    amount = FloatField(
        'Amount', 
        validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than zero.")]
    )
    date = DateField(
        'Date', 
        format='%Y-%m-%d', 
        validators=[DataRequired()]
    )
    description = StringField(
        'Description', 
        validators=[Length(max=200, message="Description cannot exceed 200 characters.")]
    )
    category = SelectField(
        'Category', 
        coerce=int, 
        validators=[DataRequired()]
    )
    recurring = BooleanField('Recurring')
    type = SelectField(
        'Type', 
        choices=[('Income', 'Income'), ('Expense', 'Expense')], 
        validators=[DataRequired()]
    )
    frequency = SelectField(
        'Frequency', 
        choices=[
            ('', 'Select Frequency'),
            ('Daily', 'Daily'),
            ('Weekly', 'Weekly'),
            ('Monthly', 'Monthly')
        ], 
        validators=[Optional()]
    )
    next_date = DateField(
        'Next Date', 
        format='%Y-%m-%d', 
        validators=[Optional()]
    )
    submit = SubmitField('Save Transaction')

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        # Populate category choices dynamically from the database
        self.category.choices = [
            (c.id, c.name) for c in Category.query.order_by('name')
        ]

    def validate_next_date(self, field):
        if self.recurring.data and field.data:
            if field.data <= self.date.data:
                raise ValidationError("Next date must be after the transaction date.")

    def validate(self, *args, **kwargs):
        # Perform the default validation
        rv = super(TransactionForm, self).validate(*args, **kwargs)
        if not rv:
            return False

        # Additional validation for recurring transactions
        if self.recurring.data:
            if not self.frequency.data or self.frequency.data not in ['Daily', 'Weekly', 'Monthly']:
                self.frequency.errors.append('Please select a valid frequency.')
                return False
            if not self.next_date.data:
                self.next_date.errors.append('Please provide the next date for the recurring transaction.')
                return False
        return True

class BudgetForm(FlaskForm):
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    amount = FloatField(
        'Budget Amount',
        validators=[DataRequired(), NumberRange(min=0.0, message="Amount must be non-negative.")]
    )
    month = StringField(
        'Month (YYYY-MM)',
        validators=[DataRequired(), Length(min=7, max=7, message="Enter month in format YYYY-MM.")]
    )
    submit = SubmitField('Save Budget')

    def __init__(self, *args, **kwargs):
        super(BudgetForm, self).__init__(*args, **kwargs)
        # Only allow categories of type 'Expense'
        self.category.choices = [
            (c.id, c.name) for c in Category.query.filter_by(type='Expense').order_by('name')
        ]

class ImportForm(FlaskForm):
    file = FileField('Import Data File (CSV or JSON)', validators=[DataRequired()])
    submit = SubmitField('Import')

    def validate_file(self, field):
        if field.data:
            filename = secure_filename(field.data.filename)
            if not (filename.endswith('.csv') or filename.endswith('.json')):
                raise ValidationError('Unsupported file format! Please upload a CSV or JSON file.')
            

class SavingsForm(FlaskForm):
    account_name = StringField(
        'Account Name',
        validators=[DataRequired(), Length(max=100, message="Account name cannot exceed 100 characters.")]
    )
    balance = DecimalField(
        'Initial Balance',
        validators=[DataRequired(), NumberRange(min=0.0, message="Balance must be non-negative.")]
    )
    submit = SubmitField('Add Savings Account')

