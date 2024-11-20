# Decima Sender

A modern web application that allows you to send files to multiple email recipients simultaneously using your Gmail account.

## Features

- Send files to multiple email addresses at once
- Modern and responsive UI using Tailwind CSS
- Secure file handling with automatic cleanup
- Support for email attachments up to 16MB
- Status notifications for successful sends and errors
- Gmail integration with App Password support

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Gmail Configuration:
   1. Enable 2-Step Verification in your Google Account:
      - Go to [Google Account Security](https://myaccount.google.com/security)
      - Enable "2-Step Verification"
   
   2. Generate an App Password:
      - Go to [App Passwords](https://myaccount.google.com/apppasswords)
      - Select "Mail" and your device type
      - Click "Generate"
      - Copy the 16-character password

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter your Gmail credentials:
   - Your Gmail address
   - The App Password you generated

2. Fill in the email details:
   - Recipient email addresses (comma-separated)
   - Subject
   - Message

3. Attach your file (max 16MB)

4. Click "Send Emails" to send the file to all recipients

## Security Notes

- Files are temporarily stored and immediately deleted after sending
- Maximum file size is limited to 16MB
- All file names are sanitized before processing
- Gmail credentials are only used for the current session and not stored
- Uses secure SMTP with TLS encryption

## Troubleshooting

If you encounter any issues:

1. Make sure 2-Step Verification is enabled on your Google Account
2. Verify you're using the correct App Password
3. Check that your Gmail address is entered correctly
4. Ensure recipient email addresses are properly comma-separated
5. Check the file size is under 16MB

## Development

The project structure is organized as follows:
```
Decima Sender/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── uploads/           # Temporary file storage
└── templates/
    └── index.html     # Frontend UI template
```
