from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from bson import ObjectId
from datetime import datetime
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_mail import Mail, Message

from config import Config
from utils import save_image, get_dashboard_stats

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ------------------- Flask Configs -------------------
app.config.from_object(Config)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")

# Email Configs
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
mail = Mail(app)

# Upload folder
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load additional configs
#app.config.from_object(Config)

# ------------------- Extensions -------------------
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'info'

# ------------------- MongoDB Connection -------------------
mongo_uri = os.getenv('MONGO_URI') or Config.MONGO_URI

try:
    if mongo_uri and 'localhost' not in mongo_uri:
        print(f"🌐 Connecting to MongoDB Atlas: {mongo_uri}")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    else:
        print("🏠 Connecting to local MongoDB (fallback)")
        client = MongoClient('localhost', 27017, serverSelectionTimeoutMS=5000)

    client.admin.command('ping')
    db = client['campusfix']
    print("✅ MongoDB connected successfully!")

except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    if mongo_uri:
        print("🚨 Deployment failed: Check your Atlas Network Access, credentials, and MONGO_URI")
    db = None


def get_db():
    global db
    if db is None:
        raise RuntimeError('Database connection not available. Check MONGO_URI and Atlas network access.')
    return db

@app.errorhandler(500)
def internal_server_error(e):
    print(f"🔥 Internal server error: {e}")
    import traceback
    traceback.print_exc()
    return "Internal server error. Check server logs.", 500

# ------------------- Email Function -------------------
def send_verification_email(user_email):
    try:
        token = serializer.dumps(user_email, salt="email-confirm")
        verify_link = url_for("verify_email", token=token, _external=True)
        msg = Message(
            subject="CampusFix Email Verification",
            sender=app.config["MAIL_USERNAME"],
            recipients=[user_email]
        )
        msg.body = f"""Welcome to CampusFix!

Please click the link below to verify your email:

{verify_link}

If you did not create this account, please ignore this email.
"""
        mail.send(msg)
        print(f"✅ Verification email sent to {user_email}")
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")

# Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'info'

# MongoDB Connection

# Load .env variables
load_dotenv()

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.role = user_data['role']
        self.department = user_data.get('department', '')
        self.roll_number = user_data.get('roll_number', '')
        self.phone = user_data.get('phone', '')
        self.created_at = user_data.get('created_at', datetime.utcnow())
    
    def get_id(self):
        return self.id
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    if db is None:
        return None
    try:
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

@app.context_processor
def utility_processor():
    return {
        'categories': Config.COMPLAINT_CATEGORIES,
        'statuses': Config.COMPLAINT_STATUSES,
        'now': datetime.utcnow()
    }

@app.before_request
def check_db_connection():
    if db is None:
        return "MongoDB connection is not available. Please configure MONGO_URI and retry.", 500

@app.route('/debug/health')
def debug_health():
    return jsonify({
        'status': 'ok',
        'mongo_uri': os.getenv('MONGO_URI', 'not-set'),
        'db_connected': db is not None
    })

