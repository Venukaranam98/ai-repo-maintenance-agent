"""
models.py

SQLAlchemy models for the audit trail and multi-user data. Using SQLite by
default (zero setup) but DATABASE_URL can point to Postgres in production
without changing any code here - that's the point of using an ORM.
"""

import datetime

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from agent.config import settings

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    github_username = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    # Access token is stored so the agent can act on the user's behalf later.
    # In a real production deploy this column should be encrypted at rest.
    github_access_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    repos = relationship("MonitoredRepo", back_populates="owner", cascade="all, delete-orphan")


class MonitoredRepo(Base):
    __tablename__ = "monitored_repos"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=False)  # "owner/repo"
    enabled = Column(Boolean, default=True)
    auto_merge_docs_only = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="repos")
    runs = relationship("AgentRun", back_populates="repo", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("monitored_repos.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="pending")  # pending | passed | failed | no_gaps | error
    gap_summary = Column(Text, nullable=True)     # JSON string of the health report
    proposed_file = Column(String, nullable=True)
    commit_message = Column(String, nullable=True)
    pr_url = Column(String, nullable=True)
    validation_log = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    repo = relationship("MonitoredRepo", back_populates="runs")


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
