from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging
import sys

# Configure logging to output to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

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
        if not request.form.get('emails'):
            return jsonify({'error': 'Recipient emails are required'}), 400
            
        emails = request.form.get('emails').split(',')
        emails = [email.strip() for email in emails if email.strip()]
        
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
    app.run(debug=True)
