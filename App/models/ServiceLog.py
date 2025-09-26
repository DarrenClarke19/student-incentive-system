from App.database import db
from datetime import datetime

class ServiceLog(db.Model):
    __tablename__ = "service_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship("Student", backref=db.backref("service_logs", lazy="select"))
    staff = db.relationship("User", backref=db.backref("logged_service", lazy="select"))
    
    def __repr__(self):
        return f"<ServiceLog {self.id}: {self.hours}h for student {self.student_id}>"

