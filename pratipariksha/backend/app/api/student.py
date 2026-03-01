from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from ..models import db, Student, Forum, Resource, Response, Question, Exam
from sqlalchemy import func
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    student_id = get_jwt_identity()
    claims = get_jwt()
    if claims.get('role') != 'student':
        return jsonify({"msg": "Unauthorized"}), 403
    
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"msg": "Student not found"}), 404
    
    responses = db.session.query(Response, Question).join(Question, Response.question_id == Question.id).filter(Response.student_id == student_id).all()
    total_marks = sum(1 for resp, quest in responses if resp.answer == quest.correct_answer)
    accuracy = (total_marks / len(responses) * 100) if responses else 0
    
    all_responses = db.session.query(Response, Question).join(Question, Response.question_id == Question.id).all()
    scores = {}
    for resp, quest in all_responses:
        if resp.answer == quest.correct_answer:
            scores[resp.student_id] = scores.get(resp.student_id, 0) + 1
    
    all_students = Student.query.all()
    for s in all_students:
        if s.admission_id not in scores:
            scores[s.admission_id] = 0
            
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (sid, score) in enumerate(sorted_scores) if sid == student_id), 0)

    return jsonify({
        "total_marks": total_marks,
        "rank": rank,
        "accuracy": round(accuracy, 2),
        "points": student.points,
        "level": student.level,
        "badges": student.badges.split(',') if student.badges else []
    }), 200

@student_bp.route('/upcoming-tests', methods=['GET'])
@jwt_required()
def get_upcoming_tests():
    exam = Exam.query.first()
    if not exam:
        return jsonify([]), 200
        
    tests = []
    if exam.status != 'stopped':
        tests.append({
            "id": exam.id,
            "test_name": "General Competency Test",
            "date": exam.start_time.isoformat() if exam.start_time else "TBD",
            "status": exam.status
        })
    return jsonify(tests), 200

@student_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_leaderboard():
    all_students = Student.query.all()
    leaderboard = []
    for s in all_students:
        responses = db.session.query(Response, Question).join(Question, Response.question_id == Question.id).filter(Response.student_id == s.admission_id).all()
        marks = sum(1 for resp, quest in responses if resp.answer == quest.correct_answer)
        leaderboard.append({
            "name": s.name,
            "marks": marks,
            "points": s.points
        })
    
    leaderboard.sort(key=lambda x: (x['marks'], x['points']), reverse=True)
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1
        
    return jsonify(leaderboard), 200

@student_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    student_id = get_jwt_identity()
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"msg": "Student not found"}), 404
    return jsonify({
        "name": student.name,
        "admission_id": student.admission_id,
        "email": student.email,
        "points": student.points,
        "level": student.level
    }), 200

@student_bp.route('/forum', methods=['GET', 'POST'])
@jwt_required()
def forum():
    student_id = get_jwt_identity()
    if request.method == 'POST':
        data = request.get_json()
        new_post = Forum(
            student_id=student_id,
            post=data.get('post'),
            poll=data.get('poll'),
            reply=None
        )
        db.session.add(new_post)
        db.session.commit()
        return jsonify({"msg": "Post created", "id": new_post.id}), 201
    
    posts = Forum.query.order_by(Forum.id.desc()).all()
    result = []
    for p in posts:
        s = Student.query.get(p.student_id)
        result.append({
            "id": p.id,
            "student_name": s.name if s else "Unknown",
            "post": p.post,
            "reply": p.reply,
            "poll": p.poll,
            "vote": p.vote
        })
    return jsonify(result), 200

@student_bp.route('/forum/vote/<int:post_id>', methods=['POST'])
@jwt_required()
def vote(post_id):
    post = Forum.query.get_or_404(post_id)
    post.vote += 1
    db.session.commit()
    return jsonify({"msg": "Voted", "votes": post.vote}), 200

@student_bp.route('/resources', methods=['GET'])
@jwt_required()
def get_resources():
    resources = Resource.query.all()
    return jsonify([{
        "id": r.id,
        "title": r.title,
        "file_url": r.file_url
    } for r in resources]), 200

@student_bp.route('/chatbot', methods=['POST'])
@jwt_required()
def chatbot_ask():
    data = request.get_json()
    query = data.get('query', '').lower()
    
    # Very basic "AI" logic mimicking search through resources
    resources = Resource.query.all()
    questions = Question.query.all()
    
    # Check if query matches any resource title or question
    response = "I am trained on your study materials. "
    found = False
    
    for r in resources:
        if query in r.title.lower():
            response += f"You can find information about this in your resource: '{r.title}'. "
            found = True
            break
            
    if not found:
        for q in questions:
            if query in q.question.lower():
                response += f"A similar topic was found in the question bank: '{q.question}'. The correct answer for that was '{q.correct_answer}'."
                found = True
                break
                
    if not found:
        response += "I'm not exactly sure about that, but try checking the Resources section for more details!"
        
    return jsonify({"reply": response}), 200
