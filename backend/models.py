import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./complaints.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String)
    email      = Column(String, unique=True, index=True)
    password   = Column(String)
    role       = Column(String, default="citizen")  # 'citizen' | 'department_admin' | 'superadmin'
    department = Column(String, nullable=True)

    complaints = relationship("Complaint", back_populates="citizen")


class Complaint(Base):
    __tablename__ = "complaints"
    id            = Column(String, primary_key=True, index=True)
    title         = Column(String)
    description   = Column(Text)
    location      = Column(String)
    department    = Column(String)
    status        = Column(String, default="Registered")
    priority      = Column(String, nullable=True)
    location_type = Column(String, nullable=True)
    registered    = Column(DateTime, default=datetime.datetime.now)
    resolved      = Column(DateTime, nullable=True)
    citizen_id    = Column(Integer, ForeignKey("users.id"))
    # Stored as a JSON string: '["data:image/jpeg;base64,...", ...]'
    # Use json.loads() / json.dumps() in the API layer.
    images        = Column(Text, nullable=True, default='[]')
    # Stored as a JSON string: '["data:video/mp4;base64,...", ...]'
    videos        = Column(Text, nullable=True, default='[]')

    citizen = relationship("User", back_populates="complaints")


def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")
