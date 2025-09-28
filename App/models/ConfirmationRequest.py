from datetime import datetime
from enum import Enum
from App.database import db

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ConfirmationRequest(db.Model):
    __tablename__ = "confirmation_requests"
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id"), nullable=True)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(RequestStatus), default=RequestStatus.PENDING)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)

    student = db.relationship("Student", backref="confirmation_requests")
    staff = db.relationship("Staff", backref="handled_requests")
    reason = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<ConfirmationRequest {self.id}: {self.hours}h - {self.status}>'
