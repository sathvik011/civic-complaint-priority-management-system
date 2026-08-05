import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, create_tables

DATABASE_URL = "sqlite:///./complaints.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

admin_accounts = {
    "superadmin": {"password": "super123", "role": "superadmin", "department": None},
    "municipal_admin": {"password": "muni123", "role": "department_admin", "department": "Municipal Corporation"},
    "police_admin": {"password": "police123", "role": "department_admin", "department": "Police Department"},
    "fire_admin": {"password": "fire123", "role": "department_admin", "department": "Fire Department"},
    "pwd_admin": {"password": "pwd123", "role": "department_admin", "department": "Public Works Department (PWD)"},
    "electricity_admin": {"password": "elec123", "role": "department_admin", "department": "Electricity Board"},
    "water_admin": {"password": "water123", "role": "department_admin", "department": "Environmental Department"},
    "health_admin": {"password": "health123", "role": "department_admin", "department": "Health Department"},
    "traffic_admin": {"password": "traffic123", "role": "department_admin", "department": "Public Works Department (PWD)"},
    "housing_admin": {"password": "house123", "role": "department_admin", "department": "Housing Board"},
    "education_admin": {"password": "edu123", "role": "department_admin", "department": "Education Department"},
    "environment_admin": {"password": "env123", "role": "department_admin", "department": "Environmental Department"},
    "parks_admin": {"password": "park123", "role": "department_admin", "department": "Department of Parks and Gardens"},
    "consumer_admin": {"password": "consumer123", "role": "department_admin", "department": "Department of Consumer Protection"},
    "labor_admin": {"password": "labor123", "role": "department_admin", "department": "Department of Labor"},
    "welfare_admin": {"password": "welfare123", "role": "department_admin", "department": "Social Welfare Department"}
}

def create_admin_users():
    db = SessionLocal()
    try:
        for username, data in admin_accounts.items():
            existing_user = db.query(User).filter(User.name == username).first()
            if not existing_user:
                new_admin = User(
                    name=username,
                    email=f"{username}@civic.gov",
                    password=data["password"],
                    role=data["role"],
                    department=data["department"]
                )
                db.add(new_admin)
                print(f"Created admin user: {username}")
            else:
                print(f"Admin user '{username}' already exists. Skipping.")
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error creating admin users: {e}", file=sys.stderr)
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()  # Ensure tables exist
    create_admin_users()