@app.route('/')
def index():
    if db is None:
        return "MongoDB not connected. Please start MongoDB service.", 500
    
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif current_user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
    
    try:
        recent_complaints = list(db.complaints.find().sort('created_at', -1).limit(5))
        stats = {
            'total_complaints': db.complaints.count_documents({}),
            'resolved_complaints': db.complaints.count_documents({'status': 'resolved'}),
            'active_users': db.users.count_documents({})
        }
    except:
        recent_complaints = []
        stats = {'total_complaints': 0, 'resolved_complaints': 0, 'active_users': 0}
    
    return render_template('index.html', recent_complaints=recent_complaints, stats=stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password', 'danger')
            return render_template('login.html')
        
        try:
            # Find user by email
            user_data = db.users.find_one({'email': email})
            
            if user_data:

                # 🔴 EMAIL VERIFICATION CHECK (NEW CODE)
                if not user_data.get("verified", False):
                    flash('Please verify your email before logging in.', 'warning')
                    return render_template('login.html')
                
                # Check password using bcrypt
                if bcrypt.check_password_hash(user_data['password'], password):
                    user = User(user_data)
                    login_user(user, remember=True)
                    
                    flash(f'Welcome , {user.username}!', 'success')
                    
                    # Redirect based on role
                    if user.role == 'student':
                        return redirect(url_for('student_dashboard'))
                    elif user.role == 'staff':
                        return redirect(url_for('staff_dashboard'))
                    elif user.role == 'admin':
                        return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid password', 'danger')
            else:
                flash('Email not found', 'danger')
                
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        roll_number = request.form.get('roll_number', '').strip()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user exists
        if db.users.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        if db.users.find_one({'username': username}):
            flash('Username already taken', 'danger')
            return render_template('register.html')
        
        try:
            # Hash password
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            
            # Create user
            user_data = {
                'username': username,
                'email': email,
                'password': hashed_password,
                'role': role,
                'roll_number': roll_number if role == 'student' else '',
                'department': department,
                'phone': phone,
                'created_at': datetime.utcnow()
            }
            
            result = db.users.insert_one(user_data)
            send_verification_email(email)
            
            if result.inserted_id:
                flash('Registration successful! Please verify your email.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed', 'danger')
                
        except Exception as e:
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/setup-database')
def setup_database():
    try:
        # Create collections
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
        if 'complaints' not in db.list_collection_names():
            db.create_collection('complaints')
        
        # Create indexes
        db.users.create_index('email', unique=True)
        db.users.create_index('username', unique=True)
        
        # Create admin if not exists
        if db.users.count_documents({'role': 'admin'}) == 0:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_data = {
                'username': 'admin',
                'email': 'admin@campusfix.com',
                'password': hashed_password,
                'role': 'admin',
                'department': 'Administration',
                'created_at': datetime.utcnow()
            }
            db.users.insert_one(admin_data)
            flash('Admin created - Email: admin@campusfix.com, Password: admin123', 'success')
        
        # Create staff accounts for each department
        staff_accounts = [
            {'username': 'academic_staff', 'email': 'academic@campusfix.com', 'department': 'Academic Department'},
            {'username': 'lab_staff', 'email': 'lab@campusfix.com', 'department': 'Lab Administrator'},
            {'username': 'hostel_staff', 'email': 'hostel@campusfix.com', 'department': 'Hostel Warden'},
            {'username': 'mess_staff', 'email': 'mess@campusfix.com', 'department': 'Mess Committee'},
            {'username': 'it_staff', 'email': 'it@campusfix.com', 'department': 'IT Department'},
            {'username': 'maintenance_staff', 'email': 'maintenance@campusfix.com', 'department': 'Maintenance Department'},
            {'username': 'housekeeping_staff', 'email': 'housekeeping@campusfix.com', 'department': 'Housekeeping Department'},
            {'username': 'electrical_staff', 'email': 'electrical@campusfix.com', 'department': 'Electrical Department'},
            {'username': 'security_staff', 'email': 'security@campusfix.com', 'department': 'Security Department'},
            {'username': 'library_staff', 'email': 'library@campusfix.com', 'department': 'Librarian'},
            {'username': 'sports_staff', 'email': 'sports@campusfix.com', 'department': 'Sports Department'},
            {'username': 'admin_staff', 'email': 'adminoffice@campusfix.com', 'department': 'Administrative Office'}
        ]
        
        for staff in staff_accounts:
            if db.users.count_documents({'email': staff['email']}) == 0:
                staff_data = {
                    'username': staff['username'],
                    'email': staff['email'],
                    'password': bcrypt.generate_password_hash('staff123').decode('utf-8'),
                    'role': 'staff',
                    'department': staff['department'],
                    'created_at': datetime.utcnow()
                }
                db.users.insert_one(staff_data)
                print(f"✅ Created staff: {staff['username']} - {staff['department']}")
        
        # Create a test student
        if db.users.count_documents({'email': 'student@test.com'}) == 0:
            student_data = {
                'username': 'Bhargav varun',
                'email': 'student@test.com',
                'password': bcrypt.generate_password_hash('student123').decode('utf-8'),
                'role': 'student',
                'roll_number': '2024CS001',
                'department': 'Computer Science',
                'phone': '1234567890',
                'created_at': datetime.utcnow()
            }
            db.users.insert_one(student_data)
            flash('Test student created - Email: student@test.com, Password: student123', 'success')
        
        # Create a test complaint
        staff_user = db.users.find_one({'email': 'hostel@campusfix.com'})
        if staff_user:
            test_complaint = {
                'title': 'restrooms not clean',
                'description': 'The restrooms on ground floor need immediate cleaning',
                'category': 'Hostel',
                'location': 'Hostel Block A, Ground Floor',
                'submitted_by': str(db.users.find_one({'email': 'student@test.com'})['_id']),
                'submitted_by_email': 'student@test.com',
                'status': 'submitted',
                'assigned_to': str(staff_user['_id']),
                'votes': [],
                'vote_count': 0,
                'images': [],
                'timeline': [{
                    'status': 'submitted',
                    'timestamp': datetime.utcnow(),
                    'note': 'Complaint submitted',
                    'updated_by': 'Bhargav varun'
                }],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            db.complaints.insert_one(test_complaint)
            flash('Test complaint created - Assigned to hostel staff', 'success')
        
        # Count and display staff users
        staff_count = db.users.count_documents({'role': 'staff'})
        print(f"\n📊 Total staff users: {staff_count}")
        for staff in db.users.find({'role': 'staff'}):
            print(f"   - {staff['username']} ({staff['department']})")
        
        flash(f'Database setup complete! Created {staff_count} staff members.', 'success')
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('login'))

# Student Routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    try:
        complaints = list(db.complaints.find(
            {'submitted_by': current_user.id}
        ).sort('created_at', -1))
        
        stats = {
            'total': db.complaints.count_documents({'submitted_by': current_user.id}),
            'pending': db.complaints.count_documents({
                'submitted_by': current_user.id,
                'status': {'$in': ['submitted', 'under_review']}
            }),
            'resolved': db.complaints.count_documents({
                'submitted_by': current_user.id,
                'status': 'resolved'
            }),
            'in_progress': db.complaints.count_documents({
                'submitted_by': current_user.id,
                'status': 'work_in_progress'
            })
        }
        
        trending = list(db.complaints.find().sort('vote_count', -1).limit(5))
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        complaints = []
        stats = {'total': 0, 'pending': 0, 'in_progress': 0, 'resolved': 0}
        trending = []
    
    return render_template('student_dashboard.html', 
                         complaints=complaints, 
                         stats=stats,
                         trending=trending)

@app.route('/student/submit-complaint', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    if current_user.role != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        
        # Validate required fields
        if not all([title, description, category, location]):
            flash('Please fill in all fields', 'danger')
            return render_template('submit_complaint.html')
        
        if category == 'Select Category':
            flash('Please select a valid category', 'danger')
            return render_template('submit_complaint.html')
        
        # Handle image uploads
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            print(f"📸 Number of files received: {len(files)}")
            
            for file in files:
                if file and file.filename:
                    print(f"📸 Processing file: {file.filename}")
                    # Save the image using the imported function
                    filename = save_image(file)
                    if filename:
                        images.append(filename)
                        print(f"✅ Image saved: {filename}")
        
        print(f"📸 Total images saved: {len(images)}")
        
        try:
            # Define category to department mapping
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
            
            # Auto-assign based on category
            assigned_to = None
            department = category_map.get(category)
            
            if department:
                # Find staff user for this department
                staff_user = db.users.find_one({
                    'role': 'staff',
                    'department': department
                })
                if staff_user:
                    assigned_to = str(staff_user['_id'])
                    print(f"✅ Complaint assigned to: {staff_user['username']} ({department})")
                else:
                    print(f"⚠️ No staff found for department: {department}")
                    # Assign to any staff as fallback
                    any_staff = db.users.find_one({'role': 'staff'})
                    if any_staff:
                        assigned_to = str(any_staff['_id'])
                        print(f"✅ Complaint assigned to fallback staff: {any_staff['username']}")
            
            # Create complaint data with images
            complaint_data = {
                'title': title,
                'description': description,
                'category': category,
                'location': location,
                'submitted_by': current_user.id,
                'submitted_by_email': current_user.email,
                'status': 'submitted',
                'assigned_to': assigned_to,
                'votes': [],
                'vote_count': 0,
                'images': images,
                'timeline': [{
                    'status': 'submitted',
                    'timestamp': datetime.utcnow(),
                    'note': 'Complaint submitted',
                    'updated_by': current_user.username
                }],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert complaint into database
            result = db.complaints.insert_one(complaint_data)
            
            if result.inserted_id:
                flash('Complaint submitted successfully!', 'success')
                print(f"✅ Complaint created with ID: {result.inserted_id}")
                print(f"📸 Images in complaint: {images}")
                return redirect(url_for('student_dashboard'))
            else:
                flash('Error submitting complaint', 'danger')
                
        except Exception as e:
            print(f"❌ Complaint submission error: {e}")
            flash(f'Error submitting complaint: {str(e)}', 'danger')
    
    return render_template('submit_complaint.html')

@app.route('/complaint/<complaint_id>')
@login_required
def view_complaint(complaint_id):
    try:
        complaint = db.complaints.find_one({'_id': ObjectId(complaint_id)})
        
        if not complaint:
            flash('Complaint not found', 'danger')
            return redirect(url_for('index'))
        
        # Check permissions
        if current_user.role == 'student' and complaint['submitted_by'] != current_user.id:
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        # Get user info
        submitted_by = db.users.find_one({'_id': ObjectId(complaint['submitted_by'])})
        assigned_to = None
        if complaint.get('assigned_to'):
            assigned_to = db.users.find_one({'_id': ObjectId(complaint['assigned_to'])})
        
        # Debug: Print image information
        print(f"🔍 Viewing complaint: {complaint_id}")
        print(f"📸 Images found: {complaint.get('images', [])}")
        
        return render_template('view_complaint.html', 
                             complaint=complaint,
                             submitted_by=submitted_by,
                             assigned_to=assigned_to)
    except Exception as e:
        print(f"Error viewing complaint: {e}")
        flash('Error loading complaint', 'danger')
        return redirect(url_for('index'))

@app.route('/complaint/<complaint_id>/vote', methods=['POST'])
@login_required
def vote_complaint(complaint_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can vote'}), 403
    
    try:
        complaint = db.complaints.find_one({'_id': ObjectId(complaint_id)})
        
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        if current_user.id in complaint.get('votes', []):
            # Remove vote
            db.complaints.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$pull': {'votes': current_user.id},
                    '$inc': {'vote_count': -1}
                }
            )
            voted = False
        else:
            # Add vote
            db.complaints.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$push': {'votes': current_user.id},
                    '$inc': {'vote_count': 1}
                }
            )
            voted = True
        
        updated = db.complaints.find_one({'_id': ObjectId(complaint_id)})
        
        return jsonify({
            'success': True,
            'voted': voted,
            'vote_count': updated.get('vote_count', 0)
        })
        
    except Exception as e:
        print(f"Vote error: {e}")
        return jsonify({'error': 'Error processing vote'}), 500

