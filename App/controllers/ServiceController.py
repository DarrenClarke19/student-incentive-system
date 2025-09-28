from datetime import datetime
from App.database import db
from App.models import User, Student, Staff, ServiceLog, ConfirmationRequest, Accolade
from App.models import RequestStatus
from .AccoladeController import check_and_award_accolades


def validate_hours(hours):
    if hours <= 0:
        return {"success": False, "message": "Hours must be greater than 0"}
    if hours > 24:
        return {"success": False, "message": "Hours cannot exceed 24 per session"}
    return {"success": True, "message": "Valid hours"}

def submit_hours(hours, description, current_user):
    if not current_user or current_user["role"] != "student":
        return {"success": False, "message": "Only students can submit hours"}
    
    validation_result = validateHours(hours)
    if not validation_result["success"]:
        return validation_result
    
    student_user = User.query.filter_by(username=current_user["username"]).first()
    if not student_user or not student_user.student:
        return {"success": False, "message": "Student profile not found"}
    
    confirmation_request = ConfirmationRequest(
        student_id=student_user.student.id,
        hours=hours,
        description=description,
        status=RequestStatus.PENDING
    )
    
    db.session.add(confirmation_request)
    db.session.commit()
    
    return {
        "success": True, 
        "message": f"Submitted {hours} hours for approval (Request ID: {confirmation_request.id})\nStaff will review and approve your request."
    }

def get_student_requests(current_user):
    if not current_user or current_user["role"] != "student":
        return {"success": False, "message": "Only students can view their requests"}
    
    student_user = User.query.filter_by(username=current_user["username"]).first()
    if not student_user or not student_user.student:
        return {"success": False, "message": "Student profile not found"}
    
    requests = ConfirmationRequest.query.filter_by(
        student_id=student_user.student.id
    ).order_by(ConfirmationRequest.requested_at.desc()).all()
    
    if not requests:
        return {
            "success": True, 
            "message": "No requests submitted yet. Use 'flask service submit-hours <hours>' to submit your first request.",
            "requests": []
        }
    
    formatted_requests = []
    for req in requests:
        formatted_requests.append({
            "id": req.id,
            "hours": req.hours,
            "status": req.status.value.title(),
            "description": req.description,
            "submitted_at": req.requested_at.strftime('%Y-%m-%d %H:%M') if req.requested_at else "Unknown",
            "reason": req.reason
        })
    
    return {
        "success": True,
        "message": f"Your Hour Requests:",
        "requests": formatted_requests
    }

def get_pending_requests_for_student(student_username):
    student_user = User.query.filter_by(username=student_username).first()
    if not student_user or not student_user.student:
        return {"success": False, "message": f"Student '{student_username}' not found", "requests": []}
    
    requests = ConfirmationRequest.query.filter_by(
        student_id=student_user.student.id,
        status=RequestStatus.PENDING
    ).all()
    
    formatted_requests = []
    for req in requests:
        formatted_requests.append({
            "id": req.id,
            "hours": req.hours,
            "description": req.description,
            "submitted_at": req.requested_at.strftime('%Y-%m-%d %H:%M') if req.requested_at else "Unknown"
        })
    
    return {
        "success": True,
        "message": f"Pending requests for {student_username}",
        "student": {
            "username": student_username,
            "current_hours": student_user.student.total_hours
        },
        "requests": formatted_requests
    }

def approve_request(request_id, staff_user):
    request = ConfirmationRequest.query.get(request_id)
    if not request:
        return {"success": False, "message": "Request not found"}
    
    if request.status != RequestStatus.PENDING:
        return {"success": False, "message": "Request is not pending"}
    
    request.staff_id = staff_user.staff.id
    request.status = RequestStatus.APPROVED
    request.responded_at = datetime.utcnow()
    
    service_log = ServiceLog(
        student_id=request.student_id,
        staff_id=staff_user.id,
        hours=request.hours,
        description=request.description,
    )
    db.session.add(service_log)
    
    student_profile = Student.query.get(request.student_id)
    student_profile.total_hours += request.hours
    
    check_and_award_accolades(student_profile)
    
    db.session.commit()
    
    student_user = User.query.get(student_profile.user_id)
    return {
        "success": True,
        "message": f"Approved! {student_user.username} now has {student_profile.total_hours} total hours."
    }

def reject_request(request_id, staff_user, reason=None):
    request = ConfirmationRequest.query.get(request_id)
    if not request:
        return {"success": False, "message": "Request not found"}
    
    if request.status != RequestStatus.PENDING:
        return {"success": False, "message": "Request is not pending"}
    
    request.staff_id = staff_user.staff.id
    request.status = RequestStatus.REJECTED
    request.responded_at = datetime.utcnow()
    if reason:
        request.reason=reason

    db.session.commit()
    
    student_user = User.query.get(request.student.user_id)
    message = f"Rejected request from {student_user.username}"
    if reason:
        message += f"\nReason: {reason}"
    
    return {"success": True, "message": message}

