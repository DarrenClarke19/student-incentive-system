import click, pytest, sys
from flask.cli import with_appcontext, AppGroup
from tabulate import tabulate
from App.database import db, get_migrate
from App.main import create_app
from App.models import User
from App.controllers import (
    # Service functions
    submit_hours, get_student_requests, get_pending_requests_for_student, 
    approve_request, reject_request, get_student_service_logs, get_pending_students,
    interactive_request_review,
    # Accolade functions
    check_and_award_accolades, get_student_accolades, get_leaderboard,
    # Session functions
    login, logout, get_current_user_info, require_login,
    # User functions
    create_user, list_users_formatted,
    # Initialize functions
    initialize
)

# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()

'''
Authentication Commands
'''
auth_cli = AppGroup('auth', help='Authentication commands')

# This command logs in a user and saves current user to a session file for RBAC
@auth_cli.command("login", help="Login as a user")
@click.argument("username")
@click.option("--password", prompt=True, hide_input=True)
def login_command(username, password):
    result = login(username, password)
    print(result["message"])

@auth_cli.command("logout", help="Logout current user")
def logout_command():
    result = logout()
    print(result["message"])

@auth_cli.command("current-user", help="Show current user")
def current_user_command():
    result = get_current_user_info()
    print(result["message"])

app.cli.add_command(auth_cli)

'''
User Commands
'''
user_cli = AppGroup('user', help='User object commands') 

# This command creates a user with a specific role
@user_cli.command("create", help="Creates a user")
@click.argument("username")
@click.argument("password")
@click.argument("role", type=click.Choice(['student', 'staff']))
def create_user_command(username, password, role):
    result = create_user(username, password, role)
    print(result["message"])

@user_cli.command("list", help="Lists users in the database")
def list_user_command():
    result = list_users_formatted()
    print("\n" + "="*80)
    print(result["message"])
    print("="*80)
    
    if result["users"]:
        table_data = []
        for user in result["users"]:
            table_data.append([user["username"], user["role"], user["profile_info"]])
        
        headers = ["Username", "Role", "Profile Info"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        print("No users found")

app.cli.add_command(user_cli)

'''
Service Commands - Core Assignment Requirements
'''
service_cli = AppGroup('service', help='Service logging and confirmation commands')

#This command allows a student to submit hours for approval by a staff member
@service_cli.command("submit-hours", help="Submit hours for approval (students only)")
@click.argument("hours", type=float)
@click.option("--description", default="", help="Description of the service performed")
def submit_hours_command(hours, description):
    login_result = require_login()
    if not login_result["success"]:
        print(login_result["message"])
        return

    result = submit_hours(hours, description, login_result["user"])
    print(result["message"])

# This command allows a student to view their submitted hour requests
@service_cli.command("my-requests", help="View your submitted hour requests (students only)")
def my_requests_command():
    login_result = require_login()
    if not login_result["success"]:
        print(login_result["message"])
        return
    
    result = get_student_requests(login_result["user"])
    print(result["message"])
    
    if result["requests"]:
        print("-" * 60)
        for req in result["requests"]:
            print(f"ID: {req['id']} | {req['hours']}h | {req['status']} | {req['description']}")
            print(f"    Submitted: {req['submitted_at']}")
    else:
        print(result["message"])

# This command allows a staff member to review and approve/reject pending requests for a specific student
@service_cli.command("review-hours", help="Interactive review of pending requests for a specific student (staff only)")
@click.argument("student_username")
def review_requests_command(student_username):
    login_result = require_login()
    if not login_result["success"]:
        print(login_result["message"])
        return
    
    if login_result["user"]["role"] != "staff":
        print("Only staff can review requests")
        return
    
    staff_user = User.query.filter_by(username=login_result["user"]["username"]).first()
    
    interactive_request_review(student_username, staff_user)

# This command shows the leaderboard of students with the most service hours
@service_cli.command("leaderboard", help="View student leaderboard")
@click.option("--limit", default=10, help="Number of students to show")
def leaderboard_command(limit):
    result = get_leaderboard(limit)
    if not result["success"]:
        print(result["message"])
        return
    
    print("\n" + "="*80)
    print(result["message"])
    print("="*80)
    
    table_data = []
    for student in result["leaderboard"]:
        table_data.append([
            f"#{student['rank']}",
            student["username"],
            f"{student['total_hours']}h",
            student["accolades"]
        ])
    
    headers = ["Rank", "Student", "Total Hours", "Accolades"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

# This command shows the accolades earned by a specific student
@service_cli.command("accolades", help="View accolades for a student")
@click.argument("student_username")
def accolades_command(student_username):
    result = get_student_accolades(student_username)
    print(f"\n{result['message']}")
    print("-" * 30)
    
    if result["accolades"]:
        for accolade in result["accolades"]:
            print(f"• {accolade['type']} hours - Awarded {accolade['awarded_at']}")
    else:
        print("No accolades yet")

# This command allows a student to view their confirmed service logs
@service_cli.command("my-logs", help="View your confirmed service logs (students only)")
def my_logs_command():
    login_result = require_login()
    if not login_result["success"]:
        print(login_result["message"])
        return
    
    result = get_student_service_logs(login_result["user"])
    print(result["message"])
    
    if result["logs"]:
        print("-" * 60)
        for log in result["logs"]:
            print(f"ID: {log['id']} | {log['hours']}h | Approved by: {log['approved_by']} | {log['description']}")
            print(f"    Logged: {log['logged_at']}")
    else:
        print("No confirmed service logs found. Submit hours for approval first!")
    
    print(f"\nTotal Confirmed Hours: {result['total_hours']}")

# This command allows a staff member to view all students with pending hour requests
@service_cli.command("pending-students", help="List students with pending hour requests (staff only)")
def pending_students_command():
    login_result = require_login()
    if not login_result["success"]:
        print(login_result["message"])
        return
    
    if login_result["user"]["role"] != "staff":
        print("Only staff can view pending students")
        return
    
    result = get_pending_students()
    print(f"\n{result['message']}")
    
    if result["students"]:
        print("-" * 70)
        for student in result["students"]:
            print(f"{student['username']}")
            print(f"   Current hours: {student['current_hours']}")
            print(f"   Pending requests: {student['pending_requests']} ({student['total_pending_hours']} hours total)")
            print(f"   Review command: flask service review-hours {student['username']}")
            print()
    else:
        print("No pending requests from any students.")
    
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