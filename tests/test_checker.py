import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.models import Monitor, User, Alert
from app.auth import hash_password
from app.checker import check_overdue_monitors
from tests.conftest import test_session


@pytest.mark.asyncio
async def test_checker_marks_overdue_monitor_down():
    """Test that the checker marks a monitor as down when it's overdue."""
    async with test_session() as db:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password"),
        )
        db.add(user)
        await db.flush()

        monitor = Monitor(
            user_id=user.id,
            name="Overdue Monitor",
            period=300,
            grace=60,
            status="up",
            last_ping_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(monitor)
        await db.commit()
        monitor_id = monitor.id

    await check_overdue_monitors(session_factory=test_session)

    async with test_session() as db:
        result = await db.execute(select(Monitor).where(Monitor.id == monitor_id))
        updated_monitor = result.scalar_one()
        assert updated_monitor.status == "down"

        alerts = await db.execute(select(Alert).where(Alert.monitor_id == monitor_id))
        alert_list = alerts.scalars().all()
        assert len(alert_list) > 0
        assert alert_list[0].alert_type == "down"


@pytest.mark.asyncio
async def test_checker_ignores_paused_monitors():
    async with test_session() as db:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password"),
        )
        db.add(user)
        await db.flush()

        monitor = Monitor(
            user_id=user.id,
            name="Paused Monitor",
            period=300,
            grace=60,
            status="paused",
            last_ping_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(monitor)
        await db.commit()
        monitor_id = monitor.id

    await check_overdue_monitors(session_factory=test_session)

    async with test_session() as db:
        result = await db.execute(select(Monitor).where(Monitor.id == monitor_id))
        m = result.scalar_one()
        assert m.status == "paused"


@pytest.mark.asyncio
async def test_checker_ignores_new_monitors():
    async with test_session() as db:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password"),
        )
        db.add(user)
        await db.flush()

        monitor = Monitor(
            user_id=user.id,
            name="New Monitor",
            period=300,
            grace=60,
            status="new",
            last_ping_at=None,
        )
        db.add(monitor)
        await db.commit()
        monitor_id = monitor.id

    await check_overdue_monitors(session_factory=test_session)

    async with test_session() as db:
        result = await db.execute(select(Monitor).where(Monitor.id == monitor_id))
        m = result.scalar_one()
        assert m.status == "new"


@pytest.mark.asyncio
async def test_checker_doesnt_alert_on_already_down():
    async with test_session() as db:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password"),
        )
        db.add(user)
        await db.flush()

        monitor = Monitor(
            user_id=user.id,
            name="Down Monitor",
            period=300,
            grace=60,
            status="down",
            last_ping_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(monitor)
        await db.commit()

    await check_overdue_monitors(session_factory=test_session)

    async with test_session() as db:
        alerts = await db.execute(select(Alert))
        alert_list = alerts.scalars().all()
        assert len(alert_list) == 0


@pytest.mark.asyncio
async def test_checker_leaves_timely_monitors_up():
    async with test_session() as db:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hash_password("password"),
        )
        db.add(user)
        await db.flush()

        monitor = Monitor(
            user_id=user.id,
            name="Timely Monitor",
            period=3600,
            grace=1800,
            status="up",
            last_ping_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        db.add(monitor)
        await db.commit()
        monitor_id = monitor.id

    await check_overdue_monitors(session_factory=test_session)

    async with test_session() as db:
        result = await db.execute(select(Monitor).where(Monitor.id == monitor_id))
        m = result.scalar_one()
        assert m.status == "up"
