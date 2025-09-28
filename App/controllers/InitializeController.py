from datetime import datetime
from App.database import db
from App.models import User, UserRoleEnum, Student, Staff, ServiceLog, ConfirmationRequest, RequestStatus, Accolade
from App.controllers import create_user

def initialize():
    db.drop_all()
    db.create_all()
    
    staff_members = create_sample_staff()
    students = create_sample_students()
    requests = create_sample_requests(students, staff_members)
    create_sample_service_logs(requests)
    update_student_hours(students)
    create_sample_accolades(students)
    print("database initialized!")

def create_sample_staff():
    staff_members = []
    staff_data = [
        {"username": "staff1", "password": "staffpass"},
        {"username": "staff2", "password": "staffpass"},
        {"username": "staff3", "password": "staffpass"}
    ]
    
    for s in staff_data:
        staff_user = User(username=s["username"], password=s["password"], role=UserRoleEnum.STAFF)
        db.session.add(staff_user)
        db.session.flush()
        staff_profile = Staff(user_id=staff_user.id)
        db.session.add(staff_profile)
        staff_members.append(staff_profile)
    
    db.session.commit()
    return staff_members

def create_sample_students():
    students = []
    for i in range(1, 8):
        student_user = User(username=f"student{i}", password="studentpass", role=UserRoleEnum.STUDENT)
        db.session.add(student_user)
        db.session.flush()
        student_profile = Student(user_id=student_user.id, total_hours=0.0)
        db.session.add(student_profile)
        students.append(student_profile)
    
    db.session.commit()
    return students

def create_sample_requests(students, staff_members):
    requests = [
        ConfirmationRequest(student_id=students[0].id, staff_id=staff_members[0].id, hours=5.0, description="Community Outreach", status=RequestStatus.APPROVED, responded_at=datetime.utcnow()),
        ConfirmationRequest(student_id=students[1].id, staff_id=staff_members[0].id, hours=3.0, description="Food Drive", status=RequestStatus.APPROVED, responded_at=datetime.utcnow()),
        ConfirmationRequest(student_id=students[1].id, staff_id=staff_members[1].id, hours=8.0, description="Football", status=RequestStatus.REJECTED, responded_at=datetime.utcnow()),
        ConfirmationRequest(student_id=students[2].id, staff_id=staff_members[1].id, hours=10.0, description="Library Book Sorting", status=RequestStatus.APPROVED, responded_at=datetime.utcnow()),
        ConfirmationRequest(student_id=students[3].id, staff_id=staff_members[2].id, hours=15.0, description="Park Cleanup", status=RequestStatus.PENDING),
        ConfirmationRequest(student_id=students[4].id, staff_id=staff_members[2].id, hours=7.0, description="Senior Center", status=RequestStatus.APPROVED, responded_at=datetime.utcnow()),
        ConfirmationRequest(student_id=students[5].id, staff_id=staff_members[0].id, hours=12.0, description="Animal Shelter", status=RequestStatus.APPROVED, responded_at=datetime.utcnow()),
        ConfirmationRequest(student_id=students[6].id, staff_id=staff_members[1].id, hours=2.0, description="Help Desk", status=RequestStatus.PENDING),
    ]
    
    db.session.add_all(requests)
    db.session.commit()
    return requests

def create_sample_service_logs(requests):
    for req in requests:
        if req.status == RequestStatus.APPROVED:
            service_log = ServiceLog(
                student_id=req.student_id,
                staff_id=req.staff_id,
                hours=req.hours,
                description=req.description
            )
            db.session.add(service_log)
    
    db.session.commit()

def update_student_hours(students):
    for student in students:
        approved_hours = db.session.query(db.func.sum(ServiceLog.hours)).filter(ServiceLog.student_id == student.id).scalar() or 0.0
        student.total_hours = approved_hours
        db.session.add(student)
    
    db.session.commit()

def create_sample_accolades(students):
    for student in students:
        if student.total_hours >= 10:
            db.session.add(Accolade(student_id=student.id, accolade_type="10"))
        if student.total_hours >= 25:
            db.session.add(Accolade(student_id=student.id, accolade_type="25"))
        if student.total_hours >= 50:
            db.session.add(Accolade(student_id=student.id, accolade_type="50"))
    
    db.session.commit()
