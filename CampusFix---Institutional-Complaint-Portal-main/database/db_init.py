from pymongo import MongoClient, ASCENDING
from config import Config
import bcrypt

def init_db():
    client = MongoClient(Config.MONGO_URI)
    db = client.get_default_database()
    
    # Create collections if they don't exist
    collections = ['users', 'complaints', 'categories']
    for collection in collections:
        if collection not in db.list_collection_names():
            db.create_collection(collection)
    
    # Create indexes
    db.users.create_index('email', unique=True)
    db.users.create_index('username', unique=True)
    db.complaints.create_index([('created_at', ASCENDING)])
    db.complaints.create_index('category')
    db.complaints.create_index('status')
    
    # Create default admin if not exists
    if db.users.count_documents({'role': 'admin'}) == 0:
        admin_data = {
            'username': 'admin',
            'email': 'admin@campusfix.com',
            'password': bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()),
            'role': 'admin',
            'department': 'Administration'
        }
        db.users.insert_one(admin_data)
        print("Default admin created - Email: admin@campusfix.com, Password: admin123")
    
    print("Database initialized successfully")
    return db

if __name__ == '__main__':
    init_db()