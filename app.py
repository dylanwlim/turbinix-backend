from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import hashlib
import random
import string
import time
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://turbinix.one"], supports_credentials=True)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")

USERS_FILE = 'users.json'
CODES_FILE = 'codes.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

users = load_json(USERS_FILE)
codes = load_json(CODES_FILE)

@app.route('/api/check-username/<username>', methods=['GET'])
def check_username(username):
    if any(u['username'] == username for u in users):
        return jsonify({"available": False}), 200
    return jsonify({"available": True}), 200

@app.route('/api/send-code', methods=['POST'])
def send_code():
    try:
        data = request.get_json()
        email = data.get('email')
        now = time.time()

        if not email:
            return jsonify({"error": "Email required"}), 400

        for record in codes:
            if record['email'] == email and now - record['timestamp'] < 60:
                return jsonify({"error": "Please wait before requesting another code."}), 429

        code = generate_code()
        codes[:] = [c for c in codes if c['email'] != email]
        codes.append({"email": email, "code": code, "timestamp": now})
        save_json(codes, CODES_FILE)

        brevo_key = os.getenv("BREVO_API_KEY")
        print("🔍 BREVO_API_KEY loaded as:", brevo_key)

        if not brevo_key:
            print("❌ Missing Brevo API Key")
            return jsonify({"error": "Missing Brevo API Key"}), 500

        res = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": brevo_key,
                "content-type": "application/json"
            },
            json={
                "sender": {"name": "Turbinix", "email": "no-reply@turbinix.one"},
                "to": [{"email": email}],
                "subject": "Your Turbinix Verification Code",
                "htmlContent": f"""
                    <p>Hi there,</p>
                    <p>Your Turbinix verification code is: <strong>{code}</strong></p>
                    <p>This code is valid for 10 minutes.</p>
                    <p>If you didn’t request this, you can safely ignore it.</p>
                    <p>– The Turbinix Team</p>
                """
            }
        )

        print("📬 Brevo response:", res.status_code, res.text)

        if res.status_code >= 400:
            return jsonify({"error": "Failed to send email"}), 500

        return jsonify({"message": "Verification code sent!"}), 200

    except Exception as e:
        print("❌ send-code exception:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({"verified": False, "error": "Missing fields"}), 400

    for record in codes:
        if record['email'] == email and record['code'] == code:
            return jsonify({"verified": True}), 200

    return jsonify({"verified": False}), 400

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data['email']
        username = data['username']
        password = hash_password(data['password'])
        first_name = data['first_name']
        last_name = data['last_name']

        if any(u.get('username') == username for u in users):
            return jsonify({"error": "Username already taken"}), 409

        if any(u.get('email') == email for u in users):
            return jsonify({"error": "Email already used"}), 409

        users.append({
            'username': username,
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name
        })
        save_json(users, USERS_FILE)
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        print("Error in register:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        identifier = data.get('identifier')
        password = data.get('password')

        if not identifier or not password:
            return jsonify({"error": "Missing fields"}), 400

        hashed_password = hash_password(password)

        for user in users:
            if (user.get('username') == identifier or user.get('email') == identifier) and user.get('password') == hashed_password:
                return jsonify({
                    "message": "Login successful",
                    "username": user['username'],
                    "first_name": user.get('first_name', ''),
                    "last_name": user.get('last_name', '')
                }), 200

        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        print("Error in login:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/property-value', methods=['GET'])
def property_value():
    address = request.args.get('address', '').lower()

    mock_properties = {
        '123 main st': {
            'value': 542000,
            'change': '+3.2%',
            'image': 'https://source.unsplash.com/featured/400x200?house',
        },
        '456 elm st': {
            'value': 610000,
            'change': '-1.1%',
            'image': 'https://source.unsplash.com/featured/400x200?modern-home',
        }
    }

    result = mock_properties.get(address, {
        'value': 480000,
        'change': '+1.0%',
        'image': 'https://images.unsplash.com/photo-1600607687920-4ff6f5ef9c07',
    })

    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)
