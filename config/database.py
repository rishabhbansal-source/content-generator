"""Database configuration settings."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration class."""

    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

    def __post_init__(self):
        """Initialize from environment variables with defaults."""
        self.host = os.getenv("DB_HOST")
        port_str = os.getenv("DB_PORT")
        try:
            self.port = int(port_str)
        except (ValueError, TypeError):
            self.port = None
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        
        # Validate required fields
        if not self.database:
            raise ValueError(
                "DB_NAME environment variable is required. "
                "Please set it in your .env file or environment."
            )
        if not self.user:
            raise ValueError(
                "DB_USER environment variable is required. "
                "Please set it in your .env file or environment."
            )
        if not self.password:
            raise ValueError(
                "DB_PASSWORD environment variable is required. "
                "Please set it in your .env file or environment."
            )

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_psycopg2_params(self) -> dict:
        """Get psycopg2 connection parameters."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password
        }
