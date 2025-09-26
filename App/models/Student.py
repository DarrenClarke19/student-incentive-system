from datetime import datetime
from App.database import db

class Student(db.Model):
    __tablename__ = "students"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    total_hours = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<Student {self.id}>'