"""Database connection manager for PostgreSQL."""

import psycopg2
from psycopg2 import pool
from typing import Optional, Any, List, Dict
import logging
from config.database import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Singleton database connection manager."""

    _instance: Optional['DatabaseConnection'] = None
    _connection_pool: Optional[pool.SimpleConnectionPool] = None

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database connection."""
        if self._connection_pool is None:
            self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            config = DatabaseConfig()
            params = config.get_psycopg2_params()

            self._connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **params
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool."""
        if self._connection_pool is None:
            self._initialize_pool()
        return self._connection_pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self._connection_pool:
            self._connection_pool.putconn(conn)

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as a list of dictionaries.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of dictionaries with column names as keys
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]

            cursor.close()
            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return results

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            Number of affected rows
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            affected_rows = cursor.rowcount
            conn.commit()

            cursor.close()
            logger.info(f"Update executed successfully, {affected_rows} rows affected")
            return affected_rows

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error executing update: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            result = self.execute_query("SELECT 1 as test")
            return len(result) > 0 and result[0].get('test') == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_table_names(self) -> List[str]:
        """
        Get all table names from the database.

        Returns:
            List of table names
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        results = self.execute_query(query)
        return [row['table_name'] for row in results]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of dictionaries containing column information
        """
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
        """
        return self.execute_query(query, (table_name,))

    def close_all_connections(self):
        """Close all connections in the pool."""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.info("All database connections closed")
