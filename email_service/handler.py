import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        to_email = body.get('email')
        name = body.get('name', 'User')

        if not action or not to_email:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Missing 'action' or 'email' in payload."})
            }

        # Define email content based on action
        if action == "SIGNUP_WELCOME":
            subject = "Welcome to MediCore!"
            html_content = f"<h3>Hello {name},</h3><p>Welcome to MediCore. We are thrilled to have you onboard.</p>"
        elif action == "BOOKING_CONFIRMATION":
            doctor = body.get('doctor_name', '')
            datetime = body.get('datetime', '')
            subject = "Appointment Confirmed"
            html_content = f"<h3>Hello {name},</h3><p>Your appointment with Dr. {doctor} on {datetime} has been confirmed.</p>"
        elif action == "DOCTOR_NOTIFICATION":
            patient = body.get('patient_name', '')
            datetime = body.get('datetime', '')
            subject = "New Appointment Scheduled"
            html_content = f"<h3>Hello Dr. {name},</h3><p>You have a new appointment with <b>{patient}</b> on {datetime}.</p>"
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Unknown action."})
            }

        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')

        # Only simulate if credentials are not set
        if not smtp_user or smtp_user == "your-email@gmail.com":
            print(f"SIMULATED EMAIL TO {to_email}: {subject}")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Email simulation successful (update SMTP creds for real delivery)."})
            }

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Email sent successfully."})
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal Server Error", "error": str(e)})
        }
