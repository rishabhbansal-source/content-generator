"""Topic agent for generating content topics based on college data."""

import logging
from typing import List, Dict, Any
from models.llm_interface import BaseLLM
from utils.content_types import get_content_type_metadata

logger = logging.getLogger(__name__)


class TopicAgent:
    """Agent for generating relevant content topics."""

    def __init__(self, llm: BaseLLM):
        """
        Initialize topic agent.

        Args:
            llm: LLM instance
        """
        self.llm = llm

    def generate_topics(
        self,
        college_data_summary: str,
        content_type: str,
        num_topics: int = 8
    ) -> List[Dict[str, str]]:
        """
        Generate topic suggestions based on college data.

        Args:
            college_data_summary: Summary of college data available
            content_type: Type of content to generate
            num_topics: Number of topics to generate

        Returns:
            List of topic dictionaries with title and description
        """
        metadata = get_content_type_metadata(content_type)

        system_prompt = f"""You are an expert content strategist specializing in higher education and college-related content.

Your task is to generate {num_topics} diverse and engaging topic ideas for content creation.

Each topic should:
1. Be specific and focused
2. Align with the content type: {metadata.name}
3. Be relevant to students, parents, and education seekers
4. Make use of available college data
5. Be SEO-friendly and engaging
6. Cover different aspects (admissions, rankings, facilities, placements, student life, etc.)

Tone: {metadata.tone}
Ideal Length: {metadata.ideal_length}"""

        prompt = f"""Based on the following college data, generate {num_topics} compelling topic ideas for {content_type} content:

Available Data Summary:
{college_data_summary}

Generate topics that cover diverse aspects such as:
- Academic programs and rankings
- Admission process and eligibility
- Infrastructure and facilities
- Placements and career outcomes
- Student life and campus culture
- Fees structure and scholarships
- Location advantages
- Comparison with peer institutions

IMPORTANT: Format each topic EXACTLY like this:

1.
Topic: [Your specific topic title]
Focus: [Brief description of what this topic covers]

2.
Topic: [Your specific topic title]
Focus: [Brief description of what this topic covers]

Generate all {num_topics} topics now:"""

        try:
            response = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # Higher temperature for creativity
                max_tokens=2000
            )

            # Parse the response into structured topics
            topics = self._parse_topics(response)

            # If parsing failed, use default topics
            if len(topics) == 0:
                logger.warning("Parsing returned 0 topics, using defaults")
                return self._get_default_topics(content_type)

            logger.info(f"Generated {len(topics)} topic ideas")
            return topics

        except Exception as e:
            logger.error(f"Error generating topics: {e}")
            # Return default topics if generation fails
            return self._get_default_topics(content_type)

    def _parse_topics(self, response: str) -> List[Dict[str, str]]:
        """
        Parse LLM response into structured topics.

        Args:
            response: LLM response text

        Returns:
            List of topic dictionaries
        """
        import re

        logger.debug(f"Parsing topics from response (length: {len(response)})")
        logger.debug(f"Response preview:\n{response[:500]}")

        topics = []
        current_topic = {}
        lines = response.split('\n')

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Check for numbered topics (e.g., "1.", "2.", etc.) - must be standalone
            if re.match(r'^\d+\.\s*$', line):
                # Save previous topic if exists
                if current_topic and 'topic' in current_topic:
                    topics.append(current_topic)
                    logger.debug(f"Added topic: {current_topic.get('topic', 'No topic')}")
                current_topic = {}
                continue

            # Extract topic (case insensitive, flexible formatting)
            topic_match = re.match(r'^topic\s*:\s*(.+)', line, re.IGNORECASE)
            if topic_match:
                topic = topic_match.group(1).strip()
                current_topic['topic'] = topic
                logger.debug(f"Found topic: {topic}")
                continue

            # Extract focus (case insensitive, flexible formatting)
            focus_match = re.match(r'^focus\s*:\s*(.+)', line, re.IGNORECASE)
            if focus_match:
                focus = focus_match.group(1).strip()
                current_topic['focus'] = focus
                logger.debug(f"Found focus: {focus[:50]}...")
                continue

            # Append multi-line focus (if we already have focus and line doesn't start with topic/focus)
            if current_topic and 'focus' in current_topic:
                if not re.match(r'^(topic|focus)\s*:', line, re.IGNORECASE):
                    current_topic['focus'] += ' ' + line

        # Add last topic
        if current_topic and 'topic' in current_topic:
            topics.append(current_topic)
            logger.debug(f"Added final topic: {current_topic.get('topic', 'No topic')}")

        # Clean up and ensure all topics have required fields
        cleaned_topics = []
        for i, t in enumerate(topics, 1):
            cleaned_topics.append({
                "topic": t.get('topic', f"Topic {i}"),
                "focus": t.get('focus', 'General overview of college information')
            })

        logger.info(f"Successfully parsed {len(cleaned_topics)} topics")

        # If parsing failed completely, log the full response for debugging
        if len(cleaned_topics) == 0:
            logger.warning("No topics were parsed! Full response:")
            logger.warning(response)

        return cleaned_topics

    def _get_default_topics(self, content_type: str) -> List[Dict[str, str]]:
        """
        Get default topic suggestions as fallback.

        Args:
            content_type: Type of content

        Returns:
            List of default topics
        """
        return [
            {
                "topic": "Complete Admission Guide",
                "focus": "Step-by-step guide covering eligibility, entrance exams, application process, and important dates"
            },
            {
                "topic": "Rankings and Accreditations Analysis",
                "focus": "Detailed breakdown of NIRF rankings, NAAC grades, and other quality certifications"
            },
            {
                "topic": "Campus Infrastructure and Facilities",
                "focus": "Comprehensive overview of labs, libraries, hostels, sports facilities, and amenities"
            },
            {
                "topic": "Placement Records and Career Opportunities",
                "focus": "Analysis of placement statistics, top recruiters, salary packages, and industry connections"
            },
            {
                "topic": "Fees Structure and Scholarship Options",
                "focus": "Complete breakdown of tuition fees, additional costs, and available financial aid"
            },
            {
                "topic": "Student Life and Campus Culture",
                "focus": "Insights into clubs, events, extracurricular activities, and student experiences"
            },
            {
                "topic": "Academic Programs and Specializations",
                "focus": "Overview of degree programs, courses offered, faculty expertise, and unique features"
            },
            {
                "topic": "Location Advantages and Connectivity",
                "focus": "Analysis of location benefits, nearby facilities, transportation, and accessibility"
            }
        ]

    def refine_topic(
        self,
        selected_topic: Dict[str, str],
        user_input: str
    ) -> Dict[str, str]:
        """
        Refine a topic based on user input.

        Args:
            selected_topic: The topic selected by user
            user_input: User's custom input or modifications

        Returns:
            Refined topic
        """
        system_prompt = """You are a content strategy expert. Refine the topic based on user input."""

        prompt = f"""Refine this content topic based on user modifications:

Original Topic:
Topic: {selected_topic['topic']}
Focus: {selected_topic['focus']}

User Input/Modifications:
{user_input}

Provide the refined topic with updated title and focus area."""

        try:
            response = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7
            )

            # Parse refined topic
            refined = self._parse_topics(response)

            if refined:
                return refined[0]
            else:
                return selected_topic

        except Exception as e:
            logger.error(f"Error refining topic: {e}")
            return selected_topic
