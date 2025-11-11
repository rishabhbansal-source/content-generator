"""Google Gemini LLM implementation."""

from typing import Optional, List, Dict
import logging
import google.generativeai as genai
from models.llm_interface import BaseLLM
from config.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class GeminiModel(BaseLLM):
    """Google Gemini model implementation."""

    def _initialize(self):
        """Initialize Gemini client."""
        try:
            genai.configure(api_key=self.config.api_key)
            self.client = genai.GenerativeModel(self.config.get_default_model())
            logger.info(f"Gemini client initialized with model: {self.config.get_default_model()}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text from a prompt."""
        try:
            # Combine system prompt with user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            generation_config = {
                "temperature": self._get_temperature(temperature),
                "max_output_tokens": self._get_max_tokens(max_tokens),
            }

            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            # Handle response with proper error checking
            return self._extract_text_from_response(response)

        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            raise

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text with conversation history."""
        try:
            # Convert messages to Gemini format
            chat = self.client.start_chat(history=[])

            generation_config = {
                "temperature": self._get_temperature(temperature),
                "max_output_tokens": self._get_max_tokens(max_tokens),
            }

            # Process messages
            for msg in messages[:-1]:  # All but last
                role = "user" if msg["role"] in ["user", "system"] else "model"
                chat.history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

            # Send last message
            last_message = messages[-1]["content"]
            response = chat.send_message(
                last_message,
                generation_config=generation_config
            )

            # Handle response with proper error checking
            return self._extract_text_from_response(response)

        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            raise

    def test_connection(self) -> bool:
        """Test Gemini connection."""
        try:
            response = self.client.generate_content(
                "Say hello in one word",
                generation_config={"max_output_tokens": 50}  # Increased token limit
            )
            # Try to extract text to verify connection works
            text = self._extract_text_from_response(response)
            return bool(text)
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False

    def _extract_text_from_response(self, response) -> str:
        """
        Extract text from Gemini response, handling various response structures.

        Args:
            response: Gemini API response object

        Returns:
            Extracted text content
        """
        # Log response structure for debugging
        logger.debug(f"Response type: {type(response)}")
        logger.debug(f"Response attributes: {dir(response)}")

        try:
            # Try the simple text accessor first
            if hasattr(response, 'text'):
                text = response.text
                logger.debug(f"Successfully extracted text using response.text: {text[:50]}...")
                return text
        except (ValueError, AttributeError) as e:
            logger.debug(f"Simple text accessor failed: {e}")
            # If simple accessor fails, use parts
            pass

        try:
            # Try accessing parts directly
            if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                logger.debug(f"Found candidate: {candidate}")

                if hasattr(candidate, 'content') and candidate.content:
                    logger.debug(f"Found content: {candidate.content}")

                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        # Combine all text parts
                        text_parts = []
                        for i, part in enumerate(candidate.content.parts):
                            logger.debug(f"Part {i} type: {type(part)}")
                            if hasattr(part, 'text'):
                                part_text = getattr(part, 'text', None)
                                logger.debug(f"Part {i} text value: '{part_text}' (type: {type(part_text)})")
                                if part_text:  # Not None and not empty
                                    text_parts.append(part_text)
                                elif part_text == "":  # Explicitly empty string
                                    logger.debug(f"Part {i} has empty string")

                        if text_parts:
                            result = ''.join(text_parts)
                            logger.debug(f"Successfully extracted text from parts: {result[:50]}...")
                            return result
                        else:
                            logger.warning(f"Parts found ({len(candidate.content.parts)}) but no text in any part")
        except Exception as e:
            logger.error(f"Error extracting text from parts: {e}", exc_info=True)

        # Check for finish reason and try one more extraction method
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]

                # Log finish reason
                finish_reason = getattr(candidate, 'finish_reason', None)
                logger.debug(f"Finish reason: {finish_reason}")

                # Even if finish_reason indicates early stop, try to get any generated text
                if hasattr(candidate, 'content'):
                    content = candidate.content
                    # Try direct parts access without checking
                    try:
                        if content.parts:
                            for part in content.parts:
                                if hasattr(part, 'text'):
                                    # Found text! Even if partial
                                    logger.debug(f"Found partial text in parts despite finish_reason={finish_reason}")
                                    return part.text
                    except:
                        pass

                if hasattr(candidate, 'safety_ratings'):
                    logger.debug(f"Safety ratings: {candidate.safety_ratings}")
        except Exception as e:
            logger.debug(f"Error checking finish reason: {e}")

        # If all else fails, check for safety ratings or blocked content
        try:
            if hasattr(response, 'prompt_feedback'):
                feedback = response.prompt_feedback
                logger.warning(f"Prompt feedback: {feedback}")
                if hasattr(feedback, 'block_reason'):
                    raise ValueError(f"Response blocked: {feedback.block_reason}")
        except Exception as e:
            logger.debug(f"Error checking prompt feedback: {e}")

        # Last resort: return empty string or raise error
        logger.error(f"Full response object: {response}")
        raise ValueError("Unable to extract text from Gemini response. Response may be empty or blocked by safety filters.")
