from flask import Flask, render_template, request, jsonify
import os
import sys
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
import logging
import webbrowser
from threading import Timer
import json
import copy

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

@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    """Send emails to the selected list"""
    try:
        data = request.get_json()
        gmail = data.get('gmail')
        app_password = data.get('appPassword')
        list_name = data.get('listName')
        subject = data.get('subject')
        message = data.get('message')
        
        if not all([gmail, app_password, list_name, subject, message]):
            return jsonify({
                'error': 'Missing required fields',
                'status': 'error'
            }), 400
            
        # Load email lists
        lists = load_email_lists()
        if list_name not in lists:
            return jsonify({
                'error': f'Email list "{list_name}" not found',
                'status': 'error'
            }), 404
            
        emails = lists[list_name]
        if not emails:
            return jsonify({
                'error': 'Email list is empty',
                'status': 'error'
            }), 400

        # Connect to SMTP server
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail, app_password)
        except Exception as e:
            logger.error(f"SMTP connection error: {str(e)}")
            return jsonify({
                'error': 'Failed to connect to SMTP server. Please check your credentials.',
                'status': 'error'
            }), 500

        failed_recipients = []
        successful_count = 0

        # Send emails
        for email in emails:
            try:
                msg = MIMEMultipart()
                msg['From'] = gmail
                msg['To'] = email
                msg['Subject'] = subject

                msg.attach(MIMEText(message, 'plain'))
                
                server.send_message(msg)
                successful_count += 1
                
                # Return progress update
                response = jsonify({
                    'status': 'progress',
                    'message': f'Sent email to {email}',
                    'progress': {
                        'current': successful_count,
                        'total': len(emails),
                        'success': successful_count,
                        'failed': len(failed_recipients)
                    }
                })
                response.headers['X-Progress'] = 'true'
                yield response
                
            except Exception as e:
                logger.error(f"Failed to send to {email}: {str(e)}")
                failed_recipients.append({
                    'email': email,
                    'error': str(e)
                })

        server.quit()

        # Final response
        return jsonify({
            'message': f'Sent {successful_count} emails successfully',
            'failed_recipients': failed_recipients,
            'status': 'success' if not failed_recipients else 'partial',
            'progress': {
                'current': len(emails),
                'total': len(emails),
                'success': successful_count,
                'failed': len(failed_recipients)
            }
        })

    except Exception as e:
        logger.error(f"Error in send_emails: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    # Open browser after server starts
    Timer(1.5, open_browser).start()
    # Run the server
    app.run(debug=False)
