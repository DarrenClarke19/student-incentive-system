from datetime import datetime
from App.database import db
from App.models import Student, Accolade

def check_and_award_accolades(student):
    thresholds = [10, 25, 50]
    
    for threshold in thresholds:
        existing_accolade = Accolade.query.filter_by(
            student_id=student.id,
            accolade_type=str(threshold)
        ).first()
        
        if student.total_hours >= threshold and not existing_accolade:
            accolade = Accolade(
                student_id=student.id,
                accolade_type=str(threshold)
            )
            db.session.add(accolade)
    
    db.session.commit()

def get_student_accolades(student_username):
    from App.models import User
    
    student_user = User.query.filter_by(username=student_username).first()
    if not student_user or not student_user.student:
        return {"success": False, "message": f"Student {student_username} not found", "accolades": []}
    
    accolades = Accolade.query.filter_by(student_id=student_user.student.id).all()
    
    if not accolades:
        return {
            "success": True,
            "message": f"Accolades for {student_username}:\nNo accolades yet",
            "accolades": []
        }
    
    formatted_accolades = []
    for accolade in accolades:
        formatted_accolades.append({
            "type": accolade.accolade_type,
            "awarded_at": accolade.awarded_at.strftime('%Y-%m-%d')
        })
    
    return {
        "success": True,
        "message": f"Accolades for {student_username}:",
        "accolades": formatted_accolades
    }

def get_leaderboard(limit=10):
    students = Student.query.order_by(Student.total_hours.desc()).limit(limit).all()
    
    if not students:
        return {"success": False, "message": "No students found", "leaderboard": []}
    
    formatted_leaderboard = []
    for i, student in enumerate(students, 1):
        accolades = Accolade.query.filter_by(student_id=student.id).all()
        accolade_badges = " ".join([f"{acc.accolade_type}h" for acc in accolades])
        
        formatted_leaderboard.append({
            "rank": i,
            "username": student.user.username,
            "total_hours": student.total_hours,
            "accolades": accolade_badges if accolade_badges else "No accolades"
        })
    
    return {
        "success": True,
        "message": f"TOP {limit} STUDENTS LEADERBOARD",
        "leaderboard": formatted_leaderboard
    }

def format_accolade_badges(student_id):
    accolades = Accolade.query.filter_by(student_id=student_id).all()
    return " ".join([f"{acc.accolade_type}h" for acc in accolades]) if accolades else "No accolades"