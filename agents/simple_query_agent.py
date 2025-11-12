"""Simplified query agent using materialized view for college data."""

import logging
from typing import Dict, Any, List, Optional
from models.llm_interface import BaseLLM
from database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class SimpleQueryAgent:
    """Simplified agent that uses mvx_college_data_flattened materialized view."""

    def __init__(self, llm: BaseLLM, db: DatabaseConnection):
        """
        Initialize simple query agent.

        Args:
            llm: LLM instance
            db: Database connection instance
        """
        self.llm = llm
        self.db = db

    def fetch_college_data(
        self,
        user_query: str,
        content_type: str,
        selected_college_id: Optional[int] = None,
        selected_college_ids: Optional[List[int]] = None,
        selected_fields: Optional[List[str]] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch college data from materialized view.

        Args:
            user_query: User's content request
            content_type: Type of content
            selected_college_id: Optional specific college ID to filter by
            selected_college_ids: Optional list of college IDs (for comparison)
            selected_fields: Optional list of specific fields to fetch (None = all fields)
            limit: Maximum number of colleges to fetch

        Returns:
            Dictionary with SQL query and fetched data
        """
        try:
            # Determine which fields to select
            if selected_fields:
                # Ensure essential fields are always included
                essential_fields = ['college_id', 'name', 'city', 'state']
                all_fields = list(set(essential_fields + selected_fields))
                field_list = ', '.join(all_fields)
                logger.info(f"Using custom field selection: {len(all_fields)} fields")
            else:
                field_list = '*'
                logger.info("Using all fields")

            # Build simple query using materialized view
            if selected_college_ids and len(selected_college_ids) > 0:
                # Fetch multiple specific colleges (for comparison)
                id_list = ','.join(map(str, selected_college_ids))
                sql_query = f"""
                    SELECT {field_list}
                    FROM mvx_college_data_flattened
                    WHERE college_id IN ({id_list})
                        AND college_is_active = true
                    ORDER BY college_id;
                """
                logger.info(f"Fetching {len(selected_college_ids)} colleges for comparison: {selected_college_ids}")
            elif selected_college_id:
                # Fetch single specific college
                sql_query = f"""
                    SELECT {field_list}
                    FROM mvx_college_data_flattened
                    WHERE college_id = {selected_college_id}
                        AND college_is_active = true
                    LIMIT 1;
                """
                logger.info(f"Fetching data for college_id={selected_college_id}")
            else:
                # Fetch multiple colleges based on query context
                filters = self._extract_filters_from_query(user_query)

                where_clauses = ["college_is_active = true"]

                if filters.get('city'):
                    where_clauses.append(f"LOWER(city) = LOWER('{filters['city']}')")
                if filters.get('state'):
                    where_clauses.append(f"LOWER(state) = LOWER('{filters['state']}')")

                where_clause = " AND ".join(where_clauses)

                sql_query = f"""
                    SELECT {field_list}
                    FROM mvx_college_data_flattened
                    WHERE {where_clause}
                    ORDER BY year_of_established DESC NULLS LAST
                    LIMIT {limit};
                """
                logger.info(f"Fetching colleges with filters: {filters}")

            # Execute query
            data = self.db.execute_query(sql_query)

            logger.info(f"Data fetched successfully: {len(data)} rows")

            return {
                "analysis": f"Fetching college data based on: {user_query}",
                "keywords": self._extract_keywords(user_query),
                "relevant_tables": ["mvx_college_data_flattened"],
                "sql_query": sql_query,
                "data": data,
                "row_count": len(data)
            }

        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return {
                "analysis": "",
                "keywords": [],
                "relevant_tables": [],
                "sql_query": f"-- ERROR: {e}",
                "data": [],
                "row_count": 0
            }

    def _extract_filters_from_query(self, user_query: str) -> Dict[str, str]:
        """
        Extract simple filters from user query.

        Args:
            user_query: User's natural language query

        Returns:
            Dictionary of filters
        """
        filters = {}
        query_lower = user_query.lower()

        # Common Indian cities
        cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 'hyderabad',
                  'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur',
                  'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri', 'patna',
                  'vadodara', 'ghaziabad', 'ludhiana', 'agra', 'nashik', 'faridabad',
                  'meerut', 'rajkot', 'kalyan', 'vasai', 'varanasi', 'srinagar']

        for city in cities:
            if city in query_lower:
                filters['city'] = city.title()
                break

        # Common Indian states
        states = ['maharashtra', 'karnataka', 'tamil nadu', 'delhi', 'west bengal',
                  'telangana', 'gujarat', 'rajasthan', 'uttar pradesh', 'madhya pradesh',
                  'bihar', 'andhra pradesh', 'kerala', 'punjab', 'haryana', 'odisha',
                  'jharkhand', 'assam', 'chhattisgarh', 'uttarakhand', 'himachal pradesh',
                  'goa', 'jammu and kashmir', 'manipur', 'meghalaya', 'nagaland',
                  'sikkim', 'tripura', 'arunachal pradesh', 'mizoram']

        for state in states:
            if state in query_lower:
                filters['state'] = state.title()
                break

        return filters

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query.

        Args:
            query: User query

        Returns:
            List of keywords
        """
        # Simple keyword extraction
        keywords = []
        query_lower = query.lower()

        if 'engineering' in query_lower or 'iit' in query_lower or 'nit' in query_lower:
            keywords.append('engineering')
        if 'medical' in query_lower or 'mbbs' in query_lower or 'aiims' in query_lower:
            keywords.append('medical')
        if 'law' in query_lower or 'nliu' in query_lower:
            keywords.append('law')
        if 'management' in query_lower or 'mba' in query_lower or 'iim' in query_lower:
            keywords.append('management')
        if 'ranking' in query_lower or 'nirf' in query_lower:
            keywords.append('ranking')
        if 'fee' in query_lower or 'cost' in query_lower or 'tuition' in query_lower:
            keywords.append('fees')
        if 'admission' in query_lower or 'entrance' in query_lower:
            keywords.append('admission')

        return keywords if keywords else ['college', 'education']

    def get_college_by_id(self, college_id: int) -> Optional[Dict[str, Any]]:
        """
        Get full college data by ID.

        Args:
            college_id: College ID

        Returns:
            College data dictionary or None
        """
        try:
            sql_query = f"""
                SELECT *
                FROM mvx_college_data_flattened
                WHERE college_id = {college_id}
                    AND college_is_active = true;
            """

            data = self.db.execute_query(sql_query)

            if data:
                logger.info(f"Retrieved college data for ID {college_id}")
                return data[0]
            else:
                logger.warning(f"No college found with ID {college_id}")
                return None

        except Exception as e:
            logger.error(f"Error fetching college by ID: {e}")
            return None

    def search_colleges(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search colleges by name, city, or state.

        Args:
            search_term: Search term
            limit: Maximum results

        Returns:
            List of matching colleges
        """
        try:
            sql_query = f"""
                SELECT
                    college_id,
                    name,
                    city,
                    state,
                    year_of_established,
                    website
                FROM mvx_college_data_flattened
                WHERE college_is_active = true
                    AND (
                        LOWER(name) LIKE LOWER('%{search_term}%')
                        OR LOWER(city) LIKE LOWER('%{search_term}%')
                        OR LOWER(state) LIKE LOWER('%{search_term}%')
                    )
                ORDER BY name
                LIMIT {limit};
            """

            data = self.db.execute_query(sql_query)
            logger.info(f"Found {len(data)} colleges matching '{search_term}'")
            return data

        except Exception as e:
            logger.error(f"Error searching colleges: {e}")
            return []

    def get_available_fields(self) -> List[Dict[str, str]]:
        """
        Get list of available fields in mvx_college_data_flattened view.

        Returns:
            List of dictionaries with column_name, data_type
        """
        try:
            schema = self.db.get_table_schema('mvx_college_data_flattened')
            logger.info(f"Retrieved {len(schema)} fields from schema")
            return schema
        except Exception as e:
            logger.error(f"Error fetching schema: {e}")
            # Return common fields as fallback
            return [
                {'column_name': 'college_id', 'data_type': 'integer'},
                {'column_name': 'name', 'data_type': 'text'},
                {'column_name': 'city', 'data_type': 'text'},
                {'column_name': 'state', 'data_type': 'text'},
                {'column_name': 'year_of_established', 'data_type': 'integer'},
                {'column_name': 'website', 'data_type': 'text'},
                {'column_name': 'rankings', 'data_type': 'jsonb'},
                {'column_name': 'accreditations', 'data_type': 'jsonb'},
                {'column_name': 'degrees', 'data_type': 'jsonb'},
                {'column_name': 'infrastructure', 'data_type': 'jsonb'},
            ]

    def get_field_groups(self) -> Dict[str, List[str]]:
        """
        Get predefined field groups for easy selection.

        Returns:
            Dictionary mapping group names to field lists
        """
        return {
            'Basic Info': [
                'college_id', 'name', 'city', 'state', 'district',
                'year_of_established', 'website', 'college_is_active',
                'is_college_verified', 'alternative_names'
            ],
            'Rankings & Accreditation': [
                'rankings', 'accreditations'
            ],
            'Academics & Programs': [
                'degrees', 'fees', 'faculty_ratio'
            ],
            'Infrastructure & Facilities': [
                'infrastructure', 'nearby_places', 'utilities'
            ],
            'Outcomes & Placement': [
                'placements', 'alumni'
            ],
            'Contact & Location': [
                'contact_info', 'address', 'city', 'state', 'district'
            ]
        }