def get_student_service_logs(current_user):
    if not current_user or current_user["role"] != "student":
        return {"success": False, "message": "Only students can view their service logs"}
    
    student_user = User.query.filter_by(username=current_user["username"]).first()
    if not student_user or not student_user.student:
        return {"success": False, "message": "Student profile not found"}
    
    service_logs = ServiceLog.query.filter_by(
        student_id=student_user.student.id
    ).order_by(ServiceLog.logged_at.desc()).all()
    
    if not service_logs:
        return {
            "success": True,
            "message": "No confirmed service logs found. Submit hours for approval first!",
            "logs": [],
            "total_hours": student_user.student.total_hours
        }
    
    formatted_logs = []
    for log in service_logs:
        staff_user = User.query.get(log.staff_id)
        formatted_logs.append({
            "id": log.id,
            "hours": log.hours,
            "description": log.description,
            "approved_by": staff_user.username,
            "logged_at": log.logged_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return {
        "success": True,
        "message": f"Confirmed Service Logs for {current_user['username']}:",
        "logs": formatted_logs,
        "total_hours": student_user.student.total_hours
    }

def get_pending_students():
    pending_requests = ConfirmationRequest.query.filter_by(status=RequestStatus.PENDING).all()
    
    if not pending_requests:
        return {
            "success": True,
            "message": "No pending requests from any students.",
            "students": []
        }
    
    students_with_requests = {}
    for req in pending_requests:
        student_id = req.student_id
        if student_id not in students_with_requests:
            students_with_requests[student_id] = []
        students_with_requests[student_id].append(req)
    
    formatted_students = []
    for student_id, requests in students_with_requests.items():
        student = Student.query.get(student_id)
        student_user = User.query.get(student.user_id)
        
        total_pending_hours = sum(req.hours for req in requests)
        formatted_students.append({
            "username": student_user.username,
            "current_hours": student.total_hours,
            "pending_requests": len(requests),
            "total_pending_hours": total_pending_hours
        })
    
    return {
        "success": True,
        "message": f"Students with Pending Requests ({len(students_with_requests)} students):",
        "students": formatted_students
    }

def interactive_request_review(student_username, staff_user):
    while True:
        result = get_pending_requests_for_student(student_username)
        if not result["success"]:
            print(result["message"])
            break
        
        requests = result["requests"]
        if not requests:
            print(f"\nNo pending requests for {student_username}.")
            break
        
        display_student_requests(student_username, requests, result["student"])
        
        choice = get_request_choice(requests)
        if choice is None:
            print("Exiting review mode.")
            break
        elif choice is False:
            continue
        
        selected_request = requests[choice]
        
        display_request_details(selected_request, student_username)
        
        result = process_request_decision(selected_request["id"], staff_user)
        print(result["message"])
        
        if not result["success"]:
            continue
        
        continue_review = input("\nContinue reviewing? (y/n): ").strip().lower()
        if continue_review != 'y':
            break

def display_student_requests(student_username, requests, student_info):
    print(f"\nReviewing requests for: {student_username}")
    print(f"Current total hours: {student_info['current_hours']}")
    print(f"Pending requests ({len(requests)} total):")
    print("-" * 80)
    for i, req in enumerate(requests, 1):
        print(f"[{i}] Hours: {req['hours']} | {req['description']}")
        print(f"     Submitted: {req['submitted_at']}")
        print()

def get_request_choice(requests):
    try:
        choice = input(f"Select request (1-{len(requests)}) or 'q' to quit: ").strip()
        
        if choice.lower() == 'q':
            return None
        
        choice_num = int(choice)
        if choice_num < 1 or choice_num > len(requests):
            print("Invalid selection. Please try again.")
            return False
        
        return choice_num - 1
        
    except ValueError:
        print("Invalid input. Please enter a number or 'q'.")
        return False
    except KeyboardInterrupt:
        print("\nExiting review mode.")
        return None

def display_request_details(request, student_username):
    print(f"\nReviewing Request #{request['id']}:")
    print(f"Student: {student_username}")
    print(f"Hours: {request['hours']}")
    print(f"Description: {request['description']}")
    print(f"Submitted: {request['submitted_at']}")

def process_request_decision(request_id, staff_user):
    decision = input("\nApprove this request? (y/n/r for reason): ").strip().lower()
    
    if decision == 'y':
        return approve_request(request_id, staff_user)
    elif decision == 'n':
        return reject_request(request_id, staff_user)
    elif decision == 'r':
        reason = input("Enter rejection reason: ").strip()
        return reject_request(request_id, staff_user, reason)
    else:
        return {"success": False, "message": "Invalid choice. Skipping this request."}