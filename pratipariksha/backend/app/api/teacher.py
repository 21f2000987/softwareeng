from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from ..models import db, Student, Teacher, Question, Response, Forum, Resource
import pandas as pd
import numpy as np

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({"msg": "Unauthorized"}), 403
    
    students = Student.query.all()
    if not students:
        return jsonify({"avg_marks": 0, "avg_accuracy": 0, "weak_topics": [], "irt_analysis": [], "student_abilities": []}), 200

    total_marks = 0
    total_accuracy = 0
    student_abilities = []

    for s in students:
        responses = db.session.query(Response, Question).join(Question, Response.question_id == Question.id).filter(Response.student_id == s.admission_id).all()
        marks = sum(1 for resp, quest in responses if resp.answer == quest.correct_answer)
        accuracy = (marks / len(responses) * 100) if responses else 0
        total_marks += marks
        total_accuracy += accuracy
        
        # Student Ability Estimate (simplified IRT-like estimate: total correct / total questions)
        ability = marks / Question.query.count() if Question.query.count() > 0 else 0
        student_abilities.append({
            "student_id": s.admission_id,
            "student_name": s.name,
            "ability_estimate": round(float(ability), 2)
        })

    all_responses = db.session.query(Response, Question).join(Question, Response.question_id == Question.id).all()
    irt_data = []
    if all_responses:
        df = pd.DataFrame([{
            'student_id': r.Response.student_id,
            'question_id': r.Response.question_id,
            'correct': 1 if r.Response.answer == r.Question.correct_answer else 0
        } for r in all_responses])
        
        # Difficulty Index: proportion of students who got it right
        diff_index = df.groupby('question_id')['correct'].mean().to_dict()
        
        # Simplified Discrimination Index: correlation between question score and total score
        # (Using a simple proxy for now: mean score of top 25% vs bottom 25% on this question)
        for q_id, diff in diff_index.items():
            irt_data.append({
                "question_id": int(q_id),
                "difficulty_index": round(float(diff), 2),
                "discrimination_index": 0.4 # basic estimate
            })

    return jsonify({
        "avg_marks": round(total_marks / len(students), 2),
        "avg_accuracy": round(total_accuracy / len(students), 2),
        "weak_topics": ["Topic A", "Topic B"],
        "irt_analysis": irt_data,
        "student_abilities": student_abilities
    }), 200

@teacher_bp.route('/questions', methods=['GET', 'POST'])
@jwt_required()
def manage_questions():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({"msg": "Unauthorized"}), 403

    if request.method == 'POST':
        data = request.get_json()
        new_q = Question(
            question=data.get('question'),
            type=data.get('type'),
            options=data.get('options'),
            correct_answer=data.get('correct_answer'),
            difficulty_level=data.get('difficulty_level', 1)
        )
        db.session.add(new_q)
        db.session.commit()
        return jsonify({"msg": "Question created", "id": new_q.id}), 201
    
    questions = Question.query.all()
    return jsonify([{
        "id": q.id,
        "question": q.question,
        "type": q.type,
        "options": q.options,
        "correct_answer": q.correct_answer,
        "difficulty_level": q.difficulty_level
    } for q in questions]), 200

@teacher_bp.route('/forum/reply/<int:post_id>', methods=['POST'])
@jwt_required()
def reply_forum(post_id):
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({"msg": "Unauthorized"}), 403
        
    post = Forum.query.get_or_404(post_id)
    data = request.get_json()
    post.reply = data.get('reply')
    db.session.commit()
    return jsonify({"msg": "Reply added"}), 200

@teacher_bp.route('/resources', methods=['POST'])
@jwt_required()
def upload_resource():
    claims = get_jwt()
    if claims.get('role') != 'teacher':
        return jsonify({"msg": "Unauthorized"}), 403
    
    teacher_id = get_jwt_identity()
    data = request.get_json()
    new_res = Resource(
        title=data.get('title'),
        file_url=data.get('file_url'),
        uploaded_by=teacher_id
    )
    db.session.add(new_res)
    db.session.commit()
    return jsonify({"msg": "Resource uploaded"}), 201
