from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_settings
from backend.database.base import Base

settings = get_settings()

engine_kwargs = {
    "future": True,
    "pool_pre_ping": True,
}

if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        {
            "pool_size": 2,
            "max_overflow": 3,
            "pool_timeout": 30,
        }
    )

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create database tables for local/dev use."""

    import backend.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        with engine.begin() as connection:
            columns = connection.execute(text("PRAGMA table_info(research_sessions)")).fetchall()
            names = {column[1] for column in columns}
            if "timeline_summary" not in names:
                connection.execute(
                    text("ALTER TABLE research_sessions ADD COLUMN timeline_summary TEXT DEFAULT '[]'")
                )
            evidence_columns = connection.execute(text("PRAGMA table_info(evidence)")).fetchall()
            evidence_names = {column[1] for column in evidence_columns}
            for column_name, definition in {
                "normalized_url": "VARCHAR(1000)",
                "source_type": "VARCHAR(120) DEFAULT 'unknown'",
                "extraction_method": "VARCHAR(80) DEFAULT 'regex'",
                "reliability_score": "INTEGER DEFAULT 50",
                "crawl_status": "VARCHAR(40) DEFAULT 'success'",
            }.items():
                if column_name not in evidence_names:
                    connection.execute(text(f"ALTER TABLE evidence ADD COLUMN {column_name} {definition}"))
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS research_cache ("
                    "id INTEGER NOT NULL PRIMARY KEY, "
                    "cache_key VARCHAR(300) NOT NULL UNIQUE, "
                    "session_id INTEGER NOT NULL, "
                    "demo_mode BOOLEAN NOT NULL DEFAULT 1, "
                    "hit_count INTEGER NOT NULL DEFAULT 0, "
                    "expires_at DATETIME NOT NULL, "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "FOREIGN KEY(session_id) REFERENCES research_sessions (id)"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS crawl_cache ("
                    "id INTEGER NOT NULL PRIMARY KEY, "
                    "url VARCHAR(1000) NOT NULL, "
                    "normalized_url VARCHAR(1000) NOT NULL UNIQUE, "
                    "source_type VARCHAR(120) DEFAULT 'unknown', "
                    "status VARCHAR(40) DEFAULT 'success', "
                    "http_status INTEGER, "
                    "content_hash VARCHAR(80), "
                    "extracted_text_preview TEXT, "
                    "extracted_fields_json TEXT, "
                    "error_message TEXT, "
                    "first_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "last_attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "last_success_at DATETIME, "
                    "attempt_count INTEGER DEFAULT 0, "
                    "ttl_expires_at DATETIME NOT NULL"
                    ")"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS research_jobs ("
                    "id INTEGER NOT NULL PRIMARY KEY, "
                    "session_id INTEGER NOT NULL, "
                    "status VARCHAR(50) DEFAULT 'pending', "
                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "started_at DATETIME, "
                    "completed_at DATETIME, "
                    "current_stage VARCHAR(80) DEFAULT 'planning', "
                    "total_urls INTEGER DEFAULT 0, "
                    "processed_urls INTEGER DEFAULT 0, "
                    "verified_businesses INTEGER DEFAULT 0, "
                    "discovered_businesses INTEGER DEFAULT 0, "
                    "failed_urls INTEGER DEFAULT 0, "
                    "stage_progress INTEGER DEFAULT 0, "
                    "candidate_urls_json TEXT DEFAULT '[]', "
                    "partial_businesses_json TEXT DEFAULT '[]', "
                    "failed_urls_json TEXT DEFAULT '[]', "
                    "enrichment_status VARCHAR(80) DEFAULT 'pending', "
                    "error_message TEXT, "
                    "FOREIGN KEY(session_id) REFERENCES research_sessions (id)"
                    ")"
                )
            )
            job_columns = connection.execute(text("PRAGMA table_info(research_jobs)")).fetchall()
            job_names = {column[1] for column in job_columns}
            if "error_message" not in job_names:
                connection.execute(text("ALTER TABLE research_jobs ADD COLUMN error_message TEXT"))
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS timeline_events ("
                    "id INTEGER NOT NULL PRIMARY KEY, "
                    "session_id INTEGER NOT NULL, "
                    "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, "
                    "event_type VARCHAR(120) NOT NULL, "
                    "message TEXT NOT NULL, "
                    "payload TEXT DEFAULT '{}', "
                    "stage VARCHAR(80), "
                    "progress FLOAT DEFAULT 0, "
                    "FOREIGN KEY(session_id) REFERENCES research_sessions (id)"
                    ")"
                )
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
