"""SQLAlchemy declarative base for all ORM models.

This module provides the DeclarativeBase class that all ORM models inherit from.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in the SOVD application."""

    pass
