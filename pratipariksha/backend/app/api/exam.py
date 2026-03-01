from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models import db, Student, Question, Response, Exam, Mood, LooBreak
from datetime import datetime

exam_bp = Blueprint('exam', __name__)

@exam_bp.route('/questions', methods=['GET'])
@jwt_required()
def get_exam_questions():
    exam = Exam.query.first()
    if not exam or exam.status != 'started':
        return jsonify({"msg": "Exam not started"}), 403
        
    questions = Question.query.limit(20).all()
    return jsonify([{
        "id": q.id,
        "question": q.question,
        "type": q.type,
        "options": q.options
    } for q in questions]), 200

@exam_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_response():
    student_id = get_jwt_identity()
    data = request.get_json()
    
    # data: [{"question_id": 1, "answer": "X"}, ...]
    for r in data:
        existing = Response.query.filter_by(student_id=student_id, question_id=r.get('question_id')).first()
        if existing:
            existing.answer = r.get('answer')
        else:
            new_resp = Response(
                student_id=student_id,
                question_id=r.get('question_id'),
                answer=r.get('answer')
            )
            db.session.add(new_resp)
            
    db.session.commit()
    return jsonify({"msg": "Responses submitted"}), 200

@exam_bp.route('/mood', methods=['POST'])
@jwt_required()
def log_mood():
    student_id = get_jwt_identity()
    data = request.get_json()
    new_mood = Mood(student_id=student_id, mood=data.get('mood'))
    db.session.add(new_mood)
    db.session.commit()
    return jsonify({"msg": "Mood logged"}), 201

@exam_bp.route('/loo-break/start', methods=['POST'])
@jwt_required()
def start_loo_break():
    student_id = get_jwt_identity()
    new_break = LooBreak(student_id=student_id, start_time=datetime.utcnow())
    db.session.add(new_break)
    db.session.commit()
    
    # Track currently on loo break
    count = LooBreak.query.filter(LooBreak.end_time == None).count()
    return jsonify({"msg": "Loo break started", "current_on_break": count}), 201

@exam_bp.route('/loo-break/end', methods=['POST'])
@jwt_required()
def end_loo_break():
    student_id = get_jwt_identity()
    active_break = LooBreak.query.filter_by(student_id=student_id, end_time=None).first()
    if active_break:
        active_break.end_time = datetime.utcnow()
        db.session.commit()
        
    count = LooBreak.query.filter(LooBreak.end_time == None).count()
    return jsonify({"msg": "Loo break ended", "current_on_break": count}), 200

@exam_bp.route('/status', methods=['GET'])
@jwt_required()
def exam_status():
    exam = Exam.query.first()
    count = LooBreak.query.filter(LooBreak.end_time == None).count()
    return jsonify({
        "status": exam.status if exam else "stopped",
        "students_on_loo_break": count
    }), 200
