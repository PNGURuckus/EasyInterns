from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .config import settings

Base = declarative_base()

class OpportunityORM(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True)
    source = Column(String, index=True)
    company = Column(String, index=True)
    title = Column(String, index=True)
    location = Column(String, index=True, nullable=True)
    apply_url = Column(Text)
    description_snippet = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    remote_friendly = Column(Boolean, nullable=True)
    job_id = Column(String, index=True, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index("ix_company_title", "company", "title"),)

class ContactORM(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    company = Column(String, index=True)
    title = Column(String, index=True)
    location = Column(String, nullable=True)
    apply_url = Column(Text)
    source = Column(String, nullable=True)
    emails = Column(Text)  # comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("apply_url", name="uq_contacts_apply_url"),)

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(engine)

def upsert_opportunities(opps):
    from .models import Opportunity
    session = SessionLocal()
    new_count = 0
    try:
        for o in opps:
            assert isinstance(o, Opportunity)
            rec = OpportunityORM(
                key=o.key(),
                source=o.source,
                company=o.company,
                title=o.title,
                location=o.location,
                apply_url=o.apply_url,
                description_snippet=o.description_snippet,
                posted_at=o.posted_at,
                remote_friendly=o.remote_friendly,
                job_id=o.job_id,
                salary_min=o.salary_min,
                salary_max=o.salary_max,
                tags=",".join(o.tags) if o.tags else None,
            )
            session.add(rec)
            try:
                session.commit()
                new_count += 1
            except IntegrityError:
                session.rollback()
        return new_count
    finally:
        session.close()

def fetch_all(limit=500):
    session = SessionLocal()
    try:
        return list(session.query(OpportunityORM).order_by(OpportunityORM.created_at.desc()).limit(limit))
    finally:
        session.close()

def upsert_contacts(rows):
    session = SessionLocal()
    new_count = 0
    try:
        for r in rows:
            c = ContactORM(
                company=r["company"],
                title=r["title"],
                location=r.get("location") or "",
                apply_url=r["apply_url"],
                source=r.get("source") or "",
                emails=r.get("emails_csv") or "",
            )
            session.add(c)
            try:
                session.commit()
                new_count += 1
            except IntegrityError:
                session.rollback()
        return new_count
    finally:
        session.close()
