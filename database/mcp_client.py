"""MCP client for PostgreSQL database introspection and operations."""

import logging
from typing import List, Dict, Any, Optional
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class PostgresMCPClient:
    """Client for PostgreSQL database operations using MCP patterns."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize MCP client.

        Args:
            db_connection: Database connection instance
        """
        self.db = db_connection

    def get_schema_info(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive schema information for tables.

        Args:
            table_names: Optional list of specific tables to query

        Returns:
            Dictionary with schema information
        """
        try:
            # Build query to get table and column information
            if table_names:
                table_filter = f"AND table_name = ANY(ARRAY{table_names}::text[])"
            else:
                table_filter = ""

            query = f"""
                SELECT
                    table_name,
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_schema = 'public'
                {table_filter}
                ORDER BY table_name, ordinal_position;
            """

            columns_info = self.db.execute_query(query)

            # Get foreign key relationships
            fk_query = f"""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                {table_filter.replace('table_name', 'tc.table_name') if table_filter else ''};
            """

            fk_info = self.db.execute_query(fk_query)

            # Organize schema information
            schema = {}
            for col in columns_info:
                table = col['table_name']
                if table not in schema:
                    schema[table] = {
                        'columns': [],
                        'foreign_keys': []
                    }

                column_info = {
                    'name': col['column_name'],
                    'type': col['data_type'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default']
                }

                if col['character_maximum_length']:
                    column_info['max_length'] = col['character_maximum_length']
                if col['numeric_precision']:
                    column_info['precision'] = col['numeric_precision']
                if col['numeric_scale']:
                    column_info['scale'] = col['numeric_scale']

                schema[table]['columns'].append(column_info)

            # Add foreign key information
            for fk in fk_info:
                table = fk['table_name']
                if table in schema:
                    schema[table]['foreign_keys'].append({
                        'column': fk['column_name'],
                        'references_table': fk['foreign_table_name'],
                        'references_column': fk['foreign_column_name']
                    })

            logger.info(f"Retrieved schema info for {len(schema)} tables")
            return schema

        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return {}

    def get_table_names(self) -> List[str]:
        """
        Get list of all table names in the database.

        Returns:
            List of table names
        """
        try:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """

            result = self.db.execute_query(query)
            tables = [row['table_name'] for row in result]
            logger.info(f"Found {len(tables)} tables")
            return tables

        except Exception as e:
            logger.error(f"Error getting table names: {e}")
            return []

    def get_colleges_list(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get list of colleges for user selection.

        Args:
            limit: Maximum number of colleges to return

        Returns:
            List of college dictionaries with id, name, city, state
        """
        try:
            query = f"""
                SELECT
                    college_id,
                    name as college_name,
                    city,
                    state
                FROM college_basic
                WHERE is_active = true
                ORDER BY name
                LIMIT {limit};
            """

            colleges = self.db.execute_query(query)
            logger.info(f"Retrieved {len(colleges)} colleges")
            return colleges

        except Exception as e:
            logger.error(f"Error getting colleges list: {e}")
            return []

    def get_college_details(self, college_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific college.

        Args:
            college_id: College ID

        Returns:
            Dictionary with college details or None
        """
        try:
            query = """
                SELECT *
                FROM college_basic
                WHERE college_id = %s
                    AND is_active = true;
            """

            result = self.db.execute_query(query, (college_id,))
            if result:
                logger.info(f"Retrieved details for college_id={college_id}")
                return result[0]
            else:
                logger.warning(f"No college found with id={college_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting college details: {e}")
            return None

    def search_colleges(
        self,
        search_term: str,
        by_name: bool = True,
        by_city: bool = True,
        by_state: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search colleges by various criteria from college_basic table.

        Args:
            search_term: Search term (searches in name, city, or state)
            by_name: Search in college name
            by_city: Search in city
            by_state: Search in state
            limit: Maximum results

        Returns:
            List of matching colleges with college_id, college_name, city, state
        """
        if not search_term or not search_term.strip():
            logger.warning("Empty search term provided")
            return []

        try:
            # Build search conditions
            conditions = []
            if by_name:
                conditions.append("LOWER(name) LIKE LOWER(%s)")
            if by_city:
                conditions.append("LOWER(city) LIKE LOWER(%s)")
            if by_state:
                conditions.append("LOWER(state) LIKE LOWER(%s)")

            if not conditions:
                logger.warning("No search criteria enabled")
                return []

            # Clean and prepare search term
            search_term = search_term.strip()
            where_clause = " OR ".join(conditions)
            search_pattern = f"%{search_term}%"
            params = tuple([search_pattern] * len(conditions))

            # Query college_basic table with parameterized query
            query = f"""
                SELECT
                    college_id,
                    name as college_name,
                    city,
                    state
                FROM college_basic
                WHERE is_active = true
                    AND ({where_clause})
                ORDER BY name
                LIMIT {limit};
            """

            colleges = self.db.execute_query(query, params)
            logger.info(f"Found {len(colleges)} colleges matching '{search_term}' in college_basic table")
            return colleges

        except Exception as e:
            logger.error(f"Error searching colleges from college_basic table: {e}", exc_info=True)
            return []

    def get_schema_context_for_llm(self, table_names: Optional[List[str]] = None) -> str:
        """
        Get schema information formatted for LLM context.

        Args:
            table_names: Optional list of specific tables

        Returns:
            Formatted schema description
        """
        schema_info = self.get_schema_info(table_names)

        if not schema_info:
            return "No schema information available."

        context = "PostgreSQL Database Schema:\n\n"

        for table_name, table_data in sorted(schema_info.items()):
            context += f"Table: {table_name}\n"
            context += "Columns:\n"

            for col in table_data['columns']:
                col_desc = f"  - {col['name']} ({col['type']})"
                if not col['nullable']:
                    col_desc += " NOT NULL"
                if col.get('default'):
                    col_desc += f" DEFAULT {col['default']}"
                context += col_desc + "\n"

            if table_data['foreign_keys']:
                context += "Foreign Keys:\n"
                for fk in table_data['foreign_keys']:
                    context += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"

            context += "\n"

        return context
