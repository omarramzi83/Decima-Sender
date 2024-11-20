from flask import Flask, render_template, request, jsonify
import os
import sys
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging
import webbrowser
from threading import Timer
import json

# Configure logging to output to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_base_path():
    """Get the base path for the application, works both for development and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.jinja_env.variable_start_string = '{[{'
app.jinja_env.variable_end_string = '}]}'
base_path = get_base_path()
app.config['UPLOAD_FOLDER'] = os.path.join(base_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['EMAIL_LISTS_FILE'] = os.path.join(base_path, 'email_lists.json')

# Ensure required folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def load_email_lists():
    """Load email lists from JSON file"""
    try:
        if os.path.exists(app.config['EMAIL_LISTS_FILE']):
            with open(app.config['EMAIL_LISTS_FILE'], 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading email lists: {str(e)}")
        return {}

def save_email_lists(lists):
    """Save email lists to JSON file"""
    try:
        with open(app.config['EMAIL_LISTS_FILE'], 'w') as f:
            json.dump(lists, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving email lists: {str(e)}")
        return False

def open_browser():
    """Open the browser after the server starts"""
    webbrowser.open('http://127.0.0.1:5000/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/email-lists', methods=['GET'])
def get_email_lists():
    """Get all email lists"""
    lists = load_email_lists()
    return jsonify(lists)

@app.route('/api/email-lists', methods=['POST'])
def create_email_list():
    """Create or update an email list"""
    try:
        data = request.get_json()
        list_name = data.get('name')
        emails = data.get('emails', [])
        
        if not list_name:
            return jsonify({'error': 'List name is required'}), 400
            
        lists = load_email_lists()
        lists[list_name] = emails
        
        if save_email_lists(lists):
            return jsonify({'message': f'Email list "{list_name}" saved successfully'})
        else:
            return jsonify({'error': 'Failed to save email list'}), 500
            
    except Exception as e:
        logger.error(f"Error creating email list: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/email-lists/<string:name>', methods=['DELETE'])
def delete_email_list(name):
    """Delete an email list"""
    try:
        lists = load_email_lists()
        if name in lists:
            del lists[name]
            if save_email_lists(lists):
                return jsonify({'message': f'Email list "{name}" deleted successfully'})
            else:
                return jsonify({'error': 'Failed to save changes'}), 500
        else:
            return jsonify({'error': 'List not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting email list: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/send_emails', methods=['POST'])
def send_emails():
    try:
        # Log all form data for debugging
        logger.info("Form data received:")
        for key, value in request.form.items():
            logger.info(f"{key}: {value}")
        
        # Log files data
        logger.info("Files received:")
        for key, file in request.files.items():
            logger.info(f"{key}: {file.filename}")

        # Get Gmail credentials from the form
        smtp_username = request.form.get('gmail')
        smtp_password = request.form.get('app_password')
        
        if not smtp_username or not smtp_password:
            return jsonify({'error': 'Gmail credentials are required'}), 400

        # Validate email format
        if '@' not in smtp_username:
            return jsonify({'error': 'Invalid Gmail address format'}), 400

        # Get and validate other form data
        emails_input = request.form.get('emails')
        selected_list = request.form.get('selectedList')
        
        # Get emails from either direct input or selected list
        if selected_list:
            lists = load_email_lists()
            emails = lists.get(selected_list, [])
            if not emails:
                return jsonify({'error': f'Selected list "{selected_list}" is empty or not found'}), 400
        else:
            if not emails_input:
                return jsonify({'error': 'Recipient emails are required'}), 400
            emails = [email.strip() for email in emails_input.split(',') if email.strip()]
        
        if not emails:
            return jsonify({'error': 'No valid recipient emails provided'}), 400

        subject = request.form.get('subject', '')
        message = request.form.get('message', '')
        
        # Check for file
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Save file with secure filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"File saved as: {filepath}")
        
        # Gmail SMTP settings
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        
        # Create and send email
        for email in emails:
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = email
                msg['Subject'] = subject
                
                # Add message body
                msg.attach(MIMEText(message, 'plain'))
                
                # Add attachment
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        part = MIMEApplication(f.read(), _subtype=os.path.splitext(filename)[1][1:])
                        part.add_header('Content-Disposition', 'attachment', filename=filename)
                        msg.attach(part)
                else:
                    logger.error(f"File not found: {filepath}")
                    return jsonify({'error': 'File upload failed'}), 500
                
                # Send email
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
                    logger.info(f"Email sent to: {email}")
            
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication Error: {str(e)}")
                return jsonify({'error': 'Gmail authentication failed. Please check your email and app password.'}), 401
            except Exception as e:
                logger.error(f"Error sending to {email}: {str(e)}")
                return jsonify({'error': f"Failed to send email to {email}: {str(e)}"}), 500
        
        # Clean up
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info("Temporary file removed")
        except Exception as e:
            logger.error(f"Error removing temporary file: {str(e)}")
        
        return jsonify({'message': 'Emails sent successfully!'})
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        # Log the full error traceback
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Open browser after server starts
    Timer(1.5, open_browser).start()
    # Run the server
    app.run(debug=False)
