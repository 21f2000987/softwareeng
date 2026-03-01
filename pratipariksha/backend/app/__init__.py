from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .models import db
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))

def create_app():
    # serve front-end static assets from the workspace so the browser can load
    # HTML/JS/CSS over HTTP instead of via file://.  this keeps the same origin
    # as the API and avoids CORS/blocked requests.
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '../frontend'))
    # use a separate URL path for static assets to avoid the static handler
    # intercepting requests for '/'.  we'll provide our own catch-all view for
    # serving frontend HTML pages below.
    app = Flask(__name__, static_folder=frontend_path, static_url_path='/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    print(f"Using database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

    db.init_app(app)
    JWTManager(app)
    CORS(app)

    # Register Blueprints
    from .api.auth import auth_bp
    from .api.student import student_bp
    from .api.teacher import teacher_bp
    from .api.admin import admin_bp
    from .api.exam import exam_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(exam_bp, url_prefix='/api/exam')

    # quick route for home; static files can be referenced directly as
    # http://localhost:5000/index.html, but this makes root work as well.
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    # catch-all route for other frontend pages (login.html, student_portal.html, etc.)
    @app.route('/<path:filename>')
    def serve_frontend(filename):
        # don't interfere with API routes
        if filename.startswith('api/'):
            # let Flask return 404 or match other routes
            from flask import abort
            abort(404)
        return app.send_static_file(filename)

    return app
