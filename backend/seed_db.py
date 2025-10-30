"""Seed database with initial users."""
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.repositories.user_repository import create_user
from app.services.auth_service import hash_password

# Use environment variable for database URL
DATABASE_URL = "postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd"


async def seed_users():
    """Create initial users in the database."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        # Create engineer user
        engineer_hash = hash_password("engineer123")
        await create_user(
            session,
            username="engineer",
            email="engineer@sovd.example.com",
            password_hash=engineer_hash,
            role="engineer",
        )

        # Create admin user
        admin_hash = hash_password("admin123")
        await create_user(
            session,
            username="admin",
            email="admin@sovd.example.com",
            password_hash=admin_hash,
            role="admin",
        )

        await session.commit()
        print("✅ Users created successfully:")
        print(f"  - Engineer: username='engineer', password='engineer123'")
        print(f"  - Admin: username='admin', password='admin123'")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_users())
