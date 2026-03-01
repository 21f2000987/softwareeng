from app import create_app
from app.models import db, Admin, Exam, Student, Teacher
from werkzeug.security import generate_password_hash
import os

app = create_app()

# initialize database and default records on startup
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print(f"Database file should be at: {app.config['SQLALCHEMY_DATABASE_URI']}")
    # default admin
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        print("Admin user created.")
    if not Exam.query.first():
        exam = Exam(status='stopped')
        db.session.add(exam)
        print("Default exam entry created.")
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
