"""
Quick test for the email service handler.
Run: python test_handler.py
"""
import os
import json

# Set environment variables (same as serverless.yml)
os.environ['SMTP_HOST'] = 'smtp.gmail.com'
os.environ['SMTP_PORT'] = '587'
os.environ['SMTP_USER'] = 'ak9111709@gmail.com'
os.environ['SMTP_PASSWORD'] = 'sdqb sgon kuys oxpt'

from handler import send_email

# Test 1: Welcome Email
print("=" * 50)
print("TEST 1: SIGNUP_WELCOME email")
print("=" * 50)
result = send_email({
    'body': json.dumps({
        'action': 'SIGNUP_WELCOME',
        'email': 'abhijeetkur025@gmail.com',   # <-- sends to yourself for testing
        'name': 'Abhijeet'
    })
}, None)
print(f"Status: {result['statusCode']}")
print(f"Response: {result['body']}")

print()

# Test 2: Booking Confirmation
print("=" * 50)
print("TEST 2: BOOKING_CONFIRMATION email")
print("=" * 50)
result = send_email({
    'body': json.dumps({
        'action': 'BOOKING_CONFIRMATION',
        'email': 'abhijeetkur025@gmail.com',   # <-- sends to yourself for testing
        'name': 'Abhijeet',
        'doctor_name': 'Sarah Jenkins',
        'datetime': '2026-04-13 at 10:00'
    })
}, None)
print(f"Status: {result['statusCode']}")
print(f"Response: {result['body']}")
