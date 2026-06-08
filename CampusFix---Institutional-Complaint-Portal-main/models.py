from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.password = user_data['password']
        self.role = user_data['role']
        self.department = user_data.get('department', '')
        self.roll_number = user_data.get('roll_number', '')
        self.phone = user_data.get('phone', '')
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.is_active = user_data.get('is_active', True)
    
    def get_id(self):
        return self.id
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return self.is_active
    
    @property
    def is_anonymous(self):
        return False

class Complaint:
    def __init__(self, complaint_data):
        self.id = str(complaint_data['_id'])
        self.title = complaint_data['title']
        self.description = complaint_data['description']
        self.category = complaint_data['category']
        self.location = complaint_data['location']
        self.submitted_by = complaint_data['submitted_by']
        self.submitted_by_email = complaint_data['submitted_by_email']
        self.status = complaint_data['status']
        self.assigned_to = complaint_data.get('assigned_to', None)
        self.votes = complaint_data.get('votes', [])
        self.vote_count = complaint_data.get('vote_count', 0)
        self.images = complaint_data.get('images', [])
        self.timeline = complaint_data.get('timeline', [])
        self.resolution_notes = complaint_data.get('resolution_notes', '')
        self.created_at = complaint_data.get('created_at', datetime.utcnow())
        self.updated_at = complaint_data.get('updated_at', datetime.utcnow())
    
    @staticmethod
    def assign_authority(mongo, category):
        # Find staff user for this category
        category_map = {
            'Classroom': 'Academic Department',
            'Laboratory': 'Lab Administrator',
            'Hostel': 'Hostel Warden',
            'Mess/Food': 'Mess Committee',
            'Internet Connectivity': 'IT Department',
            'Water Supply': 'Maintenance Department',
            'Cleanliness': 'Housekeeping Department',
            'Electrical': 'Electrical Department',
            'Security': 'Security Department',
            'Library': 'Librarian',
            'Sports Facility': 'Sports Department',
            'Other': 'Administrative Office'
        }
        
        # Try to find a staff member for this department
        department = category_map.get(category, 'Administrative Office')
        staff_user = mongo.db.users.find_one({
            'role': 'staff',
            'department': department
        })
        
        return str(staff_user['_id']) if staff_user else None
    
    @staticmethod
    def vote_complaint(mongo, complaint_id, user_id):
        try:
            complaint = mongo.db.complaints.find_one({'_id': ObjectId(complaint_id)})
            
            if not complaint:
                return None
            
            if user_id in complaint.get('votes', []):
                # Remove vote
                mongo.db.complaints.update_one(
                    {'_id': ObjectId(complaint_id)},
                    {
                        '$pull': {'votes': user_id},
                        '$inc': {'vote_count': -1}
                    }
                )
                return False
            else:
                # Add vote
                mongo.db.complaints.update_one(
                    {'_id': ObjectId(complaint_id)},
                    {
                        '$push': {'votes': user_id},
                        '$inc': {'vote_count': 1}
                    }
                )
                return True
        except Exception as e:
            print(f"Vote error: {e}")
            return None
    
    @staticmethod
    def update_status(mongo, complaint_id, status, note, updated_by):
        try:
            timeline_entry = {
                'status': status,
                'timestamp': datetime.utcnow(),
                'note': note,
                'updated_by': updated_by
            }
            
            result = mongo.db.complaints.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$set': {
                        'status': status,
                        'updated_at': datetime.utcnow()
                    },
                    '$push': {'timeline': timeline_entry}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Status update error: {e}")
            return False