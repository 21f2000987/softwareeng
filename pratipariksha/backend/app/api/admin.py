from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from ..models import db, Admin, Student, Teacher, Exam, LooBreak
from werkzeug.security import generate_password_hash
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/exam-toggle', methods=['POST'])
@jwt_required()
def toggle_exam():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Unauthorized"}), 403
        
    data = request.get_json()
    status = data.get('status') # 'started' or 'stopped'
    
    exam = Exam.query.first()
    if not exam:
        exam = Exam()
        db.session.add(exam)
        
    exam.status = status
    if status == 'started':
        exam.start_time = datetime.utcnow()
    else:
        exam.end_time = datetime.utcnow()
        
    db.session.commit()
    return jsonify({"msg": f"Exam {status}", "status": exam.status}), 200

@admin_bp.route('/users', methods=['GET', 'POST'])
@jwt_required()
def manage_users():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Unauthorized"}), 403
        
    if request.method == 'POST':
        data = request.get_json()
        role = data.get('role')
        name = data.get('name')
        email = data.get('email')
        password = generate_password_hash(data.get('password'))
        uid = data.get('id') # admission_id or employee_id
        
        if role == 'student':
            new_user = Student(admission_id=uid, name=name, email=email, password=password)
        elif role == 'teacher':
            new_user = Teacher(employee_id=uid, name=name, email=email, password=password)
        else:
            return jsonify({"msg": "Invalid role"}), 400
            
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User created"}), 201
        
    students = Student.query.all()
    teachers = Teacher.query.all()
    return jsonify({
        "students": [{"admission_id": s.admission_id, "name": s.name, "email": s.email} for s in students],
        "teachers": [{"employee_id": t.employee_id, "name": t.name, "email": t.email} for t in teachers]
    }), 200

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def system_analytics():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Unauthorized"}), 403
        
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    active_exams = Exam.query.filter_by(status='started').count()
    
    return jsonify({
        "total_students": total_students,
        "total_teachers": total_teachers,
        "active_exams": active_exams
    }), 200

@admin_bp.route('/loo-breaks', methods=['GET'])
@jwt_required()
def monitor_loo_breaks():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"msg": "Unauthorized"}), 403
        
    active_breaks = LooBreak.query.filter(LooBreak.end_time == None).all()
    result = []
    for b in active_breaks:
        s = Student.query.get(b.student_id)
        result.append({
            "student_name": s.name if s else "Unknown",
            "student_id": b.student_id,
            "start_time": b.start_time.isoformat()
        })
    return jsonify(result), 200
