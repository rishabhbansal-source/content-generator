"""SerpAPI helper for fetching trends and latest information."""

import logging
from typing import List, Dict, Any, Optional
from serpapi import GoogleSearch
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class SerpAPIHelper:
    """Helper class for SerpAPI integration."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpAPI helper.

        Args:
            api_key: SerpAPI API key (uses env var if not provided)
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("SerpAPI key not provided. Trend features will be limited.")

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a Google search using SerpAPI.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        if not self.api_key:
            logger.warning("SerpAPI key not available. Returning empty results.")
            return []

        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google"
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            organic_results = results.get("organic_results", [])

            formatted_results = []
            for result in organic_results[:num_results]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0)
                })

            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results

        except Exception as e:
            logger.error(f"Error performing SerpAPI search: {e}")
            return []

    def get_trending_topics(self, base_query: str) -> List[str]:
        """
        Get trending topics related to a base query.

        Args:
            base_query: Base search query

        Returns:
            List of trending topics/related searches
        """
        if not self.api_key:
            return []

        try:
            params = {
                "q": base_query,
                "api_key": self.api_key,
                "engine": "google"
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # Extract related searches
            related_searches = results.get("related_searches", [])
            trending = [rs.get("query", "") for rs in related_searches if rs.get("query")]

            logger.info(f"Found {len(trending)} trending topics for: {base_query}")
            return trending[:10]  # Return top 10

        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            return []

    def get_news(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent news articles for a query.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of news articles
        """
        if not self.api_key:
            return []

        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "tbm": "nws",  # News search
                "num": num_results
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            news_results = results.get("news_results", [])

            formatted_news = []
            for article in news_results[:num_results]:
                formatted_news.append({
                    "title": article.get("title", ""),
                    "link": article.get("link", ""),
                    "snippet": article.get("snippet", ""),
                    "source": article.get("source", ""),
                    "date": article.get("date", "")
                })

            logger.info(f"Found {len(formatted_news)} news articles for: {query}")
            return formatted_news

        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []

    def get_context_for_llm(
        self,
        query: str,
        include_trends: bool = True,
        include_news: bool = True
    ) -> str:
        """
        Get formatted context for LLM from search results.

        Args:
            query: Search query
            include_trends: Include trending topics
            include_news: Include recent news

        Returns:
            Formatted context string
        """
        context = f"Current Information for: {query}\n\n"

        # Get search results
        search_results = self.search(query, num_results=3)
        if search_results:
            context += "Recent Web Results:\n"
            for i, result in enumerate(search_results, 1):
                context += f"{i}. {result['title']}\n"
                context += f"   {result['snippet']}\n\n"

        # Get trending topics
        if include_trends:
            trending = self.get_trending_topics(query)
            if trending:
                context += "Related Trending Topics:\n"
                for topic in trending[:5]:
                    context += f"- {topic}\n"
                context += "\n"

        # Get news
        if include_news:
            news = self.get_news(query, num_results=3)
            if news:
                context += "Recent News:\n"
                for i, article in enumerate(news, 1):
                    context += f"{i}. {article['title']} ({article.get('date', 'N/A')})\n"
                    context += f"   {article['snippet']}\n\n"

        return context

    def test_connection(self) -> bool:
        """
        Test SerpAPI connection.

        Returns:
            True if connection is successful
        """
        if not self.api_key:
            return False

        try:
            results = self.search("test", num_results=1)
            return len(results) > 0
        except Exception as e:
            logger.error(f"SerpAPI connection test failed: {e}")
            return False
