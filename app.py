from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import logging
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["*", "https://*.onrender.com"])

# Database configuration
DATABASE = 'applications.db'

# Email configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
ADMIN_EMAIL = EMAIL_ADDRESS

# Valid languages and availability
VALID_LANGUAGES = ['English', 'Spanish', 'French', 'German', 'Chinese', 'Arabic', 'Portuguese', 'Russian', 'Japanese', 'Korean']
VALID_AVAILABILITY = ['Day', 'Night', 'Both']

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and ensure it has the correct structure."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create applications table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            experience_level TEXT,
            language TEXT,
            availability TEXT,
            motivation TEXT CHECK(length(motivation) <= 500),
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create admins table for admin users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add status column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN status TEXT DEFAULT 'pending';")
        logger.info("Added status column to existing applications table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("Status column already exists")
        else:
            logger.error(f"Error adding status column: {e}")
    
    # Insert default admin user if it doesn't exist
    default_email = "admin@work4u.com"
    default_password = "admin123"
    
    cursor.execute("SELECT COUNT(*) FROM admins WHERE email = ?", (default_email,))
    if cursor.fetchone()[0] == 0:
        hashed_pw = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO admins (username, email, password_hash) 
            VALUES (?, ?, ?)
        ''', ("admin", default_email, hashed_pw))
        logger.info(f"Created default admin user: {default_email}")
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def send_email(to_email, subject, body):
    """Send email using SMTP configuration."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.warning("Email credentials not configured. Skipping email sending.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = "Work4U <" + EMAIL_ADDRESS + ">"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        
        logger.info(f"Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_confirmation_email(first_name, last_name, email):
    body = f"""Hi {first_name} {last_name},

We are delighted to let you know that we have successfully received your application. Thank you for showing interest in joining our team. We truly value the time and effort you put into applying.

Our recruitment team will carefully review your details and get back to you within 3 days.

If you find this email in your spam or promotions folder, kindly mark it as "Not Spam" so you won't miss our updates.

We look forward to the possibility of working together.

Best regards,
Work4U Recruitment Team"""

    return send_email(email, "Thank you for applying with us", body)

def send_admin_notification(first_name, last_name, applicant_email, language, created_at):
    formatted_datetime = created_at.strftime("%B %d, %Y at %I:%M %p")
    
    body = f"""Hello Admin,

A new application has just been submitted. Here are the applicant's details:

Full Name: {first_name} {last_name}
Email Address: {applicant_email}
Language Applied For: {language}
Date Submitted: {formatted_datetime}

Please log in to the dashboard for full application details.

Best regards,
Work4U Recruitment System"""

    return send_email(ADMIN_EMAIL, "New Application Received", body)

def send_approval_email(first_name, last_name, email):
    body = f"""Hi {first_name} {last_name},

Congratulations! Your application has been approved. Welcome to Work4U!

We are excited to have you join our team of dedicated professionals. Our team will be in touch shortly with next steps regarding onboarding and training.

Thank you for your interest in Work4U.

Best regards,
Work4U Recruitment Team"""

    return send_email(email, "Congratulations! Your Application Has Been Approved", body)

def send_rejection_email(first_name, last_name, email):
    body = f"""Hi {first_name} {last_name},

Thank you for your application and interest in joining Work4U.

After careful consideration, we regret to inform you that we cannot proceed with your application at this time. We appreciate the time and effort you invested in your application.

We encourage you to apply for future opportunities with us.

Best regards,
Work4U Recruitment Team"""

    return send_email(email, "Regarding Your Application", body)

# ✅ SERVE PUBLIC HIRING WEBSITE AT ROOT
@app.route('/')
def serve_public_site():
    return send_from_directory('.', 'index.html')

# ✅ SERVE ADMIN DASHBOARD AT /admin
@app.route('/admin')
def serve_admin_dashboard():
    return send_from_directory('.', 'admin.html')

# --- PASSWORD CHANGE ENDPOINT ---
@app.route('/change-password', methods=['POST'])
def change_password():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        confirm_password = data.get('confirmPassword')
        admin_email = data.get('email', 'admin@work4u.com')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({"status": "error", "message": "All password fields are required"}), 400
            
        if new_password != confirm_password:
            return jsonify({"status": "error", "message": "New password and confirmation do not match"}), 400
            
        if len(new_password) < 6:
            return jsonify({"status": "error", "message": "New password must be at least 6 characters long"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM admins WHERE email = ?', (admin_email,))
        admin_record = cursor.fetchone()
        
        if not admin_record:
            conn.close()
            return jsonify({"status": "error", "message": "Invalid current password"}), 401

        stored_hash = admin_record['password_hash']
        admin_id = admin_record['id']
        
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash):
            conn.close()
            return jsonify({"status": "error", "message": "Invalid current password"}), 401
            
        new_hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('UPDATE admins SET password_hash = ? WHERE id = ?', (new_hashed_pw, admin_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Password changed successfully for admin ID {admin_id}")
        return jsonify({"status": "success", "message": "Password updated successfully"})
        
    except Exception as e:
        logger.error(f"Unexpected error during password change: {str(e)}")
        return jsonify({"status": "error", "message": "An unexpected error occurred"}), 500

@app.route('/apply', methods=['POST'])
def submit_application():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        required_fields = ['first_name', 'last_name', 'email', 'experience_level', 'language', 'availability']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
        
        if data['experience_level'] not in ['Yes', 'No']:
            return jsonify({"status": "error", "message": "Experience level must be 'Yes' or 'No'"}), 400
        
        if data['language'] not in VALID_LANGUAGES:
            return jsonify({"status": "error", "message": "Invalid language selection"}), 400
        
        if data['availability'] not in VALID_AVAILABILITY:
            return jsonify({"status": "error", "message": "Availability must be 'Day', 'Night', or 'Both'"}), 400
        
        if '@' not in data['email']:
            return jsonify({"status": "error", "message": "Invalid email format"}), 400
        
        motivation = str(data.get('motivation', ''))[:500] if data.get('motivation') else ''
        current_time = datetime.now()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applications 
            (first_name, last_name, email, experience_level, language, availability, motivation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(data['first_name']).strip(),
            str(data['last_name']).strip(),
            str(data['email']).strip(),
            str(data['experience_level']).strip(),
            str(data['language']).strip(),
            str(data['availability']).strip(),
            motivation,
            current_time
        ))
        
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        send_confirmation_email(data['first_name'], data['last_name'], data['email'])
        send_admin_notification(data['first_name'], data['last_name'], data['email'], data['language'], current_time)
        logger.info(f"Application submitted for {data['first_name']} {data['last_name']} ({data['email']})")
        return jsonify({"status": "success", "message": "Submitted"})
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"status": "error", "message": "An unexpected error occurred"}), 500

@app.route('/applications', methods=['GET'])
def get_applications():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications ORDER BY created_at DESC')
        applications = cursor.fetchall()
        applications_list = []
        for app in applications:
            app_dict = {
                'id': app['id'],
                'first_name': app['first_name'],
                'last_name': app['last_name'],
                'email': app['email'],
                'experience_level': app['experience_level'],
                'language': app['language'],
                'availability': app['availability'],
                'motivation': app['motivation'],
                'status': app['status'],
                'created_at': app['created_at']
            }
            applications_list.append(app_dict)
        conn.close()
        return jsonify(applications_list)
    except Exception as e:
        logger.error(f"Error fetching applications: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to retrieve applications: {str(e)}"}), 500

@app.route('/applications/<int:app_id>/approve', methods=['POST'])
def approve_application(app_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE id = ?', (app_id,))
        app = cursor.fetchone()
        if not app:
            conn.close()
            return jsonify({"status": "error", "message": "Application not found"}), 404
        first_name = app['first_name']
        last_name = app['last_name']
        email = app['email']
        cursor.execute('UPDATE applications SET status = ? WHERE id = ?', ('approved', app_id))
        conn.commit()
        conn.close()
        send_approval_email(first_name, last_name, email)
        logger.info(f"Application {app_id} approved for {first_name} {last_name}")
        return jsonify({"status": "success", "message": "Application approved and email sent"})
    except Exception as e:
        logger.error(f"Error approving application: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to approve application: {str(e)}"}), 500

@app.route('/applications/<int:app_id>/reject', methods=['POST'])
def reject_application(app_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications WHERE id = ?', (app_id,))
        app = cursor.fetchone()
        if not app:
            conn.close()
            return jsonify({"status": "error", "message": "Application not found"}), 404
        first_name = app['first_name']
        last_name = app['last_name']
        email = app['email']
        cursor.execute('UPDATE applications SET status = ? WHERE id = ?', ('rejected', app_id))
        conn.commit()
        conn.close()
        send_rejection_email(first_name, last_name, email)
        logger.info(f"Application {app_id} rejected for {first_name} {last_name}")
        return jsonify({"status": "success", "message": "Application rejected and email sent"})
    except Exception as e:
        logger.error(f"Error rejecting application: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to reject application: {str(e)}"}), 500

if __name__ == '__main__':
    init_db()
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.warning("Email credentials not set. Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)