# Staff Routes
@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Debug: Print current staff info
        print(f"🔍 Staff Dashboard for: {current_user.username} (ID: {current_user.id})")
        print(f"🔍 Department: {current_user.department}")
        
        # Find complaints assigned to this staff member
        complaints = list(db.complaints.find({
            'assigned_to': current_user.id
        }).sort('created_at', -1))
        
        print(f"📊 Found {len(complaints)} assigned complaints")
        
        # Debug: Print each complaint's images
        for complaint in complaints:
            print(f"   Complaint: {complaint['title']}")
            print(f"   Images: {complaint.get('images', [])}")
        
        # Calculate statistics
        stats = {
            'assigned': len(complaints),
            'pending': db.complaints.count_documents({
                'assigned_to': current_user.id,
                'status': {'$in': ['submitted', 'under_review']}
            }),
            'resolved': db.complaints.count_documents({
                'assigned_to': current_user.id,
                'status': 'resolved'
            })
        }
        
        # Category distribution for chart
        category_wise = {}
        for complaint in complaints:
            cat = complaint['category']
            category_wise[cat] = category_wise.get(cat, 0) + 1
        
    except Exception as e:
        print(f"❌ Staff dashboard error: {e}")
        complaints = []
        stats = {'assigned': 0, 'pending': 0, 'resolved': 0}
        category_wise = {}
    
    return render_template('staff_dashboard.html', 
                         complaints=complaints, 
                         stats=stats, 
                         category_wise=category_wise)

