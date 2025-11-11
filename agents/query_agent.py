"""Query agent for converting natural language to SQL queries."""

import logging
from typing import Dict, Any, List, Optional
from models.llm_interface import BaseLLM
from database.query_generator import QueryGenerator
from database.mcp_client import PostgresMCPClient

logger = logging.getLogger(__name__)


class QueryAgent:
    """Agent for generating and executing database queries."""

    def __init__(
        self,
        llm: BaseLLM,
        query_generator: QueryGenerator,
        mcp_client: Optional[PostgresMCPClient] = None
    ):
        """
        Initialize query agent.

        Args:
            llm: LLM instance
            query_generator: Query generator instance
            mcp_client: Optional MCP client for enhanced schema introspection
        """
        self.llm = llm
        self.query_generator = query_generator
        self.mcp_client = mcp_client

    def analyze_query(self, user_query: str, content_type: str) -> Dict[str, Any]:
        """
        Analyze user query to determine what data is needed.

        Args:
            user_query: User's content request
            content_type: Type of content to generate

        Returns:
            Analysis results including keywords and relevant tables
        """
        system_prompt = """You are a database query analyzer. Your job is to extract key information from a user's content request.

Extract:
1. Main topics/keywords
2. Specific entities (college names, programs, locations, etc.)
3. Type of information needed (rankings, fees, infrastructure, etc.)

Return your analysis in a structured format."""

        prompt = f"""Analyze this content request for a college database:

Content Type: {content_type}
User Request: {user_query}

Extract the following:
- Keywords: List the main keywords related to colleges, programs, locations, etc.
- Entities: Any specific college names, degree programs, cities, etc.
- Data Requirements: What type of data is needed (basic info, rankings, fees, infrastructure, etc.)?

Provide a clear, structured analysis."""

        try:
            response = self.llm.generate(prompt, system_prompt=system_prompt)
            logger.info("Query analysis completed")

            # Parse keywords from response (simple extraction)
            keywords = self._extract_keywords(response)

            # Find relevant tables
            relevant_tables = self.query_generator.get_relevant_tables(keywords)

            return {
                "analysis": response,
                "keywords": keywords,
                "relevant_tables": relevant_tables
            }

        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {
                "analysis": "",
                "keywords": [],
                "relevant_tables": []
            }

    def generate_sql_query(
        self,
        user_query: str,
        relevant_tables: List[str],
        content_type: str,
        selected_college_id: Optional[int] = None,
        previous_error: Optional[str] = None
    ) -> str:
        """
        Generate SQL query based on user request.

        Args:
            user_query: User's content request
            relevant_tables: List of relevant table names
            content_type: Type of content
            selected_college_id: Optional specific college ID to filter by
            previous_error: Optional error from previous attempt (for learning)

        Returns:
            SQL query string
        """
        # Get schema context for relevant tables
        # Use MCP client if available for more accurate schema info
        if self.mcp_client:
            schema_context = self.mcp_client.get_schema_context_for_llm(relevant_tables)
        else:
            schema_context = self.query_generator.get_schema_context(relevant_tables)

        system_prompt = """You are an expert PostgreSQL query generator. Create efficient, well-structured SQL queries based on user requirements.

IMPORTANT - PostgreSQL Syntax Rules:
1. Use STRING_AGG() NOT GROUP_CONCAT() for string concatenation
2. Use proper JOIN syntax for related tables
3. Include only necessary columns
4. Use WHERE clauses to filter active records (is_active = true)
5. Limit results appropriately (LIMIT 50 or less)
6. Use meaningful aliases
7. PostgreSQL-specific: Use ARRAY_AGG() for arrays, || for string concatenation
8. Return ONLY the SQL query, no explanations or markdown

CRITICAL - PostgreSQL GROUP BY Rules:
- When using GROUP BY, ALL non-aggregated columns in SELECT must be in GROUP BY clause
- Example CORRECT:
  SELECT cb.name, cb.city, STRING_AGG(d.name, ', ') as degrees
  FROM college_basic cb
  JOIN degree d ON cb.college_id = d.college_id
  GROUP BY cb.college_id, cb.name, cb.city

- Example WRONG:
  SELECT cb.name, cb.city, STRING_AGG(d.name, ', ') as degrees
  FROM college_basic cb
  JOIN degree d ON cb.college_id = d.college_id
  GROUP BY cb.college_id  -- MISSING cb.name, cb.city

EXCLUDED TABLES - DO NOT USE:
- college_long_info
- college_short_info

PostgreSQL Examples:
- String aggregation: STRING_AGG(column, ', ')
- Array aggregation: ARRAY_AGG(column)
- String concat: column1 || ' ' || column2"""

        college_filter_note = ""
        if selected_college_id:
            college_filter_note = f"""

IMPORTANT - College Filter:
The user has selected a specific college (college_id = {selected_college_id}).
You MUST add a WHERE clause to filter by this college_id in the main query or JOIN condition.
Example: WHERE c.college_id = {selected_college_id}
"""

        previous_error_note = ""
        if previous_error:
            previous_error_note = f"""

⚠️ PREVIOUS ATTEMPT FAILED - LEARN FROM THIS ERROR:
{previous_error}

IMPORTANT: Carefully review the error above and ensure you don't make the same mistake.
- Check table aliases match the JOIN statements
- Verify column names exist in the actual tables
- Ensure all non-aggregated columns are in GROUP BY
"""

        prompt = f"""Generate a PostgreSQL query for this request:

User Request: {user_query}
Content Type: {content_type}
{college_filter_note}
{previous_error_note}

Available Database Schema:
{schema_context}

Generate a SELECT query that retrieves the necessary data.

CRITICAL Rules:
1. This is PostgreSQL, NOT MySQL. Use PostgreSQL syntax:
   - Use STRING_AGG() instead of GROUP_CONCAT()
   - Use ARRAY_AGG() for arrays
   - Use || for string concatenation

2. DO NOT use these tables:
   - college_long_info
   - college_short_info

3. IMPORTANT - Table Usage:
   - Use college_ranking (NOT history_college_ranking) for current rankings
   - Use college_accreditation (NOT history_college_accreditation) for current accreditations
   - History tables are for temporal versioning - only use if specifically needed

4. When using table aliases, be VERY careful:
   - Check which table each column belongs to
   - Use the correct alias.column_name format
   - Example: If 'hr' is alias for history_college_ranking, use hr.rank_value (NOT ra.rank_value)

Return ONLY the SQL query, no explanations."""

        try:
            sql_query = self.llm.generate(prompt, system_prompt=system_prompt, temperature=0.3)

            # Clean up the response (remove markdown code blocks if present)
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

            # Fix common MySQL → PostgreSQL syntax issues
            sql_query = self._fix_postgresql_syntax(sql_query)

            logger.info("SQL query generated")
            return sql_query

        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return ""

    def _fix_postgresql_syntax(self, sql: str) -> str:
        """
        Fix common MySQL syntax issues for PostgreSQL compatibility.

        Args:
            sql: SQL query string

        Returns:
            Fixed SQL query
        """
        import re

        original_sql = sql

        # Fix GROUP_CONCAT → STRING_AGG with better pattern
        # Handle nested parentheses and complex expressions
        def replace_group_concat(match):
            distinct = match.group(1) if match.group(1) else ''
            content = match.group(2)
            # Remove any trailing/leading whitespace
            distinct = distinct.strip()
            content = content.strip()
            if distinct:
                return f"STRING_AGG({distinct} {content}, ', ')"
            else:
                return f"STRING_AGG({content}, ', ')"

        sql = re.sub(
            r'GROUP_CONCAT\s*\(\s*(DISTINCT\s+)?(.+?)\)',
            replace_group_concat,
            sql,
            flags=re.IGNORECASE
        )

        # Log if changes were made
        if sql != original_sql:
            logger.info("Fixed SQL syntax: GROUP_CONCAT → STRING_AGG")
            logger.debug(f"Before: {original_sql[:200]}...")
            logger.debug(f"After: {sql[:200]}...")

        # Fix backticks → double quotes (for identifiers)
        sql = sql.replace('`', '"')

        # Fix AUTO_INCREMENT → SERIAL (though this shouldn't appear in SELECT queries)
        sql = re.sub(r'AUTO_INCREMENT', 'SERIAL', sql, flags=re.IGNORECASE)

        return sql

    def _fix_column_references(self, sql: str, error: str) -> str:
        """
        Attempt to fix column reference errors based on error message.

        Args:
            sql: SQL query with error
            error: Error message from PostgreSQL

        Returns:
            Fixed SQL query (or original if can't fix)
        """
        import re

        # Extract the problematic column reference from error
        # Error format: "column alias.column_name does not exist"
        # Hint format: "Perhaps you meant to reference the column \"correct_alias.column_name\"."

        # Try to extract the suggested fix from HINT
        hint_match = re.search(r'Perhaps you meant to reference the column "([^"]+)"', error)
        if hint_match:
            suggested = hint_match.group(1)
            logger.info(f"Found suggested fix in error: {suggested}")

            # Extract incorrect reference from error line
            # Match patterns like: column al.name does not exist OR column "al.name" does not exist
            line_match = re.search(r'column (?:")?([^\s"]+)(?:")? does not exist', error)
            if line_match:
                incorrect = line_match.group(1)
                logger.info(f"Replacing {incorrect} with {suggested}")

                # Try multiple replacement strategies
                sql_fixed = sql

                # Strategy 1: Direct replacement with context (e.g., "al.name" -> "cl.name")
                # Use word boundaries to avoid partial matches
                sql_fixed = re.sub(
                    r'\b' + re.escape(incorrect) + r'\b',
                    suggested,
                    sql_fixed
                )

                # Strategy 2: If the incorrect reference appears in an aggregate function
                # Replace patterns like: STRING_AGG(DISTINCT al.name, ...) with STRING_AGG(DISTINCT cl.name, ...)
                if sql_fixed == sql:  # If strategy 1 didn't work
                    # Extract just the column part (e.g., "name" from "al.name")
                    if '.' in incorrect:
                        incorrect_alias, incorrect_col = incorrect.split('.', 1)
                        if '.' in suggested:
                            suggested_alias, suggested_col = suggested.split('.', 1)
                            # Replace alias.column pattern
                            sql_fixed = re.sub(
                                r'\b' + re.escape(incorrect_alias) + r'\.' + re.escape(incorrect_col) + r'\b',
                                f'{suggested_alias}.{suggested_col}',
                                sql
                            )

                if sql_fixed != sql:
                    logger.info(f"Successfully fixed column reference")
                return sql_fixed

        return sql

    def _fix_group_by_error(self, sql: str, error: str) -> str:
        """
        Attempt to fix GROUP BY clause errors by adding missing columns.

        Args:
            sql: SQL query with GROUP BY error
            error: Error message from PostgreSQL

        Returns:
            Fixed SQL query (or original if can't fix)
        """
        import re

        # Error format: column "alias.column_name" must appear in the GROUP BY clause
        # Extract the missing column
        column_match = re.search(r'column "([^"]+)" must appear in the GROUP BY clause', error)
        if not column_match:
            return sql

        missing_column = column_match.group(1)
        logger.info(f"Missing column in GROUP BY: {missing_column}")

        # Find the GROUP BY clause
        group_by_match = re.search(r'GROUP BY\s+([^\n;]+)', sql, re.IGNORECASE)
        if not group_by_match:
            return sql

        current_group_by = group_by_match.group(1).strip()
        logger.info(f"Current GROUP BY: {current_group_by}")

        # Add the missing column to GROUP BY
        new_group_by = f"{current_group_by}, {missing_column}"
        sql_fixed = re.sub(
            r'GROUP BY\s+[^\n;]+',
            f'GROUP BY {new_group_by}',
            sql,
            flags=re.IGNORECASE
        )

        logger.info(f"Fixed GROUP BY clause: GROUP BY {new_group_by}")
        return sql_fixed

    def fetch_data(
        self,
        user_query: str,
        content_type: str,
        selected_college_id: Optional[int] = None,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """
        Complete workflow: analyze query, generate SQL, and fetch data.

        Args:
            user_query: User's content request
            content_type: Type of content
            selected_college_id: Optional specific college ID to filter by
            max_retries: Maximum number of times to retry query generation on failure

        Returns:
            Dictionary with SQL query and fetched data
        """
        # Step 1: Analyze query
        analysis = self.analyze_query(user_query, content_type)

        # Step 2: Generate SQL with retry mechanism
        sql_query = ""
        data = []
        last_error = None

        if analysis["relevant_tables"]:
            for retry_attempt in range(max_retries):
                try:
                    # Generate SQL query (pass previous error to help LLM learn)
                    sql_query = self.generate_sql_query(
                        user_query,
                        analysis["relevant_tables"],
                        content_type,
                        selected_college_id,
                        previous_error=last_error if retry_attempt > 0 else None
                    )

                    # Step 3: Validate query
                    if sql_query:
                        is_valid, error = self.query_generator.validate_query(sql_query)

                        # If validation failed, try to auto-fix common issues
                        if not is_valid:
                            error_lower = str(error).lower()

                            # Fix GROUP_CONCAT issue
                            if 'group_concat' in error_lower:
                                logger.warning("GROUP_CONCAT error detected, applying fix...")
                                sql_query = self._fix_postgresql_syntax(sql_query)
                                is_valid, error = self.query_generator.validate_query(sql_query)

                            # Fix GROUP BY errors
                            elif 'must appear in the group by clause' in error_lower:
                                logger.warning("GROUP BY error detected, trying to fix...")
                                original_sql = sql_query
                                # Try to fix up to 5 times (in case multiple columns are missing)
                                for attempt in range(5):
                                    sql_query = self._fix_group_by_error(sql_query, str(error))
                                    if sql_query == original_sql:
                                        # No fix applied, stop trying
                                        break
                                    is_valid, error = self.query_generator.validate_query(sql_query)
                                    if is_valid:
                                        logger.info(f"GROUP BY fixed after {attempt + 1} attempt(s)")
                                        break
                                    # Check if still a GROUP BY error
                                    if 'must appear in the group by clause' not in str(error).lower():
                                        break
                                    original_sql = sql_query

                            # Fix alias/column mismatch
                            elif 'column' in error_lower and 'does not exist' in error_lower:
                                logger.warning("Column reference error detected, trying to fix...")
                                sql_query = self._fix_column_references(sql_query, error)
                                is_valid, error = self.query_generator.validate_query(sql_query)

                        # If still invalid after auto-fix attempts
                        if not is_valid:
                            last_error = error
                            if retry_attempt < max_retries - 1:
                                logger.warning(
                                    f"Query validation failed (attempt {retry_attempt + 1}/{max_retries}). "
                                    f"Regenerating query... Error: {error}"
                                )
                                continue  # Retry with new query generation
                            else:
                                logger.error(f"Query validation failed after {max_retries} attempts: {error}")
                                sql_query = f"-- INVALID QUERY\n-- Error: {error}\n{sql_query}"
                                break
                        else:
                            # Query is valid, execute it
                            data = self.query_generator.execute_query(sql_query)
                            logger.info(f"Data fetched successfully: {len(data)} rows (attempt {retry_attempt + 1})")
                            break  # Success, exit retry loop

                except Exception as e:
                    last_error = str(e)
                    if retry_attempt < max_retries - 1:
                        logger.warning(
                            f"Error in query generation/execution (attempt {retry_attempt + 1}/{max_retries}): {e}. "
                            "Retrying..."
                        )
                        continue
                    else:
                        logger.error(f"Error after {max_retries} attempts: {e}")
                        sql_query = f"-- EXECUTION ERROR\n-- Error: {e}\n{sql_query if sql_query else 'No query generated'}"
                        break

        return {
            "analysis": analysis["analysis"],
            "keywords": analysis["keywords"],
            "relevant_tables": analysis["relevant_tables"],
            "sql_query": sql_query,
            "data": data,
            "row_count": len(data)
        }

    def _extract_keywords(self, analysis_text: str) -> List[str]:
        """
        Extract keywords from analysis text.

        Args:
            analysis_text: Analysis response from LLM

        Returns:
            List of keywords
        """
        # Simple keyword extraction from analysis
        # Look for common patterns in the response
        keywords = []
        lines = analysis_text.lower().split('\n')

        for line in lines:
            if 'keyword' in line or 'topic' in line:
                # Extract words that might be keywords
                words = line.split(':')[-1].strip()
                keywords.extend([w.strip(' ,-') for w in words.split() if len(w) > 3])

        # Add some common college-related keywords if none found
        if not keywords:
            keywords = ['college', 'degree', 'ranking', 'fee', 'admission']

        return list(set(keywords))[:10]  # Return unique keywords, max 10
