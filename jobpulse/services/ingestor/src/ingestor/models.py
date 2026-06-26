from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Vacancy(Base):
    __tablename__ = "vacancies"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_vacancy_source_external"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    external_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    analyst_role: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    employer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    area: Mapped[str | None] = mapped_column(String(128), nullable=True)
    experience: Mapped[str | None] = mapped_column(String(64), nullable=True)
    employment: Mapped[str | None] = mapped_column(String(64), nullable=True)
    schedule: Mapped[str | None] = mapped_column(String(64), nullable=True)
    salary_from: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_to: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    salary_gross: Mapped[bool | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class IngestRun(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SalarySnapshot(Base):
    __tablename__ = "salary_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    analyst_role: Mapped[str] = mapped_column(String(32), index=True)
    experience: Mapped[str] = mapped_column(String(64), index=True)
    avg_salary: Mapped[float] = mapped_column(Float)
    median_salary: Mapped[float] = mapped_column(Float)
    vacancy_count: Mapped[int] = mapped_column(Integer, default=0)


def get_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


def _migrate_schema(engine) -> None:
    stmts = (
        "ALTER TABLE vacancies ADD COLUMN IF NOT EXISTS key_skills TEXT",
    )
    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))


def init_db(database_url: str) -> sessionmaker:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    _migrate_schema(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