# MISSING ROUTE ADDED HERE - manage_complaints
@app.route('/staff/complaints')
@login_required
def manage_complaints():
    if current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    status = request.args.get('status', 'all')
    query = {'assigned_to': current_user.id}
    
    if status != 'all':
        query['status'] = status
    
    try:
        complaints = list(db.complaints.find(query).sort('created_at', -1))
        print(f"📊 Found {len(complaints)} complaints for staff {current_user.username}")
    except Exception as e:
        print(f"❌ Error fetching complaints: {e}")
        complaints = []
    
    return render_template('manage_complaints.html', complaints=complaints, current_filter=status)

@app.route('/staff/complaint/<complaint_id>/update', methods=['POST'])
@login_required
def update_complaint_status(complaint_id):
    if current_user.role != 'staff':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    status = request.form.get('status')
    note = request.form.get('note')
    
    if not status or not note:
        flash('Please provide status and note', 'danger')
        return redirect(url_for('view_complaint', complaint_id=complaint_id))
    
    try:
        # Verify assignment
        complaint = db.complaints.find_one({
            '_id': ObjectId(complaint_id),
            'assigned_to': current_user.id
        })
        
        if not complaint:
            flash('Complaint not found or not assigned to you', 'danger')
            return redirect(url_for('manage_complaints'))
        
        timeline_entry = {
            'status': status,
            'timestamp': datetime.utcnow(),
            'note': note,
            'updated_by': current_user.username
        }
        
        result = db.complaints.update_one(
            {'_id': ObjectId(complaint_id)},
            {
                '$set': {
                    'status': status,
                    'updated_at': datetime.utcnow()
                },
                '$push': {'timeline': timeline_entry}
            }
        )
        
        if result.modified_count > 0:
            flash('Complaint status updated successfully', 'success')
            print(f"✅ Complaint {complaint_id} status updated to {status}")
        else:
            flash('Error updating complaint status', 'danger')
            
    except Exception as e:
        print(f"❌ Update error: {e}")
        flash('Error updating complaint', 'danger')
    
    return redirect(url_for('view_complaint', complaint_id=complaint_id))

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    try:
        stats = {
            'total_users': db.users.count_documents({}),
            'total_complaints': db.complaints.count_documents({}),
            'pending_complaints': db.complaints.count_documents({
                'status': {'$in': ['submitted', 'under_review']}
            }),
            'resolved_complaints': db.complaints.count_documents({'status': 'resolved'}),
            'students': db.users.count_documents({'role': 'student'}),
            'staff': db.users.count_documents({'role': 'staff'})
        }
        
        recent = list(db.complaints.find().sort('created_at', -1).limit(10))
        
        category_stats = {}
        for complaint in db.complaints.find():
            cat = complaint['category']
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        stats = {}
        recent = []
        category_stats = {}
    
    return render_template('admin_dashboard.html', stats=stats, recent=recent, category_stats=category_stats)

