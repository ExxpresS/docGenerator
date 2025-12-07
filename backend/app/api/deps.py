from typing import Generator
from app.db.connection import get_db


def get_database() -> Generator:
    """Dependency pour récupérer une connexion DB"""
    with get_db() as db:
        yield db
