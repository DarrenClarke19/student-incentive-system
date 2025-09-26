import click, pytest, sys
from flask.cli import with_appcontext, AppGroup
from datetime import datetime
from functools import wraps
from tabulate import tabulate
from App.database import db, get_migrate
from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users, initialize )
from App.models import User, UserRoleEnum, Student, Staff, ServiceLog, ConfirmationRequest, RequestStatus, Accolade

import json
import os


# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    db.drop_all()
    db.create_all()   
        
    staff_users = [
        {"username": "staff1", "password": "staffpass", "role": UserRoleEnum.STAFF},
        {"username": "staff2", "password": "staffpass", "role": UserRoleEnum.STAFF},
    ] 
    for staff in staff_users:
        existing = User.query.filter_by(username=staff["username"]).first()
        if not existing:
            staff = User(
                username=staff["username"],
                password=staff["password"],
                role=staff["role"]
            )
            db.session.add(staff)
            db.session.flush()
                
            staff_profile = Staff(
                user_id=staff.id,
                staff_id=f"S{staff.id:03d}"
            )
            db.session.add(staff_profile)
        
    for i in range(1, 6):
        student_data = {
            "username": f"student{i}",
            "password": "studentpass",
            "role": UserRoleEnum.STUDENT
        }
            
        existing = User.query.filter_by(username=student_data["username"]).first()
        if not existing:
            student = User(
                username=student_data["username"],
                password=student_data["password"],
                role=student_data["role"]
            )
            db.session.add(student)
            db.session.flush()
                
            profile = Student(
                user_id=student.id,
                student_id=f"S{i:03d}",
                total_hours=i * 2.0
            )
            db.session.add(profile)
        
    db.session.commit()
    print("database initialized!")

'''
Authentication Commands
'''
auth_cli = AppGroup('auth', help='Authentication commands')

# Session management using a file

SESSION_FILE = ".current_user.json"

def set_current_user(user):
    session_data = {
        "username": user.username,
        "role": user.role.value,
        "user_id": user.id,
        "login_time": datetime.utcnow().isoformat()
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)

