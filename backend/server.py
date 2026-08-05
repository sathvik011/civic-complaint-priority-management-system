from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from models import SessionLocal, Complaint, User, create_tables
import datetime
import uuid
import sys
import json

# Load environment variables from .env file
load_dotenv()

from priority_classifier import (
    get_priority_hybrid,
    get_location_density,
    get_priority_score,
    load_or_train_model,
    calculate_final_priority,
    get_department_groq,
)

# Create database tables
create_tables()

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080", "https://civic-complaint-priority-management.vercel.app/"])

# No ML models needed - using Groq only
print("🚀 Using Groq LLM for classification (no ML models required)")


@app.route("/")
def home():
    return "Civic Complaint System Backend"


# ── Citizen Signup ─────────────────────────────────────────────────────────────
@app.route("/api/signup", methods=["POST"])
def signup():
    db = SessionLocal()
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if db.query(User).filter(User.email == email).first():
            return jsonify({"error": "User with this email already exists."}), 409

        new_user = User(name=name, email=email, password=password, role="citizen")
        db.add(new_user)
        db.commit()
        return jsonify({"message": "User created successfully", "user_id": new_user.id}), 201
    finally:
        db.close()


# ── Citizen / Admin Login ───────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    db = SessionLocal()
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        username = data.get("username")

        user = None
        if email:
            user = db.query(User).filter(User.email == email, User.password == password).first()
        elif username:
            user = db.query(User).filter(User.name == username, User.password == password).first()

        if user:
            return jsonify({
                "message": "Login successful",
                "user_id": user.id,
                "role": user.role,
                "name": user.name,
                "department": user.department,
            }), 200
        return jsonify({"error": "Invalid credentials"}), 401
    finally:
        db.close()


# ── Submit New Complaint ────────────────────────────────────────────────────────
@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    db = SessionLocal()
    try:
        data = request.get_json()
        title       = data.get("title")
        description = data.get("description")
        location    = data.get("location")
        user_id     = data.get("user_id")
        lat         = data.get("lat")
        lon         = data.get("lon")
        # Images: list of base64 data-URL strings sent from the frontend
        images      = data.get("images", [])  # [] if none uploaded
        # Videos: list of base64 data-URL strings sent from the frontend
        videos      = data.get("videos", [])  # [] if none uploaded

        # 1. Classify department with Groq LLM
        department, _ = get_department_groq(description)

        # 2. Assign priority with Groq
        priority_level_desc, _ = get_priority_hybrid(description)

        # 3. Location density → final priority
        location_type = None
        final_priority = None
        if lat and lon:
            location_type  = get_location_density(lat, lon)
            final_priority = calculate_final_priority(priority_level_desc, location_type)
        else:
            p_score, _ = get_priority_score(priority_level_desc, "Low")
            if p_score >= 2.5:
                final_priority = "1"
            elif p_score >= 1.5:
                final_priority = "2"
            else:
                final_priority = "3"

        complaint_id = str(uuid.uuid4())

        new_complaint = Complaint(
            id=complaint_id,
            title=title,
            description=description,
            location=location,
            department=department,
            priority=final_priority,
            location_type=location_type,
            citizen_id=user_id,
            status="Registered",
            # Store images list as a JSON string in the DB column
            images=json.dumps(images) if images else json.dumps([]),
            videos=json.dumps(videos) if videos else json.dumps([]),
        )
        db.add(new_complaint)
        db.commit()

        return jsonify({
            "message": "Complaint submitted successfully",
            "complaint": {
                "id": new_complaint.id,
                "title": new_complaint.title,
                "description": new_complaint.description,
                "location": new_complaint.location,
                "department": new_complaint.department,
                "priority": new_complaint.priority,
                "location_type": new_complaint.location_type,
                "status": new_complaint.status,
                "registered": new_complaint.registered.isoformat(),
                "images": images,
                "videos": videos,
                "user_id": new_complaint.citizen_id,
            },
        }), 201

    except Exception as e:
        db.rollback()
        print(f"Error creating complaint: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ── Get Complaints for a User ───────────────────────────────────────────────────
@app.route("/api/complaints/user/<int:user_id>", methods=["GET"])
def get_user_complaints(user_id):
    db = SessionLocal()
    try:
        complaints = db.query(Complaint).filter(Complaint.citizen_id == user_id).all()
        result = []
        for c in complaints:
            result.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "location": c.location,
                "department": c.department,
                "status": c.status,
                "priority": c.priority,
                "location_type": c.location_type,
                "registered": c.registered.isoformat(),
                "resolved": c.resolved.isoformat() if c.resolved else None,
                "images": json.loads(c.images) if c.images else [],
                "videos": json.loads(c.videos) if c.videos else [],
            })
        return jsonify(result), 200
    finally:
        db.close()


# ── Get All Complaints (Admin) ──────────────────────────────────────────────────
@app.route("/api/complaints", methods=["GET"])
def get_all_complaints():
    db = SessionLocal()
    try:
        complaints = db.query(Complaint).all()
        result = []
        for c in complaints:
            citizen_email = db.query(User.email).filter(User.id == c.citizen_id).scalar()
            result.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "location": c.location,
                "department": c.department,
                "status": c.status,
                "priority": c.priority,
                "location_type": c.location_type,
                "registered": c.registered.isoformat(),
                "resolved": c.resolved.isoformat() if c.resolved else None,
                "citizen_email": citizen_email,
                "images": json.loads(c.images) if c.images else [],
                "videos": json.loads(c.videos) if c.videos else [],
            })
        return jsonify(result), 200
    finally:
        db.close()


# ── Update Complaint Status ─────────────────────────────────────────────────────
@app.route("/api/complaints/<string:complaint_id>", methods=["PUT"])
def update_complaint(complaint_id):
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        data = request.get_json()
        new_status = data.get("status")
        complaint.status = new_status
        if new_status == "Resolved":
            complaint.resolved = datetime.datetime.now()

        db.commit()
        return jsonify({"message": "Complaint updated successfully"}), 200
    finally:
        db.close()


# ── Delete Complaint ────────────────────────────────────────────────────────────
@app.route("/api/complaints/<string:complaint_id>", methods=["DELETE"])
def delete_complaint(complaint_id):
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return jsonify({"error": "Complaint not found"}), 404

        db.delete(complaint)
        db.commit()
        return jsonify({"message": "Complaint deleted successfully"}), 200
    finally:
        db.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
