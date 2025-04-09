from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import hashlib

app = Flask(__name__)
CORS(app)

ENTRIES_FILE = 'entries.json'
USERS_FILE = 'users.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

entries = load_json(ENTRIES_FILE)
users = load_json(USERS_FILE)

# ✅ API to get entries for the logged-in user
@app.route('/api/entries/<username>', methods=['GET'])
def get_entries(username):
    user_entries = [e for e in entries if e.get("user") == username]
    return jsonify(user_entries)

# ✅ Add entry for specific user
@app.route('/api/entries/<username>', methods=['POST'])
def add_entry(username):
    data = request.get_json()
    data["user"] = username
    entries.append(data)
    save_json(entries, ENTRIES_FILE)
    return jsonify({"message": "Entry saved"}), 201

@app.route('/api/entries/<username>/<int:index>', methods=['DELETE'])
def delete_entry(username, index):
    user_entries = [e for e in entries if e.get("user") == username]
    if 0 <= index < len(user_entries):
        full_index = entries.index(user_entries[index])
        entries.pop(full_index)
        save_json(entries, ENTRIES_FILE)
        return jsonify({"message": "Entry deleted"}), 200
    return jsonify({"error": "Invalid index"}), 400

@app.route('/api/entries/<username>/<int:index>', methods=['PUT'])
def update_entry(username, index):
    data = request.get_json()
    user_entries = [e for e in entries if e.get("user") == username]
    if 0 <= index < len(user_entries):
        full_index = entries.index(user_entries[index])
        data["user"] = username  # ensure user tag persists
        entries[full_index] = data
        save_json(entries, ENTRIES_FILE)
        return jsonify({"message": "Entry updated"}), 200
    return jsonify({"error": "Invalid index"}), 400

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = hash_password(data.get('password'))

    if any(u['username'] == username for u in users):
        return jsonify({"error": "User already exists"}), 409

    users.append({'username': username, 'password': password})
    save_json(users, USERS_FILE)
    return jsonify({"message": "User registered"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = hash_password(data.get('password'))

    for user in users:
        if user['username'] == username and user['password'] == password:
            return jsonify({"message": "Login successful"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

