PennyPilot - Personal Finance Management App

PennyPilot is a personal finance management web application that helps users manage their transactions, budgets, and recurring expenses efficiently. This app is built using Python's Flask framework and uses SQLAlchemy for database management.

Table of Contents
Features
Installation
Usage
Project Structure
Screenshots
Contributing
License
Contact


Features

Transaction Management: Add, edit, and delete transactions for various categories (e.g., Food, Rent, Utilities).
Recurring Transactions: Manage recurring transactions with support for daily, weekly, and monthly frequencies.
Budget Tracking: Create and track budgets for different expense categories.
Data Import/Export: Import and export data in CSV and JSON formats.
Dashboard Overview: View total income, expenses, and balance at a glance.
Visualizations and Reports: Display expenses by category and recurring transactions on a calendar.


Installation

Prerequisites
Ensure you have the following installed:

Python 3.7 or higher
Flask 2.0 or higher
Flask-WTF and WTForms
Flask-SQLAlchemy
APScheduler
SQLite (for local database)


Steps
Clone the Repository:

git clone https://github.com/yourusername/pennypilot.git
cd pennypilot


Create and Activate a Virtual Environment:

python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate


Install Dependencies:

bash
Copy code
pip install -r requirements.txt


Set Up the Database:

Initialize the SQLite database and create necessary tables:

python -c "from app import db; db.create_all()"


Run the Application:

python app.py
Access the Application:

Open your browser and navigate to http://127.0.0.1:5000 to access PennyPilot.


Usage

Adding Transactions
Navigate to the Add Transaction page.
Fill in the required fields (amount, date, description, category).
Check the Is Recurring box if the transaction is recurring.
Click Save Transaction.
Managing Budgets
Navigate to the Budgets page.
Add or edit budgets for different categories and track your spending.
Importing/Exporting Data
Use the Import/Export page to upload CSV or JSON files for transactions.
Export your current transactions to a file for external use.


Project Structure

pennypilot/
├── app.py                      # Main application file
├── config.py                   # Configuration settings for Flask and SQLAlchemy
├── requirements.txt            # Project dependencies
├── models/
│   └── models.py               # Database models for the app
├── forms/
│   └── forms.py                # Flask-WTF form classes for handling user input
├── templates/
│   ├── base.html               # Base HTML template
│   ├── add_transaction.html    # Template for adding transactions
│   ├── edit_transaction.html   # Template for editing transactions
│   ├── dashboard.html          # Main dashboard template
│   ├── view_budgets.html       # Template for viewing budgets
│   └── import_data.html        # Template for importing/exporting data
├── static/
│   ├── css/
│   │   └── styles.css          # Custom CSS styles
│   └── js/
│       └── scripts.js          # Custom JavaScript functions
└── utils/
    └── helpers.py              # Helper functions for background tasks and utilities


Contributing
Contributions are welcome! Please submit a pull request or open an issue to discuss your ideas. Make sure to follow the coding style and provide sufficient test coverage.
