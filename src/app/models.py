import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    api_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=generate_uuid, index=True
    )
    alert_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    monitors: Mapped[list["Monitor"]] = relationship(
        "Monitor", back_populates="user", cascade="all, delete-orphan"
    )


class Monitor(Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=generate_uuid, index=True
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)  # seconds
    grace: Mapped[int] = mapped_column(Integer, nullable=False)  # seconds
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="new"
    )  # new, up, down, paused
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="monitors")
    pings: Mapped[list["Ping"]] = relationship(
        "Ping", back_populates="monitor", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="monitor", cascade="all, delete-orphan"
    )


class Ping(Base):
    __tablename__ = "pings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monitor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("monitors.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    remote_addr: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    monitor: Mapped["Monitor"] = relationship("Monitor", back_populates="pings")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monitor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("monitors.id"), nullable=False, index=True
    )
    alert_type: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "down" or "up" (recovery)
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "email", "webhook"
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    monitor: Mapped["Monitor"] = relationship("Monitor", back_populates="alerts")
