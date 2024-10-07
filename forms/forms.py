# forms/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, SubmitField, SelectField, DateField, FileField, BooleanField
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from models.models import Category

class TransactionForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    description = StringField('Description', validators=[Length(max=200)])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    
    # Fields for recurring transactions
    is_recurring = BooleanField('Is Recurring')
    frequency = SelectField(
        'Frequency',
        choices=[('', 'Select Frequency'), ('Daily', 'Daily'), ('Weekly', 'Weekly'), ('Monthly', 'Monthly')],
        validators=[Optional()]
    )
    next_date = DateField('Next Date', format='%Y-%m-%d', validators=[Optional()])
    
    submit = SubmitField('Save Transaction')

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.order_by('name')]

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        if self.is_recurring.data:
            if not self.frequency.data or self.frequency.data not in ['Daily', 'Weekly', 'Monthly']:
                self.frequency.errors.append('Please select a valid frequency.')
                return False
            if not self.next_date.data:
                self.next_date.errors.append('Please provide the next date for the recurring transaction.')
                return False
        return True

class BudgetForm(FlaskForm):
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    amount = FloatField('Budget Amount', validators=[DataRequired(), NumberRange(min=0.0)])
    month = StringField('Month (YYYY-MM)', validators=[DataRequired(), Length(min=7, max=7)])  # Format: 'YYYY-MM'
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
