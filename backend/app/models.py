from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    image_path = db.Column(db.String(200), nullable=True)

class EntryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_captured = db.Column(db.String(200), nullable=True)