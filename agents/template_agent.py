"""Template agent for creating content structure and outlines."""

import logging
from typing import Dict, Any, List
from models.llm_interface import BaseLLM
from utils.content_types import get_content_type_metadata

logger = logging.getLogger(__name__)


class TemplateAgent:
    """Agent for generating content templates and outlines."""

    def __init__(self, llm: BaseLLM):
        """
        Initialize template agent.

        Args:
            llm: LLM instance
        """
        self.llm = llm

    def generate_template(
        self,
        content_prompt: Dict[str, str],
        content_type: str,
        data_summary: str,
        serp_context: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a content template/outline.

        Args:
            content_prompt: Selected content prompt
            content_type: Type of content
            data_summary: Summary of available data
            serp_context: Context from SerpAPI (optional)

        Returns:
            Template structure with sections and bullet points
        """
        metadata = get_content_type_metadata(content_type)

        system_prompt = f"""You are a content strategist creating detailed content outlines for Indian higher education content.

Create a comprehensive outline that:
1. Follows the {metadata.name} format
2. Includes clear section headings
3. Lists key points for each section
4. Incorporates available data effectively
5. Maintains the tone: {metadata.tone}
6. Targets length: {metadata.ideal_length}

INDIAN CONTEXT REQUIREMENTS:
- Use Indian English style (lakhs/crores, not hundreds of thousands/millions)
- Target Indian students, parents, and education seekers
- Reference Indian education system (CBSE, ICSE, JEE, NEET, CAT, CLAT)
- Use Indian accreditation bodies (UGC, AICTE, NAAC, NIRF)
- Include Indian-specific sections (reservation categories, domicile requirements, state quota)
- Use Indian terminology and local context

CRITICAL DATA USAGE RULES:
- ALWAYS use ACTUAL college names from the data provided
- NEVER use placeholder names like "College X", "College Y", "College Z", "College A", "College B"
- Extract real college names from the data summary and use them in section headings and outline
- For comparison outlines, use actual college names in comparison table headers"""

        # Build trends section separately to avoid f-string backslash issue
        trends_section = ""
        if serp_context:
            trends_section = f"Current Trends/Context:\n{serp_context}\n\n"
        
        prompt = f"""Create a detailed content outline for this topic:

Title: {content_prompt['title']}
Angle: {content_prompt['angle']}
Description: {content_prompt['description']}

Content Type: {content_type}
Typical Sections: {', '.join(metadata.typical_sections)}

Available Data:
{data_summary}

{trends_section}IMPORTANT: Use ACTUAL college names from the "Available Data" section above. Never use "College X/Y/Z" or "College A/B/C".

Create a detailed outline with:
- Main sections/headings (use actual college names in headings)
- Sub-sections
- Key points to cover in each section (use bullet points, not long paragraphs)
- Suggested data to include (specify where tables/comparisons should be used)
- For comparison content, specify actual college names in table headers

FORMATTING REQUIREMENTS:
- Prefer bullet points and numbered lists over paragraphs
- Identify sections where tables would be useful (fees, rankings, placements, comparisons)
- Keep paragraphs to minimum (max 2-3 per section)
- Structure data in organized formats

FORMAT GUIDANCE:
- For rankings/comparisons: Use tables
- For features/benefits: Use bullet points
- For steps/processes: Use numbered lists
- For data/statistics: Use tables or structured lists

Format the outline clearly with hierarchical structure."""

        try:
            response = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.6
            )

            # Parse the outline
            template = self._parse_outline(response)

            template.update({
                "title": content_prompt['title'],
                "content_type": content_type,
                "metadata": {
                    "ideal_length": metadata.ideal_length,
                    "tone": metadata.tone
                },
                "raw_outline": response
            })

            logger.info("Template generated successfully")
            return template

        except Exception as e:
            logger.error(f"Error generating template: {e}")
            return {
                "title": content_prompt['title'],
                "sections": [],
                "raw_outline": "",
                "content_type": content_type
            }

    def _parse_outline(self, outline_text: str) -> Dict[str, Any]:
        """
        Parse outline text into structured format.

        Args:
            outline_text: Outline text from LLM

        Returns:
            Structured outline
        """
        sections = []
        current_section = None
        current_subsection = None

        lines = outline_text.split('\n')

        for line in lines:
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # Detect main sections (usually start with numbers or ##)
            if (line_stripped[0].isdigit() and '.' in line_stripped[:3]) or line_stripped.startswith('##'):
                if current_section:
                    sections.append(current_section)

                # Extract section title
                section_title = line_stripped.lstrip('#0123456789. ').strip()
                current_section = {
                    "title": section_title,
                    "subsections": [],
                    "points": []
                }
                current_subsection = None

            # Detect subsections
            elif line_stripped.startswith('-') and line_stripped[1:].strip()[0].isupper():
                subsection_title = line_stripped.lstrip('- ').strip()
                current_subsection = {
                    "title": subsection_title,
                    "points": []
                }
                if current_section:
                    current_section["subsections"].append(current_subsection)

            # Detect bullet points
            elif line_stripped.startswith('-') or line_stripped.startswith('*') or line_stripped.startswith('•'):
                point = line_stripped.lstrip('-*• ').strip()

                if current_subsection:
                    current_subsection["points"].append(point)
                elif current_section:
                    current_section["points"].append(point)

        # Add last section
        if current_section:
            sections.append(current_section)

        return {"sections": sections}

    def refine_template(
        self,
        template: Dict[str, Any],
        user_feedback: str
    ) -> Dict[str, Any]:
        """
        Refine template based on user feedback.

        Args:
            template: Current template
            user_feedback: User's requested changes

        Returns:
            Refined template
        """
        system_prompt = """You are a content strategist. Refine the content outline based on user feedback while maintaining structure and quality."""

        # Reconstruct outline text for context
        outline_text = template.get('raw_outline', '')

        prompt = f"""Refine this content outline based on user feedback:

Current Outline:
{outline_text}

User Feedback:
{user_feedback}

Provide the refined outline with requested changes."""

        try:
            response = self.llm.generate(prompt, system_prompt=system_prompt)

            refined_template = self._parse_outline(response)
            refined_template.update({
                "title": template.get('title', ''),
                "content_type": template.get('content_type', ''),
                "metadata": template.get('metadata', {}),
                "raw_outline": response
            })

            logger.info("Template refined successfully")
            return refined_template

        except Exception as e:
            logger.error(f"Error refining template: {e}")
            return template

    def get_template_summary(self, template: Dict[str, Any]) -> str:
        """
        Get a human-readable summary of the template.

        Args:
            template: Template structure

        Returns:
            Summary string
        """
        summary = f"# {template.get('title', 'Content Outline')}\n\n"
        summary += f"**Content Type:** {template.get('content_type', 'N/A')}\n\n"

        metadata = template.get('metadata', {})
        if metadata:
            summary += f"**Target Length:** {metadata.get('ideal_length', 'N/A')}\n"
            summary += f"**Tone:** {metadata.get('tone', 'N/A')}\n\n"

        summary += "## Outline:\n\n"

        for i, section in enumerate(template.get('sections', []), 1):
            summary += f"{i}. **{section['title']}**\n"

            if section.get('points'):
                for point in section['points']:
                    summary += f"   - {point}\n"

            if section.get('subsections'):
                for subsection in section['subsections']:
                    summary += f"   - {subsection['title']}\n"
                    for point in subsection.get('points', []):
                        summary += f"     • {point}\n"

            summary += "\n"

        return summary
