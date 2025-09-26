from datetime import datetime
from App.database import db

class Staff(db.Model):
    __tablename__ = "staff"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)

    def __repr__(self):
        return f'<Staff {self.id}>'