from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    reviews: Mapped[list["ReviewRecord"]] = relationship(
        "ReviewRecord", back_populates="owner", cascade="all, delete-orphan"
    )


class ReviewRecord(Base):
    """Stores high-level metadata for a single code review request."""

    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Nullable for backward-compatibility with pre-auth reviews.
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    space_complexity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    refactored_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner: Mapped["User | None"] = relationship("User", back_populates="reviews")
    issues: Mapped[list["IssueRecord"]] = relationship(
        "IssueRecord", back_populates="review", cascade="all, delete-orphan"
    )


class IssueRecord(Base):
    """Stores individual issues found during a code review."""

    __tablename__ = "review_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    review_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("review_records.id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)      # STATIC_ANALYSIS | AI
    severity: Mapped[str] = mapped_column(String(20), nullable=False)    # LOW | MEDIUM | HIGH | CRITICAL
    category: Mapped[str] = mapped_column(String(50), nullable=False)    # BUG | SECURITY | …
    message: Mapped[str] = mapped_column(Text, nullable=False)
    line: Mapped[str | None] = mapped_column(String(100), nullable=True)
    column: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    review: Mapped["ReviewRecord"] = relationship("ReviewRecord", back_populates="issues")
