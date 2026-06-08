import os
from werkzeug.utils import secure_filename
from PIL import Image
import time
from config import Config

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_image(file):
    """Save uploaded image and return filename"""
    if file and allowed_file(file.filename):
        try:
            # Create secure filename
            filename = secure_filename(file.filename)
            
            # Add timestamp to make filename unique
            name, ext = os.path.splitext(filename)
            timestamp = int(time.time())
            unique_filename = f"{name}_{timestamp}{ext}"
            
            # Ensure upload folder exists
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            
            # Save file path
            filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
            
            # Save the file
            file.save(filepath)
            
            # Optimize image if it's too large
            try:
                img = Image.open(filepath)
                # Resize if image is too large (max 1024x1024)
                img.thumbnail((1024, 1024))
                img.save(filepath, optimize=True, quality=85)
            except Exception as e:
                print(f"Image optimization error: {e}")
            
            print(f"✅ Image saved: {unique_filename}")
            return unique_filename
            
        except Exception as e:
            print(f"❌ Error saving image: {e}")
            return None
    
    return None

def delete_image(filename):
    """Delete image file"""
    try:
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        print(f"Error deleting image: {e}")
    return False

def get_dashboard_stats(mongo, user_id=None, role=None):
    """Get dashboard statistics based on user role"""
    stats = {}
    
    if role == 'student':
        stats['total'] = mongo.db.complaints.count_documents({'submitted_by': user_id})
        stats['pending'] = mongo.db.complaints.count_documents({
            'submitted_by': user_id,
            'status': {'$in': ['submitted', 'under_review']}
        })
        stats['resolved'] = mongo.db.complaints.count_documents({
            'submitted_by': user_id,
            'status': 'resolved'
        })
        stats['in_progress'] = mongo.db.complaints.count_documents({
            'submitted_by': user_id,
            'status': 'work_in_progress'
        })
    
    elif role == 'staff':
        stats['assigned'] = mongo.db.complaints.count_documents({'assigned_to': user_id})
        stats['pending'] = mongo.db.complaints.count_documents({
            'assigned_to': user_id,
            'status': {'$in': ['submitted', 'under_review']}
        })
        stats['resolved'] = mongo.db.complaints.count_documents({
            'assigned_to': user_id,
            'status': 'resolved'
        })
    
    elif role == 'admin':
        stats['total_users'] = mongo.db.users.count_documents({})
        stats['total_complaints'] = mongo.db.complaints.count_documents({})
        stats['pending_complaints'] = mongo.db.complaints.count_documents({
            'status': {'$in': ['submitted', 'under_review']}
        })
        stats['resolved_complaints'] = mongo.db.complaints.count_documents({
            'status': 'resolved'
        })
        stats['students'] = mongo.db.users.count_documents({'role': 'student'})
        stats['staff'] = mongo.db.users.count_documents({'role': 'staff'})
    
    return stats