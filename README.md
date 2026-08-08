# 🏛️ Civic Complaint System

An AI-powered full-stack web application that allows citizens to submit civic complaints, which are automatically classified to the correct government department using a BERT-based machine learning model. Complaints are prioritized based on description severity and location density, and managed by role-based admins through a dedicated dashboard.

---

## 📸 Features

- **ML-based Department Classification** — BERT model automatically routes complaints to the correct city department
- **Hybrid Priority Scoring** — Combines rule-based fuzzy matching and logistic regression to assign P1/P2/P3 priority, weighted with real-time location density via OpenStreetMap
- **OTP Authentication** — Two-step login with a 6-digit OTP sent to the user's mobile number via Twilio SMS
- **Photo & Video Upload** — Citizens can attach up to 5 photos and 3 videos to complaints with drag-and-drop support
- **Role-based Admin Dashboard** — Superadmin sees all complaints; department admins see only their department's complaints
- **Geolocation Support** — Citizens can auto-fill location using browser GPS
- **Status Tracking** — Complaints move through Registered → In Progress → Resolved

---

## 🗂️ Project Structure

```
temp_proj/
├── backend/
│   ├── complaint_agency_bert_classifier.joblib   # Trained BERT classifier
│   ├── complaint_priority_model.joblib           # Priority ML model
│   ├── label_encoder_bert.joblib                 # Label encoder
│   ├── server.py                                 # Flask REST API
│   ├── models.py                                 # SQLAlchemy DB models
│   ├── database.py                               # DB config (Render/PostgreSQL)
│   ├── priority_classifier.py                    # Hybrid priority logic
│   ├── create_admins.py                          # Seed admin accounts
│   ├── requirements.txt
│   ├── Dockerfile
│   └── run.sh
└── frontend/
    ├── index.html
    ├── citizen-signup.html
    ├── citizen-login.html
    ├── citizen-dashboard.html
    ├── admin-login.html
    ├── admin-dashboard.html
    ├── new-complaint.html
    ├── complaint-detail.html
    ├── contact.html
    ├── app.js                                    # All frontend logic
    ├── geo.js                                    # Geolocation helper
    └── styles.css
```

---

## 🤖 ML Models

| Model | Purpose |
|-------|---------|
| BERT + SVM (`complaint_agency_bert_classifier.joblib`) | Classifies complaint text to one of 15 city departments |
| Logistic Regression (`complaint_priority_model.joblib`) | Assigns P1 / P2 / P3 priority from complaint description |
| Label Encoder (`label_encoder_bert.joblib`) | Decodes model output to department names |

Priority is further refined using real-time **Point of Interest (POI) density** from the Overpass API (OpenStreetMap), weighting complaints in high-density areas higher.

---

## 🏢 Supported Departments

- Department of Buildings
- Department of Consumer and Worker Protection
- Department of Education
- Department of Environmental Protection
- Department of Health and Mental Hygiene
- Department of Homeless Services
- Department of Housing Preservation and Development
- Department of Parks and Recreation
- Department of Sanitation
- Department of Transportation
- Economic Development Corporation
- New York City Police Department
- Office of Technology and Innovation
- Taxi and Limousine Commission

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite (dev) / PostgreSQL (production via Render) |
| ORM | SQLAlchemy |
| ML | scikit-learn, sentence-transformers (all-MiniLM-L6-v2) |
| NLP | BERT embeddings via HuggingFace |
| SMS OTP | Twilio |
| Geolocation | Browser Geolocation API + Overpass API |
| Frontend | Vanilla HTML, CSS, JavaScript |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip
- A [Twilio](https://www.twilio.com) account (free trial works)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/civic-complaint-system.git
cd civic-complaint-system
```

### 2. Install dependencies

```bash
cd backend
pip install flask flask-cors sqlalchemy sentence-transformers joblib scikit-learn rapidfuzz requests twilio
```

### 3. Configure Twilio SMS

Open `backend/server.py` and fill in your Twilio credentials:

```python
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN  = "your_auth_token_here"
TWILIO_FROM_NUMBER = "+12345678901"
```

> **No Twilio yet?** OTP will fall back to printing in the server terminal for development.

### 4. Set up the database

```bash
cd backend
python models.py        # creates complaints.db
python create_admins.py # seeds admin accounts
```

### 5. Start the backend

```bash
python server.py
# Running on http://127.0.0.1:5000
```

### 6. Start the frontend

Open a second terminal:

```bash
cd frontend
python -m http.server 8080
```

### 7. Open in browser

```
http://localhost:8080/index.html
```

---

## 👤 Default Admin Accounts

| Username | Password | Department |
|----------|----------|------------|
| `superadmin` | `super123` | All departments |
| `buildings_admin` | `build123` | Department of Buildings |
| `sanitation_admin` | `clean123` | Department of Sanitation |
| `police_admin` | `police123` | NYPD |
| `health_admin` | `health123` | Department of Health |
| `transport_admin` | `trans123` | Department of Transportation |

> Full list of admin accounts is in `backend/create_admins.py`

---

## 🔐 Authentication Flow

```
Enter credentials + mobile number
        ↓
Backend verifies credentials
        ↓
OTP generated → sent to mobile via Twilio SMS
        ↓
User enters OTP (valid 5 minutes)
        ↓
Login successful → redirected to dashboard
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/signup` | Register a new citizen |
| `POST` | `/api/login/request-otp` | Verify credentials and send OTP |
| `POST` | `/api/login/verify-otp` | Verify OTP and complete login |
| `POST` | `/api/complaints` | Submit a new complaint |
| `GET`  | `/api/complaints` | Get all complaints (admin) |
| `GET`  | `/api/complaints/user/<id>` | Get complaints for a citizen |
| `PUT`  | `/api/complaints/<id>` | Update complaint status |
| `DELETE` | `/api/complaints/<id>` | Delete a complaint |

---

## 🗄️ Database Schema

### Users
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Full name |
| email | String | Unique email |
| password | String | Plain text (hash in production) |
| phone | String | Mobile number in E.164 format |
| role | String | `citizen`, `department_admin`, `superadmin` |
| department | String | Assigned department (admins only) |

### Complaints
| Column | Type | Description |
|--------|------|-------------|
| id | String (UUID) | Primary key |
| title | String | Short title |
| description | Text | Full complaint text |
| location | String | Location string or coordinates |
| department | String | ML-assigned department |
| status | String | Registered / In Progress / Resolved |
| priority | String | 1 (high) / 2 (medium) / 3 (low) |
| location_type | String | High / Medium / Low density |
| registered | DateTime | Submission timestamp |
| resolved | DateTime | Resolution timestamp |
| images | Text | JSON array of base64 image strings |
| videos | Text | JSON array of base64 video strings |
| citizen_id | Integer | Foreign key → users.id |

---

## 🔮 Future Improvements

- [ ] Hash passwords with bcrypt
- [ ] JWT token-based session management
- [ ] Email notifications on status change
- [ ] Analytics dashboard with complaint trends
- [ ] Mobile app (React Native)
- [ ] Export complaints to CSV/PDF
- [ ] Map view of complaints by location

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

> Built as a civic technology project to demonstrate AI-assisted complaint routing for municipal governments.
