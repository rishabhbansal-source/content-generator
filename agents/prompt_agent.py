"""Prompt agent for generating multiple content prompt variations."""

import logging
from typing import List, Dict, Any
from models.llm_interface import BaseLLM
from utils.content_types import get_content_type_metadata

logger = logging.getLogger(__name__)


class PromptAgent:
    """Agent for generating content prompt variations."""

    def __init__(self, llm: BaseLLM):
        """
        Initialize prompt agent.

        Args:
            llm: LLM instance
        """
        self.llm = llm

    def generate_prompts(
        self,
        user_query: str,
        content_type: str,
        data_summary: str,
        num_variations: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate multiple prompt variations for content generation.

        Args:
            user_query: Original user query
            content_type: Type of content to generate
            data_summary: Summary of available data
            num_variations: Number of prompt variations to generate

        Returns:
            List of prompts with titles and descriptions
        """
        metadata = get_content_type_metadata(content_type)

        system_prompt = f"""You are a content strategy expert specializing in educational and college-related content.

Your task is to generate {num_variations} different content prompts based on a user's request.

Each prompt should:
1. Be clear and specific
2. Align with the content type requirements
3. Make effective use of available data
4. Have a unique angle or perspective
5. Be engaging for the target audience (students, parents, education seekers)

Content Type: {metadata.name}
Typical Sections: {', '.join(metadata.typical_sections)}
Ideal Length: {metadata.ideal_length}
Tone: {metadata.tone}"""

        prompt = f"""Generate {num_variations} different content prompts for this request:

Original Request: {user_query}
Content Type: {content_type}

Available Data Summary:
{data_summary}

For each prompt variation, provide:
1. Title: A catchy, SEO-friendly title
2. Angle: The unique perspective or angle
3. Description: Brief description of what the content will cover

IMPORTANT: Format each prompt EXACTLY like this:

1.
Title: [Your catchy title here]
Angle: [Your unique angle here]
Description: [Your description here]

2.
Title: [Your catchy title here]
Angle: [Your unique angle here]
Description: [Your description here]

Generate all {num_variations} prompts now:"""

        try:
            response = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.8  # Higher temperature for creativity
            )

            # Parse the response into structured prompts
            prompts = self._parse_prompts(response)

            logger.info(f"Generated {len(prompts)} prompt variations")
            return prompts

        except Exception as e:
            logger.error(f"Error generating prompts: {e}")
            # Return a default prompt if generation fails
            return [{
                "title": "Comprehensive Guide",
                "angle": "General overview",
                "description": user_query,
                "full_prompt": user_query
            }]

    def _parse_prompts(self, response: str) -> List[Dict[str, str]]:
        """
        Parse LLM response into structured prompts.

        Args:
            response: LLM response text

        Returns:
            List of prompt dictionaries
        """
        import re

        logger.debug(f"Parsing prompts from response (length: {len(response)})")
        logger.debug(f"Response preview: {response[:200]}...")

        prompts = []
        current_prompt = {}
        lines = response.split('\n')

        for line in lines:
            line = line.strip()

            # Check for numbered prompts (e.g., "1.", "2.", "Prompt 1:", etc.)
            if line and (re.match(r'^\d+\.?\s*$', line) or line.startswith('Prompt')):
                if current_prompt and ('title' in current_prompt or 'description' in current_prompt):
                    prompts.append(current_prompt)
                    logger.debug(f"Added prompt: {current_prompt.get('title', 'No title')}")
                current_prompt = {"full_text": line}

            # Extract title (case insensitive, flexible formatting)
            elif re.match(r'^title\s*:', line, re.IGNORECASE):
                title = re.split(r'title\s*:', line, maxsplit=1, flags=re.IGNORECASE)[1].strip()
                current_prompt['title'] = title
                logger.debug(f"Found title: {title}")

            # Extract angle (case insensitive, flexible formatting)
            elif re.match(r'^angle\s*:', line, re.IGNORECASE):
                angle = re.split(r'angle\s*:', line, maxsplit=1, flags=re.IGNORECASE)[1].strip()
                current_prompt['angle'] = angle
                logger.debug(f"Found angle: {angle}")

            # Extract description (case insensitive, flexible formatting)
            elif re.match(r'^description\s*:', line, re.IGNORECASE):
                description = re.split(r'description\s*:', line, maxsplit=1, flags=re.IGNORECASE)[1].strip()
                current_prompt['description'] = description
                logger.debug(f"Found description: {description[:50]}...")

            # Append multi-line descriptions
            elif current_prompt and 'description' in current_prompt and line and not line.lower().startswith(('title', 'angle', 'description')):
                current_prompt['description'] += ' ' + line

            # Add to current prompt's full text
            elif current_prompt and line:
                current_prompt['full_text'] = current_prompt.get('full_text', '') + '\n' + line

        # Add last prompt
        if current_prompt and ('title' in current_prompt or 'description' in current_prompt):
            prompts.append(current_prompt)
            logger.debug(f"Added final prompt: {current_prompt.get('title', 'No title')}")

        # Clean up and ensure all prompts have required fields
        cleaned_prompts = []
        for i, p in enumerate(prompts, 1):
            cleaned_prompts.append({
                "title": p.get('title', f"Content Variation {i}"),
                "angle": p.get('angle', "Standard approach"),
                "description": p.get('description', p.get('full_text', 'No description provided')[:200]),
                "full_prompt": p.get('full_text', '')
            })

        logger.info(f"Successfully parsed {len(cleaned_prompts)} prompts")

        # If no prompts were parsed, log the full response for debugging
        if len(cleaned_prompts) == 0:
            logger.warning("No prompts were parsed from response!")
            logger.debug(f"Full response:\n{response}")

        return cleaned_prompts

    def refine_prompt(
        self,
        selected_prompt: Dict[str, str],
        user_modifications: str
    ) -> Dict[str, str]:
        """
        Refine a selected prompt based on user modifications.

        Args:
            selected_prompt: The prompt selected by user
            user_modifications: User's requested changes

        Returns:
            Refined prompt
        """
        system_prompt = """You are a content strategy expert. Refine the given prompt based on user feedback."""

        prompt = f"""Refine this content prompt based on user modifications:

Original Prompt:
Title: {selected_prompt['title']}
Angle: {selected_prompt['angle']}
Description: {selected_prompt['description']}

User Modifications:
{user_modifications}

Provide the refined prompt with updated title, angle, and description."""

        try:
            response = self.llm.generate(prompt, system_prompt=system_prompt)

            # Parse refined prompt
            refined = self._parse_prompts(response)

            if refined:
                return refined[0]
            else:
                return selected_prompt

        except Exception as e:
            logger.error(f"Error refining prompt: {e}")
            return selected_prompt