def get_current_user():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def clear_current_user():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# This command logs in a user and saves current user to a session file for RBAC
@auth_cli.command("login", help="Login as a user")
@click.argument("username")
@click.option("--password", prompt=True, hide_input=True)
def login_command(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        set_current_user(user)
        print(f"Logged in as {username} ({user.role.value})")
    else:
        print("Invalid username or password")

@auth_cli.command("logout", help="Logout current user")
def logout_command():
    clear_current_user()
    print("Logged out")

@auth_cli.command("current-user", help="Show current user")
def current_user_command():
    user = get_current_user()
    if user:
        print(f"Logged in as: {user['username']} ({user['role']})")
    else:
        print("Not logged in")

app.cli.add_command(auth_cli)

'''
User Commands
'''
user_cli = AppGroup('user', help='User object commands') 

# This command creates a user with a specific role
@user_cli.command("create", help="Creates a user")
@click.argument("username")
@click.argument("password")
@click.argument("role", type=click.Choice(['student', 'staff', 'admin']))
def create_user_command(username, password, role):
    existing = User.query.filter_by(username=username).first()
    if existing:
        print(f"User {username} already exists")
        return
    
    user = User(
        username=username,
        password=password,
        role=UserRoleEnum(role)
    )
    db.session.add(user)
    
    if role == 'student':
        db.session.flush()
        student = Student(
            user_id=user.id,
            student_id=f"S{user.id:03d}"
        )
        db.session.add(student)
    elif role == 'staff':
        db.session.flush()
        staff = Staff(
            user_id=user.id,
            staff_id=f"ST{user.id:03d}",
            department="General"
        )
        db.session.add(staff)
    
    db.session.commit()
    print(f'User {username} created with role {role}!')

@user_cli.command("list", help="Lists users in the database")
def list_user_command():
    users = User.query.all()
    
    # Prepare table data
    table_data = []
    for user in users:
        profile_info = ""
        if user.student:
            profile_info = f"Student ID: {user.student.student_id} | Hours: {user.student.total_hours}"
        elif user.staff:
            profile_info = f"Staff ID: {user.staff.staff_id}"
        else:
            profile_info = "No profile"
        
        table_data.append([
            user.username,
            user.role.value.title(),
            profile_info
        ])
    
    headers = ["Username", "Role", "Profile Info"]
    print("\n" + "="*80)
    print("ALL USERS")
    print("="*80)
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

app.cli.add_command(user_cli)

'''
Service Commands - Core Assignment Requirements
'''
service_cli = AppGroup('service', help='Service logging and confirmation commands')

def require_login():
    user = get_current_user()
    if not user:
        print("You must login first. Use: flask auth login <username>")
        return None
    return user

def require_role(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = require_login()
            if not user:
                return
            if user["role"] not in allowed_roles:
                print(f"Insufficient permissions. Required role: {', '.join(allowed_roles)}")
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator

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

@service_cli.command("submit-hours", help="Submit hours for approval (students only)")
@click.argument("hours", type=float)
@click.option("--description", default="", help="Description of the service performed")
def submit_hours_command(hours, description):
    user = require_login()
    if not user or user["role"] != "student":
        print("Only students can submit hours")
        return
    
    if hours <= 0:
        print("Hours must be greater than 0")
        return
    if hours > 24:
        print("Hours cannot exceed 24 per session")
        return
    
    # Find student
    student_user = User.query.filter_by(username=user["username"]).first()
    if not student_user or not student_user.student:
        print("Student profile not found")
        return
    
    # Create confirmation request (student submits hours for approval)
    confirmation_request = ConfirmationRequest(
        student_id=student_user.student.id,
        hours=hours,
        description=description,
        status=RequestStatus.PENDING
    )
    
    db.session.add(confirmation_request)
    db.session.commit()
    
    print(f"Submitted {hours} hours for approval (Request ID: {confirmation_request.id})")
    print("Staff will review and approve your request.")

@service_cli.command("my-requests", help="View your submitted hour requests (students only)")
def my_requests_command():
    user = require_login()
    if not user or user["role"] != "student":
        print("Only students can view their requests")
        return
    
    # Find student
    student_user = User.query.filter_by(username=user["username"]).first()
    if not student_user or not student_user.student:
        print("Student profile not found")
        return
    
    requests = ConfirmationRequest.query.filter_by(student_id=student_user.student.id).order_by(ConfirmationRequest.requested_at.desc()).all()
    
    print(f"\nYour Hour Requests:")
    print("-" * 60)
    for req in requests:
        print(f"ID: {req.id} | {req.hours}h | {req.status.value.title()} | {req.description}")
        if req.requested_at:
            print(f"    Submitted: {req.requested_at.strftime('%Y-%m-%d %H:%M')}")
    if not requests:
        print("No requests submitted yet. Use 'flask service submit-hours <hours>' to submit your first request.")

@service_cli.command("review-hours", help="Interactive review of pending requests for a specific student (staff only)")
@click.argument("student_username")
def review_requests_command(student_username):
    user = require_login()
    if not user or user["role"] != "staff":
        print("Only staff can review requests")
        return
    
    # Find staff user
    staff_user = User.query.filter_by(username=user["username"]).first()
    
    # Find student
    student_user = User.query.filter_by(username=student_username).first()
    if not student_user or not student_user.student:
        print(f"Student '{student_username}' not found")
        return
    
    while True:
        # Get pending requests for this specific student
        requests = ConfirmationRequest.query.filter_by(
            student_id=student_user.student.id,
            status=RequestStatus.PENDING
        ).all()
        
        if not requests:
            print(f"\nNo pending requests for {student_username}.")
            break
        
        # Display student info and requests
        print(f"\nReviewing requests for: {student_username}")
        print(f"Current total hours: {student_user.student.total_hours}")
        print(f"Pending requests ({len(requests)} total):")
        print("-" * 80)
        for i, req in enumerate(requests, 1):
            print(f"[{i}] Hours: {req.hours} | {req.description}")
            print(f"     Submitted: {req.requested_at.strftime('%Y-%m-%d %H:%M')}")
            print()
        
        # Get user selection
        try:
            choice = input(f"Select request (1-{len(requests)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("Exiting review mode.")
                break
            
            choice_num = int(choice)
            if choice_num < 1 or choice_num > len(requests):
                print("Invalid selection. Please try again.")
                continue
            
            # Get the selected request
            selected_request = requests[choice_num - 1]
            student = User.query.get(selected_request.student.user_id)
            
            # Show request details
            print(f"\nReviewing Request #{selected_request.id}:")
            print(f"Student: {student.username}")
            print(f"Hours: {selected_request.hours}")
            print(f"Description: {selected_request.description}")
            print(f"Submitted: {selected_request.requested_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Get decision
            decision = input("\nApprove this request? (y/n/r for reason): ").strip().lower()
            
            if decision == 'y':
                # Approve request
                selected_request.staff_id = staff_user.id
                selected_request.status = RequestStatus.APPROVED
                selected_request.responded_at = datetime.utcnow()
                
                # Create confirmed ServiceLog
                service_log = ServiceLog(
                    student_id=selected_request.student_id,
                    staff_id=staff_user.id,
                    hours=selected_request.hours,
                    description=selected_request.description,
                    confirmed=True
                )
                db.session.add(service_log)
                
                # Update student total hours
                student_profile = Student.query.get(selected_request.student_id)
                student_profile.total_hours += selected_request.hours
                
                # Check for accolades
                check_and_award_accolades(student_profile)
                
                db.session.commit()
                
                print(f"Approved! {student.username} now has {student_profile.total_hours} total hours.")
                
            elif decision == 'n':
                # Reject request
                selected_request.staff_id = staff_user.id
                selected_request.status = RequestStatus.REJECTED
                selected_request.responded_at = datetime.utcnow()
                
                db.session.commit()
                
                print(f"Rejected request from {student.username}")
                
            elif decision == 'r':
                # Reject with reason
                reason = input("Enter rejection reason: ").strip()
                
                selected_request.staff_id = staff_user.id
                selected_request.status = RequestStatus.REJECTED
                selected_request.responded_at = datetime.utcnow()
                
                db.session.commit()
                
                print(f"Rejected request from {student.username}")
                print(f"Reason: {reason}")
                
            else:
                print("Invalid choice. Skipping this request.")
                continue
            
            # Ask if user wants to continue
            continue_review = input("\nContinue reviewing? (y/n): ").strip().lower()
            if continue_review != 'y':
                break
                
        except ValueError:
            print("Invalid input. Please enter a number or 'q'.")
            continue
        except KeyboardInterrupt:
            print("\nExiting review mode.")
            break

@service_cli.command("leaderboard", help="View student leaderboard")
@click.option("--limit", default=10, help="Number of students to show")
def leaderboard_command(limit):
    students = Student.query.order_by(Student.total_hours.desc()).limit(limit).all()
    
    if not students:
        print("No students found")
        return
    
    # Prepare table data
    table_data = []
    for i, student in enumerate(students, 1):
        # Get accolades for this student
        accolades = Accolade.query.filter_by(student_id=student.id).all()
        accolade_badges = " ".join([f"{acc.accolade_type}h" for acc in accolades])
        
        table_data.append([
            f"#{i}",
            student.user.username,
            f"{student.total_hours}h",
            accolade_badges if accolade_badges else "No accolades"
        ])
    
    headers = ["Rank", "Student", "Total Hours", "Accolades"]
    print("\n" + "="*80)
    print(f"TOP {limit} STUDENTS LEADERBOARD")
    print("="*80)
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

@service_cli.command("accolades", help="View accolades for a student")
@click.argument("student_username")
def accolades_command(student_username):
    student_user = User.query.filter_by(username=student_username).first()
    if not student_user or not student_user.student:
        print(f"Student {student_username} not found")
        return
    
    accolades = Accolade.query.filter_by(student_id=student_user.student.id).all()
    
    print(f"\n Accolades for {student_username}:")
    print("-" * 30)
    if accolades:
        for accolade in accolades:
            print(f"• {accolade.accolade_type} hours - Awarded {accolade.awarded_at.strftime('%Y-%m-%d')}")
    else:
        print("No accolades yet")

@service_cli.command("my-logs", help="View your confirmed service logs (students only)")
def my_logs_command():
    user = require_login()
    if not user or user["role"] != "student":
        print("Only students can view their service logs")
        return
    
    student_user = User.query.filter_by(username=user["username"]).first()
    if not student_user or not student_user.student:
        print("Student profile not found")
        return
    
    service_logs = ServiceLog.query.filter_by(student_id=student_user.student.id, confirmed=True).order_by(ServiceLog.logged_at.desc()).all()
    
    print(f"\nConfirmed Service Logs for {user['username']}:")
    print("-" * 60)
    for log in service_logs:
        staff_user = User.query.get(log.staff_id)
        print(f"ID: {log.id} | {log.hours}h | Approved by: {staff_user.username} | {log.description}")
        print(f"    Logged: {log.logged_at.strftime('%Y-%m-%d %H:%M')}")
    
    if not service_logs:
        print("No confirmed service logs found. Submit hours for approval first!")
    
    # Also show current total hours
    print(f"\nTotal Confirmed Hours: {student_user.student.total_hours}")

@service_cli.command("pending-students", help="List students with pending hour requests (staff only)")
def pending_students_command():
    user = require_login()
    if not user or user["role"] != "staff":
        print("Only staff can view pending students")
        return
    
    # Get all pending requests grouped by student
    pending_requests = ConfirmationRequest.query.filter_by(status=RequestStatus.PENDING).all()
    
    if not pending_requests:
        print("\nNo pending requests from any students.")
        return
    
    # Group by student
    students_with_requests = {}
    for req in pending_requests:
        student_id = req.student_id
        if student_id not in students_with_requests:
            students_with_requests[student_id] = []
        students_with_requests[student_id].append(req)
    
    print(f"\nStudents with Pending Requests ({len(students_with_requests)} students):")
    print("-" * 70)
    
    for student_id, requests in students_with_requests.items():
        student = Student.query.get(student_id)
        student_user = User.query.get(student.user_id)
        
        total_pending_hours = sum(req.hours for req in requests)
        print(f"{student_user.username}")
        print(f"   Current hours: {student.total_hours}")
        print(f"   Pending requests: {len(requests)} ({total_pending_hours} hours total)")
        print(f"   Review command: flask service review-hours {student_user.username}")
        print()
    
    print("Use 'flask service review-hours <username>' to review a specific student's requests.")


app.cli.add_command(service_cli)

'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    

app.cli.add_command(test)