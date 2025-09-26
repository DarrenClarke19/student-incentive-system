from datetime import datetime
from App.database import db

class Accolade(db.Model):
    __tablename__ = "accolades"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    accolade_type = db.Column(db.String(10), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="accolades", lazy="select")

    def __repr__(self):
        return f'<Accolade {self.accolade_type}h for student {self.student_id}>'



