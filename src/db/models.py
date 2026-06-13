import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/prospectpilot.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    company_name = Column(String, nullable=False)
    company_domain = Column(String, default="")
    research = Column(JSON)               # research_agent çıktısı
    draft_subject = Column(Text)
    draft_body = Column(Text)
    contact_name = Column(String, default="")
    contact_email = Column(String, default="")
    contact_position = Column(String, default="")
    status = Column(String, default="draft")   # draft | approved | sent | replied
    sent_at = Column(DateTime, nullable=True)
    follow_up_count = Column(Integer, default=0)
    last_follow_up_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Lead {self.company_name} — {self.status}>"


def init_db():
    Base.metadata.create_all(engine)
