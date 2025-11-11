"""SQL query generator for content generation."""

from typing import List, Dict, Any, Optional
from database.connection import DatabaseConnection
from database.schema_parser import DBMLParser
import logging

logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generate and execute SQL queries based on user requests."""

    def __init__(self, dbml_path: str):
        """
        Initialize query generator.

        Args:
            dbml_path: Path to DBML schema file
        """
        self.db = DatabaseConnection()
        self.schema_parser = DBMLParser(dbml_path)

    def get_relevant_tables(self, keywords: List[str]) -> List[str]:
        """
        Find tables relevant to given keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of relevant table names
        """
        relevant_tables = set()

        for table_name in self.schema_parser.get_all_table_names():
            table = self.schema_parser.get_table(table_name)

            # Check table name
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in table_name.lower():
                    relevant_tables.add(table_name)
                    continue

                # Check table note
                if table.note and keyword_lower in table.note.lower():
                    relevant_tables.add(table_name)
                    continue

                # Check column names and notes
                for col in table.columns:
                    if keyword_lower in col.name.lower():
                        relevant_tables.add(table_name)
                        break
                    if col.note and keyword_lower in col.note.lower():
                        relevant_tables.add(table_name)
                        break

        return list(relevant_tables)

    def get_schema_context(self, table_names: Optional[List[str]] = None) -> str:
        """
        Get schema context for LLM.

        Args:
            table_names: Specific tables to include

        Returns:
            Schema information formatted for LLM
        """
        return self.schema_parser.get_table_info_for_llm(table_names)

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query.

        Args:
            sql: SQL query string

        Returns:
            Query results
        """
        try:
            results = self.db.execute_query(sql)
            return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def validate_query(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query without executing it.

        Args:
            sql: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Use EXPLAIN to validate without executing
            explain_sql = f"EXPLAIN {sql}"
            self.db.execute_query(explain_sql)
            return True, None
        except Exception as e:
            return False, str(e)

    def get_college_basic_info(self, college_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get basic college information.

        Args:
            college_id: Specific college ID (optional)
            limit: Maximum number of results

        Returns:
            College basic information
        """
        if college_id:
            query = """
                SELECT *
                FROM college_basic
                WHERE college_id = %s
                  AND is_active = true
            """
            return self.db.execute_query(query, (college_id,))
        else:
            query = f"""
                SELECT *
                FROM college_basic
                WHERE is_active = true
                LIMIT {limit}
            """
            return self.db.execute_query(query)

    def get_college_degrees(self, college_id: int) -> List[Dict[str, Any]]:
        """
        Get degrees offered by a college.

        Args:
            college_id: College ID

        Returns:
            List of degrees
        """
        query = """
            SELECT *
            FROM college_degree
            WHERE college_id = %s
              AND is_active = true
        """
        return self.db.execute_query(query, (college_id,))

    def get_college_with_rankings(self, college_id: int) -> Dict[str, Any]:
        """
        Get college information with rankings.

        Args:
            college_id: College ID

        Returns:
            College data with rankings
        """
        college_query = """
            SELECT cb.*
            FROM college_basic cb
            WHERE cb.college_id = %s
              AND cb.is_active = true
        """
        college_data = self.db.execute_query(college_query, (college_id,))

        if not college_data:
            return {}

        ranking_query = """
            SELECT cr.*, rb.body_name, rb.full_name
            FROM college_ranking cr
            JOIN ranking_body rb ON cr.ranking_body_id = rb.id
            WHERE cr.college_id = %s
              AND cr.is_active = true
            ORDER BY cr.year DESC
        """
        rankings = self.db.execute_query(ranking_query, (college_id,))

        return {
            "college": college_data[0],
            "rankings": rankings
        }

    def search_colleges(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search colleges by name, city, or state.

        Args:
            search_term: Search term
            limit: Maximum results

        Returns:
            Matching colleges
        """
        query = f"""
            SELECT *
            FROM college_basic
            WHERE (
                LOWER(name) LIKE %s
                OR LOWER(city) LIKE %s
                OR LOWER(state) LIKE %s
            )
            AND is_active = true
            LIMIT {limit}
        """
        search_pattern = f"%{search_term.lower()}%"
        return self.db.execute_query(query, (search_pattern, search_pattern, search_pattern))

    def get_college_complete_data(self, college_id: int) -> Dict[str, Any]:
        """
        Get complete college data for content generation.

        Args:
            college_id: College ID

        Returns:
            Complete college data including all related information
        """
        result = {}

        # Basic info
        basic_query = "SELECT * FROM college_basic WHERE college_id = %s AND is_active = true"
        basic = self.db.execute_query(basic_query, (college_id,))
        result['basic'] = basic[0] if basic else None

        if not result['basic']:
            return result

        # Degrees
        degrees_query = "SELECT * FROM college_degree WHERE college_id = %s AND is_active = true"
        result['degrees'] = self.db.execute_query(degrees_query, (college_id,))

        # Rankings
        rankings_query = """
            SELECT cr.*, rb.body_name, rb.full_name
            FROM college_ranking cr
            JOIN ranking_body rb ON cr.ranking_body_id = rb.id
            WHERE cr.college_id = %s AND cr.is_active = true
        """
        result['rankings'] = self.db.execute_query(rankings_query, (college_id,))

        # Accreditations
        accred_query = """
            SELECT ca.*, ab.body_name, ab.full_name
            FROM college_accreditation ca
            JOIN accreditation_body ab ON ca.accreditation_body_id = ab.id
            WHERE ca.college_id = %s AND ca.is_active = true
        """
        result['accreditations'] = self.db.execute_query(accred_query, (college_id,))

        # Infrastructure
        infra_query = "SELECT * FROM college_infrastructure WHERE college_id = %s AND is_active = true"
        result['infrastructure'] = self.db.execute_query(infra_query, (college_id,))

        # Long info
        long_info_query = "SELECT * FROM college_long_info WHERE college_id = %s"
        long_info = self.db.execute_query(long_info_query, (college_id,))
        result['long_info'] = long_info[0] if long_info else None

        return result
