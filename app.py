# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'walkup.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Data model
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.Integer)
    track_uri = db.Column(db.String(200), nullable=False)
    start_ms = db.Column(db.Integer, default=0)
    duration_sec = db.Column(db.Integer, default=15)

# Create tables before first request
@app.before_first_request
def create_tables():
    db.create_all()

# Simple test route
@app.route('/')
def index():
    return "🎵 Walk-Up Music App Backend is running!"

if __name__ == '__main__':
    app.run(debug=True)

# requirements.txt
# Flask
# Flask-SQLAlchemy
# python-dotenv
