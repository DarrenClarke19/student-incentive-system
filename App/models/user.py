from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db
from enum import Enum

class UserRoleEnum(str, Enum):
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username =  db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRoleEnum), nullable=False)

    student = db.relationship('Student', backref='user', uselist=False)
    staff = db.relationship('Staff', backref='user', uselist=False)

    def __init__(self, username, password, role):
        self.username = username
        self.set_password(password)
        self.role = role

    def get_json(self):
        return{
            'id': self.id,
            'username': self.username,
            'role': self.role.value
        }

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

