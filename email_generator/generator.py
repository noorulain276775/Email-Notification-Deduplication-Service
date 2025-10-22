import os
import requests
import time
import random
import json

VERIFY_URL = os.environ.get('VERIFY_URL', 'http://flask_verification:5000/webhook/email')
INTERVAL = int(os.environ.get('GEN_INTERVAL', 5))

# Imperfect: sometimes sends duplicate or malformed data
def generate_email_event():
    email_id = random.choice(['2345', '3456', '4567']) if random.random() < 0.7 else str(random.randint(10_000_000, 99_999_999))
    user = random.choice(['bob@example.com', 'alice@example.com'])
    subject = random.choice(['Your invoice', 'Password reset', 'Welcome'])
    body = 'You have a new message...'
    state = 'pending'
    if random.random() < 0.2:
        return {'email_id': email_id, 'user': user}
    return {'email_id': email_id, 'user': user, 'subject': subject, 'body': body, 'state': state}

if __name__ == '__main__':
    while True:
        data = generate_email_event()
        try:
            resp = requests.post(VERIFY_URL, json=data)
            print(f"Sent: {json.dumps(data)} | Response: {resp.status_code}")
        except Exception as e:
            print(f"Failed to send: {e}")
        time.sleep(INTERVAL)
