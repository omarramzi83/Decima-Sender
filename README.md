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

4. Click "Send Emails" to send your message

## Building the Executable

To create a Windows executable:

1. Run the build script:
```bash
python build_exe.py
```

2. Find the executable in the `dist` folder
3. Double-click `Decima-Sender.exe` to run the application

## Security Note

- Never share your Gmail App Password
- The application does not store any credentials
- All uploaded files are automatically deleted after sending
