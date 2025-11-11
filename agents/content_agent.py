"""Content agent for generating final markdown content."""

import logging
from typing import Dict, Any, Optional
from models.llm_interface import BaseLLM
from utils.content_types import get_content_type_metadata

logger = logging.getLogger(__name__)


class ContentAgent:
    """Agent for generating final content."""

    def __init__(self, llm: BaseLLM):
        """
        Initialize content agent.

        Args:
            llm: LLM instance
        """
        self.llm = llm

    def generate_content(
        self,
        template: Dict[str, Any],
        data: str,
        serp_context: str = "",
        additional_instructions: str = ""
    ) -> str:
        """
        Generate complete content based on template and data.

        Args:
            template: Content template/outline
            data: Available data (formatted string)
            serp_context: Context from SerpAPI
            additional_instructions: Any additional instructions

        Returns:
            Generated markdown content
        """
        content_type = template.get('content_type', '')
        metadata = get_content_type_metadata(content_type)

        system_prompt = f"""You are an expert content writer specializing in educational and college-related content.

Your writing should:
1. Be informative, accurate, and well-researched
2. Follow the {metadata.name} format
3. Maintain a {metadata.tone} tone
4. Target length: {metadata.ideal_length}
5. Use proper markdown formatting
6. Include relevant data and statistics
7. Be engaging and reader-friendly
8. Use SEO-friendly headings and structure

Format:
- Use # for main title
- Use ## for main sections
- Use ### for subsections
- Use bullet points and numbered lists where appropriate
- Use bold and italic for emphasis
- Include relevant data in tables when appropriate"""

        # Create outline text from template
        outline_text = self._create_outline_text(template)

        # Build optional sections separately to avoid f-string backslash issue
        trends_section = ""
        if serp_context:
            trends_section = f"Current Context/Trends:\n{serp_context}\n\n"
        
        instructions_section = ""
        if additional_instructions:
            instructions_section = f"Additional Instructions:\n{additional_instructions}\n\n"

        prompt = f"""Write comprehensive content following this outline:

# {template.get('title', 'Content')}

Outline:
{outline_text}

Available Data to Incorporate:
{data}

{trends_section}{instructions_section}Generate the complete content in markdown format. Make it comprehensive, informative, and engaging.
Include relevant data, examples, and insights throughout the content.

Content:"""

        try:
            content = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4000
            )

            logger.info("Content generated successfully")
            return content.strip()

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"# {template.get('title', 'Error')}\n\nError generating content: {str(e)}"

    def generate_section(
        self,
        section_title: str,
        section_outline: str,
        data: str,
        context: str = ""
    ) -> str:
        """
        Generate content for a specific section.

        Args:
            section_title: Title of the section
            section_outline: Outline/bullet points for the section
            data: Available data
            context: Additional context

        Returns:
            Generated section content
        """
        system_prompt = """You are an expert content writer. Generate detailed, informative content for a specific section."""

        # Build context section separately to avoid f-string backslash issue
        context_section = ""
        if context:
            context_section = f"Context:\n{context}\n\n"

        prompt = f"""Write detailed content for this section:

Section Title: {section_title}

Section Outline:
{section_outline}

Available Data:
{data}

{context_section}Generate comprehensive content for this section in markdown format.
Use appropriate sub-headings, bullet points, and formatting."""

        try:
            section_content = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )

            return section_content.strip()

        except Exception as e:
            logger.error(f"Error generating section: {e}")
            return f"## {section_title}\n\nError generating section content."

    def regenerate_content(
        self,
        original_content: str,
        regeneration_instructions: str
    ) -> str:
        """
        Regenerate content based on user feedback.

        Args:
            original_content: Original generated content
            regeneration_instructions: User's instructions for changes

        Returns:
            Regenerated content
        """
        system_prompt = """You are an expert content editor. Improve and modify content based on user feedback while maintaining quality and structure."""

        prompt = f"""Modify this content based on user feedback:

Original Content:
{original_content}

User Feedback/Instructions:
{regeneration_instructions}

Generate the improved content in markdown format."""

        try:
            new_content = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4000
            )

            logger.info("Content regenerated successfully")
            return new_content.strip()

        except Exception as e:
            logger.error(f"Error regenerating content: {e}")
            return original_content

    def expand_section(
        self,
        section_content: str,
        expansion_instructions: str = "Make this section more detailed and comprehensive"
    ) -> str:
        """
        Expand a specific section of content.

        Args:
            section_content: Current section content
            expansion_instructions: How to expand

        Returns:
            Expanded section content
        """
        system_prompt = """You are an expert content writer. Expand content sections with more detail, examples, and insights."""

        prompt = f"""Expand this content section:

Current Content:
{section_content}

Instructions:
{expansion_instructions}

Generate the expanded version with more detail, examples, and insights."""

        try:
            expanded = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )

            return expanded.strip()

        except Exception as e:
            logger.error(f"Error expanding section: {e}")
            return section_content

    def _create_outline_text(self, template: Dict[str, Any]) -> str:
        """
        Create outline text from template structure.

        Args:
            template: Template dictionary

        Returns:
            Formatted outline text
        """
        outline = ""

        for section in template.get('sections', []):
            outline += f"\n## {section['title']}\n"

            for point in section.get('points', []):
                outline += f"- {point}\n"

            for subsection in section.get('subsections', []):
                outline += f"\n### {subsection['title']}\n"
                for point in subsection.get('points', []):
                    outline += f"- {point}\n"

        return outline.strip()

    def add_seo_elements(self, content: str, keywords: list) -> str:
        """
        Enhance content with SEO elements.

        Args:
            content: Original content
            keywords: Target keywords

        Returns:
            SEO-enhanced content
        """
        system_prompt = """You are an SEO content specialist. Enhance content with SEO best practices while maintaining readability and quality."""

        prompt = f"""Enhance this content with SEO best practices:

Original Content:
{content}

Target Keywords: {', '.join(keywords)}

Add:
1. Natural keyword integration
2. Meta description suggestion
3. Internal linking suggestions (as comments)
4. Alt text suggestions for images (as comments)

Return the enhanced content in markdown format."""

        try:
            enhanced = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.6
            )

            return enhanced.strip()

        except Exception as e:
            logger.error(f"Error adding SEO elements: {e}")
            return content