@app.route('/admin/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    role = request.args.get('role', 'all')
    query = {}
    
    if role != 'all':
        query['role'] = role
    
    try:
        users = list(db.users.find(query))
    except Exception as e:
        print(f"Error fetching users: {e}")
        users = []
    
    return render_template('admin_manage_users.html', users=users, current_filter=role)

@app.route('/admin/user/<user_id>/update', methods=['POST'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    role = request.form.get('role')
    department = request.form.get('department')
    
    try:
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'role': role,
                    'department': department
                }
            }
        )
        flash('User updated successfully', 'success')
    except Exception as e:
        print(f"Update error: {e}")
        flash('Error updating user', 'danger')
    
    return redirect(url_for('manage_users'))

@app.route('/admin/user/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    if user_id == current_user.id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('manage_users'))
    
    try:
        db.users.delete_one({'_id': ObjectId(user_id)})
        flash('User deleted successfully', 'success')
    except Exception as e:
        print(f"Delete error: {e}")
        flash('Error deleting user', 'danger')
    
    return redirect(url_for('manage_users'))

# Debug Routes
@app.route('/debug/assignments')
@login_required
def debug_assignments():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    debug_info = []
    
    # Check all staff
    staff_members = list(db.users.find({'role': 'staff'}))
    debug_info.append(f"📊 Total Staff: {len(staff_members)}")
    
    for staff in staff_members:
        complaints = list(db.complaints.find({'assigned_to': str(staff['_id'])}))
        debug_info.append(f"\n👤 Staff: {staff['username']}")
        debug_info.append(f"   Department: {staff['department']}")
        debug_info.append(f"   Email: {staff['email']}")
        debug_info.append(f"   Assigned Complaints: {len(complaints)}")
        
        for complaint in complaints:
            debug_info.append(f"   - {complaint['title']} ({complaint['status']})")
    
    # Check unassigned complaints
    unassigned = list(db.complaints.find({'assigned_to': None}))
    debug_info.append(f"\n⚠️ Unassigned Complaints: {len(unassigned)}")
    
    return '<pre>' + '\n'.join(debug_info) + '</pre>'

@app.route('/debug/routes')
@login_required
def debug_routes():
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'url': str(rule)
        })
    
    # Sort by endpoint
    routes.sort(key=lambda x: x['endpoint'])
    
    html = '<h2>Registered Routes</h2>'
    html += '<table border="1" cellpadding="5">'
    html += '<tr><th>Endpoint</th><th>URL</th><th>Methods</th></tr>'
    
    for route in routes:
        html += f'<tr>'
        html += f'<td>{route["endpoint"]}</td>'
        html += f'<td>{route["url"]}</td>'
        html += f'<td>{", ".join(route["methods"])}</td>'
        html += f'</tr>'
    
    html += '</table>'
    
    return html

