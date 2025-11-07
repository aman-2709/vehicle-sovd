"""Seed database with test vehicles."""
import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.vehicle import Vehicle

DATABASE_URL = "postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd"


async def seed_vehicles():
    """Create test vehicles in the database."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        # Create test vehicles
        vehicles = [
            Vehicle(
                vin="1HGBH41JXMN109186",
                make="Tesla",
                model="Model 3",
                year=2023,
                connection_status="connected",
                last_seen_at=datetime.now(timezone.utc),
                metadata={"battery_capacity": "75 kWh", "autopilot": True}
            ),
            Vehicle(
                vin="5YJSA1E14HF123456",
                make="Tesla",
                model="Model S",
                year=2022,
                connection_status="connected",
                last_seen_at=datetime.now(timezone.utc),
                metadata={"battery_capacity": "100 kWh", "autopilot": True}
            ),
            Vehicle(
                vin="WBADT43452G123456",
                make="BMW",
                model="i4",
                year=2024,
                connection_status="disconnected",
                last_seen_at=None,
                metadata={"battery_capacity": "80 kWh"}
            ),
            Vehicle(
                vin="WAUZZZ8V8KA123456",
                make="Audi",
                model="e-tron GT",
                year=2023,
                connection_status="connected",
                last_seen_at=datetime.now(timezone.utc),
                metadata={"battery_capacity": "93 kWh", "quattro": True}
            ),
        ]

        for vehicle in vehicles:
            session.add(vehicle)

        await session.commit()
        print("✅ Test vehicles created successfully:")
        for v in vehicles:
            print(f"  - {v.year} {v.make} {v.model} (VIN: {v.vin}) - Status: {v.connection_status}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_vehicles())
