from App.models import User, UserRoleEnum, Student, Staff
from App.database import db

def create_user(username, password, role):
    existing = User.query.filter_by(username=username).first()
    if existing:
        return {"success": False, "message": f"User {username} already exists"}
    
    user = User(
        username=username,
        password=password,
        role=UserRoleEnum(role)
    )
    db.session.add(user)
    
    if role == 'student':
        db.session.flush()
        student = Student(
            user_id=user.id
        )
        db.session.add(student)
    elif role == 'staff':
        db.session.flush()
        staff = Staff(
            user_id=user.id
        )
        db.session.add(staff)
    
    db.session.commit()
    return {"success": True, "message": f'User {username} created with role {role}!', "user": user}

def validate_user_creation(username, password, role):
    if not username or not password:
        return {"success": False, "message": "Username and password are required"}
    
    if role not in ['student', 'staff', 'admin']:
        return {"success": False, "message": "Role must be student, staff, or admin"}
    
    return {"success": True, "message": "Valid parameters"}

def list_users_formatted():
    users = User.query.all()
    
    if not users:
        return {"success": True, "message": "No users found", "users": []}
    
    formatted_users = []
    for user in users:
        profile_info = ""
        if user.student:
            profile_info = f"Student ID: {user.student.id} | Hours: {user.student.total_hours}"
        elif user.staff:
            profile_info = f"Staff ID: {user.staff.id}"
        else:
            profile_info = "No profile"
        
        formatted_users.append({
            "username": user.username,
            "role": user.role.value.title(),
            "profile_info": profile_info
        })
    
    return {
        "success": True,
        "message": "ALL USERS",
        "users": formatted_users
    }

def get_user_by_username(username):
    result = db.session.execute(db.select(User).filter_by(username=username))
    return result.scalar_one_or_none()

def get_user(id):
    return db.session.get(User, id)

def get_all_users():
    return db.session.scalars(db.select(User)).all()

def get_all_users_json():
    users = get_all_users()
    if not users:
        return []
    users = [user.get_json() for user in users]
    return users

def update_user(id, username):
    user = get_user(id)
    if user:
        user.username = username
        db.session.commit()
        return True
    return None
