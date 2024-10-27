# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Example configuration; adjust according to your setup
    SQLALCHEMY_DATABASE_URI = 'sqlite:///finance.db'  # Ensure this path is correct
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'