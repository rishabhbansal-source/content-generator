"""
Keyword Parser Utility

Handles parsing keywords from multiple sources:
- CSV files
- TXT files
- Manual text input
"""

import logging
from typing import List, Optional
import io
import csv

logger = logging.getLogger(__name__)


class KeywordParser:
    """Parse keywords from various input formats"""

    @staticmethod
    def parse_csv(file_content: bytes, column_name: Optional[str] = None) -> List[str]:
        """
        Parse keywords from CSV file

        Args:
            file_content: Raw bytes from uploaded CSV file
            column_name: Name of column containing keywords (if None, uses first column)

        Returns:
            List of keywords (cleaned and deduplicated)
        """
        try:
            # Decode bytes to string
            content_str = file_content.decode('utf-8')

            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(content_str))
            keywords = []

            for row in csv_reader:
                if column_name and column_name in row:
                    keyword = row[column_name].strip()
                else:
                    # Use first column
                    keyword = list(row.values())[0].strip()

                if keyword:
                    keywords.append(keyword)

            logger.info(f"Parsed {len(keywords)} keywords from CSV")
            return KeywordParser._clean_keywords(keywords)

        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            return []

    @staticmethod
    def parse_txt(file_content: bytes, delimiter: str = '\n') -> List[str]:
        """
        Parse keywords from TXT file

        Args:
            file_content: Raw bytes from uploaded TXT file
            delimiter: Delimiter to split keywords (default: newline)

        Returns:
            List of keywords (cleaned and deduplicated)
        """
        try:
            # Decode bytes to string
            content_str = file_content.decode('utf-8')

            # Split by delimiter
            keywords = content_str.split(delimiter)

            # Also try comma if newline doesn't work well
            if len(keywords) == 1 and ',' in keywords[0]:
                keywords = keywords[0].split(',')

            logger.info(f"Parsed {len(keywords)} keywords from TXT")
            return KeywordParser._clean_keywords(keywords)

        except Exception as e:
            logger.error(f"Error parsing TXT: {str(e)}")
            return []

    @staticmethod
    def parse_manual_input(text: str) -> List[str]:
        """
        Parse keywords from manual text input

        Args:
            text: Comma-separated or newline-separated keywords

        Returns:
            List of keywords (cleaned and deduplicated)
        """
        try:
            # Try splitting by comma first
            if ',' in text:
                keywords = text.split(',')
            else:
                # Fall back to newline
                keywords = text.split('\n')

            logger.info(f"Parsed {len(keywords)} keywords from manual input")
            return KeywordParser._clean_keywords(keywords)

        except Exception as e:
            logger.error(f"Error parsing manual input: {str(e)}")
            return []

    @staticmethod
    def _clean_keywords(keywords: List[str]) -> List[str]:
        """
        Clean and deduplicate keywords

        Args:
            keywords: Raw list of keywords

        Returns:
            Cleaned list of unique keywords
        """
        # Strip whitespace
        cleaned = [k.strip() for k in keywords]

        # Remove empty strings
        cleaned = [k for k in cleaned if k]

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for k in cleaned:
            k_lower = k.lower()
            if k_lower not in seen:
                seen.add(k_lower)
                unique.append(k)

        logger.info(f"Cleaned keywords: {len(keywords)} -> {len(unique)}")
        return unique

    @staticmethod
    def format_keywords_for_prompt(keywords: List[str], max_keywords: int = 20) -> str:
        """
        Format keywords for inclusion in LLM prompt

        Args:
            keywords: List of keywords
            max_keywords: Maximum number of keywords to include (to avoid token limits)

        Returns:
            Formatted string for prompt
        """
        if not keywords:
            return ""

        # Limit number of keywords
        limited = keywords[:max_keywords]

        if len(keywords) > max_keywords:
            logger.warning(f"Limited keywords from {len(keywords)} to {max_keywords}")

        # Format as bullet list
        formatted = "Target Keywords (integrate naturally for SEO):\n"
        for kw in limited:
            formatted += f"- {kw}\n"

        return formatted
