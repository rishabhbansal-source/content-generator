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

        system_prompt = f"""You are an expert content strategist specializing in Indian higher education and college-related content.

Your task is to generate {num_topics} diverse and engaging topic ideas for content creation.

CRITICAL REQUIREMENTS - Each topic MUST:
1. Be SPECIFIC to the actual college(s) data provided (use actual college names, rankings, fees, programs)
2. Reference ACTUAL data points (specific NIRF ranks, NAAC grades, fees in lakhs, placement percentages, program names)
3. Use INDIAN context: Indian English style, target Indian students/parents, reference Indian education system
4. Align with the content type: {metadata.name}
5. Be SEO-friendly with college name + specific aspect (e.g., "IIT Delhi Placements 2024")
6. Be directly answerable using the provided data

INDIAN CONTEXT:
- Use Indian English (lakhs/crores instead of hundreds of thousands/millions)
- Target Indian students and parents
- Reference Indian education boards (CBSE, ICSE, State Boards)
- Mention Indian entrance exams (JEE, NEET, CAT, CLAT, etc.)
- Use Indian accreditation bodies (UGC, AICTE, NAAC, NIRF)
- Use Indian terminology (college vs university, reservation categories, domicile)

BAD EXAMPLES (too generic, avoid these):
- "Complete Admission Guide"
- "Rankings and Accreditations"
- "Campus Infrastructure Overview"

GOOD EXAMPLES (specific, data-driven):
- "IIT Bombay NIRF Rank #1: Complete BTech Admission Guide for 2025 (JEE Advanced Cutoff, Fees ₹2.5 Lakhs)"
- "MIT Manipal vs VIT Vellore: Placement Comparison 2024 (₹8.5 LPA vs ₹7.2 LPA Average CTC)"
- "Top 5 Engineering Programs at NIT Trichy with 95%+ Placement Rate and ₹15 LPA Average Package"

Tone: {metadata.tone}
Ideal Length: {metadata.ideal_length}"""

        prompt = f"""Based on the following college data, generate {num_topics} compelling topic ideas for {content_type} content:

Available Data Summary:
{college_data_summary}

CRITICAL INSTRUCTIONS:
1. Each topic MUST include the actual college name(s) from the data above
2. Each topic MUST reference at least one specific data point (NIRF rank number, NAAC grade, fees in lakhs, placement %, program names)
3. Topics should be DIRECT and SPECIFIC, not generic - use actual numbers and facts
4. Use Indian English and Indian education context (JEE/NEET, lakhs/crores, NIRF/NAAC)
5. Topics must be directly answerable using the provided college data

Topic Focus Areas (use actual data for each):
- Academic programs: Mention specific program names, duration, seats available
- Rankings: Use actual NIRF ranks, NAAC grades from the data
- Admissions: Reference actual entrance exams (JEE, NEET), eligibility criteria, cutoffs if available
- Fees: Use actual fee amounts in lakhs from the data
- Placements: Use actual placement percentages/packages in LPA from the data
- Infrastructure: Mention specific facilities by name from the data
- Location: Use actual city/state and nearby advantages from the data

IMPORTANT: Format each topic EXACTLY like this:

1.
Topic: [College Name + Specific Aspect with Data Point]
Focus: [Brief description mentioning specific details from data]

2.
Topic: [College Name + Specific Aspect with Data Point]
Focus: [Brief description mentioning specific details from data]

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

            # Validate topics for specificity
            validated_topics = self._validate_topic_specificity(topics, college_data_summary)

            # If no valid topics, use defaults
            if len(validated_topics) == 0:
                logger.warning("No valid specific topics generated, using defaults")
                return self._get_default_topics(content_type)

            logger.info(f"Generated {len(validated_topics)} validated topic ideas")
            return validated_topics

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

    def _extract_college_names(self, college_data_summary: str) -> List[str]:
        """
        Extract college names from data summary.

        Args:
            college_data_summary: Summary of college data

        Returns:
            List of college names
        """
        import re

        names = []
        # Look for patterns like "- College Name in City, State"
        matches = re.findall(r'-\s+([^(]+?)\s+(?:in|,|\()', college_data_summary)
        for match in matches:
            name = match.strip()
            if name and len(name) > 3:  # Avoid short matches
                names.append(name)

        logger.debug(f"Extracted {len(names)} college names: {names}")
        return names

    def _validate_topic_specificity(
        self,
        topics: List[Dict[str, str]],
        college_data_summary: str
    ) -> List[Dict[str, str]]:
        """
        Validate that topics are specific and not generic.

        Args:
            topics: List of topic dictionaries
            college_data_summary: Summary of college data

        Returns:
            List of validated topics
        """
        import re

        if not topics:
            return []

        # Extract college names from data
        college_names = self._extract_college_names(college_data_summary)

        validated = []
        rejected = []

        for topic in topics:
            topic_text = topic['topic']
            topic_lower = topic_text.lower()

            # Check 1: Does topic mention at least one college name?
            mentions_college = any(
                name.lower() in topic_lower
                for name in college_names
                if len(name) > 3
            )

            # Check 2: Does topic contain numbers (rankings, fees, percentages)?
            has_numbers = bool(re.search(r'\d+', topic_text))

            # Check 3: Does topic contain Indian context keywords?
            indian_keywords = ['nirf', 'naac', 'jee', 'neet', 'cat', 'clat', 'lakh', 'crore',
                             'lpa', 'btech', 'mba', 'mbbs', 'aicte', 'ugc']
            has_indian_context = any(keyword in topic_lower for keyword in indian_keywords)

            # Topic is valid if it meets at least 2 of 3 criteria
            score = sum([mentions_college, has_numbers, has_indian_context])

            if score >= 2:
                validated.append(topic)
                logger.debug(f"✓ Validated topic (score {score}/3): {topic_text[:60]}")
            else:
                rejected.append(topic_text)
                logger.debug(f"✗ Rejected generic topic (score {score}/3): {topic_text[:60]}")

        # Log summary
        if rejected:
            logger.info(f"Rejected {len(rejected)} generic topics: {rejected[:3]}")
        logger.info(f"Validated {len(validated)}/{len(topics)} topics as specific")

        return validated

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
