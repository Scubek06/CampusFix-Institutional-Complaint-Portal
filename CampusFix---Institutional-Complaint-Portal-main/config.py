import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campusfix-secret-key-2024'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/campusfix'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # ✉️ Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # Default sender if not specified in Message()
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

    # Complaint categories
    COMPLAINT_CATEGORIES = [
        'Classroom',
        'Laboratory',
        'Hostel',
        'Mess/Food',
        'Internet Connectivity',
        'Water Supply',
        'Cleanliness',
        'Electrical',
        'Security',
        'Library',
        'Sports Facility',
        'Other'
    ]
    
    # Complaint statuses
    COMPLAINT_STATUSES = [
        'submitted',
        'under_review',
        'work_in_progress',
        'resolved',
        'rejected'
    ]