# API Routes
@app.route('/api/complaints/trending')
def api_trending_complaints():
    try:
        complaints = list(db.complaints.find().sort('vote_count', -1).limit(5))
        
        for complaint in complaints:
            complaint['_id'] = str(complaint['_id'])
            complaint['created_at'] = complaint['created_at'].isoformat() if complaint.get('created_at') else None
        
        return jsonify(complaints)
    except Exception as e:
        print(f"API error: {e}")
        return jsonify([])

@app.route('/api/stats')
def api_stats():
    try:
        stats = {
            'total': db.complaints.count_documents({}),
            'resolved': db.complaints.count_documents({'status': 'resolved'}),
            'pending': db.complaints.count_documents({'status': {'$in': ['submitted', 'under_review', 'work_in_progress']}}),
            'users': db.users.count_documents({})
        }
        return jsonify(stats)
    except Exception as e:
        print(f"API error: {e}")
        return jsonify({'total': 0, 'resolved': 0, 'pending': 0, 'users': 0})

@app.route("/verify/<token>")
def verify_email(token):
    try:
        # Decode token and get email
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
    except:
        return "<h1 style='color:red; font-size:24px; text-align:center;'>The verification link is invalid or expired.</h1>"

    print("Verification request received for:", email)

    # Mark user as verified in the database
    try:
        db.users.update_one(
            {"email": email},
            {"$set": {"verified": True}}
        )
    except Exception as e:
        print("Error updating user verification:", e)
        return "<h1 style='color:red; font-size:24px; text-align:center;'>Error verifying email. Please try again later.</h1>"

    # Success message
    return "<h1 style='color:black; font-size:24px; text-align:center;'>Email verified successfully! You can now login.</h1>"

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)