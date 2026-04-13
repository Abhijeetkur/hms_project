# Hospital Management System (HMS)

A complete full-stack web application designed to streamline hospital operations, appointment scheduling, and patient-doctor communications. Built using Django for the core backend/frontend and AWS Lambda for scalable, automated microservices.

## Features

- **Robust Dashboards**: Dedicated portal views for both Doctors and Patients.
- **Appointment Management**: Seamless scheduling system.
- **Google Calendar Integration**: Automatically synchronizes patient appointments directly to Google Calendar.
- **Automated Email Notifications**: Triggered alerts for bookings and updates handled asynchronously by an AWS Serverless (Lambda) microservice.
- **Google OAuth**: Secure and quick login/signup process for doctors.

## Project Architecture

The repository is configured as a monorepo consisting of:
- `hms/`: The main Django monolithic application.
- `email_service/`: A Serverless framework project containing the AWS Lambda functions used for email delivery.

## Local Setup

### Prerequisites
- **Python 3.x**
- **Node.js & npm** (for deploying the email service)
- **Serverless Framework** (`npm install -g serverless`)
- **Google Cloud Console Credentials**: You must configure OAuth 2.0 Client IDs to enable Google Calendar/Login features.

### 1. Django Web Application Setup

1. Navigate to the Django directory:
   ```bash
   cd hms
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure all dependencies like Django, google-api-python-client, etc., are installed)*
4. Set up the Database:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. **Configure Google Credentials**: 
   Place your Google OAuth Client Secret JSON file in the `hms/` directory. (e.g. `client_secret_<your_identifier>.apps.googleusercontent.com.json`). 
   > *Note: This file is ignored by git for security purposes.*
6. Run the local development server:
   ```bash
   python manage.py runserver
   ```

### 2. AWS Serverless Email Service Setup

The email microservice runs on AWS Lambda to ensure reliable, non-blocking notifications.

1. Navigate to the microservice directory:
   ```bash
   cd email_service
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Deploy to AWS:
   Make sure your AWS CLI is configured (`aws configure`), then run:
   ```bash
   serverless deploy
   ```

## License
MIT
