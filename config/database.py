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
        
        # Validate required fields and provide helpful error messages
        missing_vars = []
        if not self.database:
            missing_vars.append("DB_NAME")
        if not self.user:
            missing_vars.append("DB_USER")
        if not self.password:
            missing_vars.append("DB_PASSWORD")
        
        if missing_vars:
            error_msg = (
                f"Missing required database environment variables: {', '.join(missing_vars)}\n\n"
            )
            
            # Detect if this might be a cloud deployment
            if os.path.exists('/mount/src') or 'STREAMLIT_SHARING' in os.environ:
                error_msg += (
                    "🌐 **Cloud Deployment Detected**\n\n"
                    "For Streamlit Cloud or similar platforms:\n"
                    "1. Go to your app's settings/secrets page\n"
                    "2. Add these environment variables:\n"
                    "   - DB_HOST (e.g., db.xxxxx.supabase.co)\n"
                    "   - DB_PORT (usually 5432)\n"
                    "   - DB_NAME (your database name)\n"
                    "   - DB_USER (your database username)\n"
                    "   - DB_PASSWORD (your database password)\n\n"
                    "💡 **Recommended:** Use a free PostgreSQL service like:\n"
                    "   - Supabase (https://supabase.com)\n"
                    "   - Neon (https://neon.tech)\n"
                    "   - AWS RDS, Google Cloud SQL, etc.\n"
                )
            else:
                error_msg += (
                    "📝 **Local Development Setup**\n\n"
                    "Create a `.env` file in your project root with:\n"
                    "```env\n"
                    "DB_HOST=localhost\n"
                    "DB_PORT=5432\n"
                    "DB_NAME=your_database_name\n"
                    "DB_USER=your_username\n"
                    "DB_PASSWORD=your_password\n"
                    "```\n\n"
                    "Then make sure PostgreSQL is running locally."
                )
            
            raise ValueError(error_msg)

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
