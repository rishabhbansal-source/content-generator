"""Content type definitions and metadata."""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict


class ContentType(Enum):
    """Available content types for generation."""
    WEB_ARTICLE = "web_article"
    FAQ_PAGE = "faq_page"
    BLOG_POST = "blog_post"


@dataclass
class ContentTypeMetadata:
    """Metadata for content types."""
    name: str
    description: str
    typical_sections: List[str]
    ideal_length: str
    tone: str


# Content type metadata
CONTENT_TYPE_METADATA: Dict[ContentType, ContentTypeMetadata] = {
    ContentType.WEB_ARTICLE: ContentTypeMetadata(
        name="Web Article",
        description="General informational article about a topic",
        typical_sections=["Introduction", "Main Content", "Key Takeaways", "Conclusion"],
        ideal_length="1000-2000 words",
        tone="Informative, engaging"
    ),
    ContentType.FAQ_PAGE: ContentTypeMetadata(
        name="FAQ Page",
        description="Frequently Asked Questions with answers",
        typical_sections=["Question & Answer pairs", "Categories"],
        ideal_length="800-1500 words",
        tone="Clear, concise, helpful"
    ),
    ContentType.BLOG_POST: ContentTypeMetadata(
        name="Blog Post",
        description="Blog post about a topic",
        typical_sections=["Introduction", "Main Content", "Conclusion"],
        ideal_length="1000-2000 words",
        tone="Informative, engaging"
    ),
}


def get_content_type_options() -> List[str]:
    """Get list of content type names for UI selection."""
    return [ct.value for ct in ContentType]


def get_content_type_display_names() -> Dict[str, str]:
    """Get mapping of content type values to display names."""
    return {
        ct.value: CONTENT_TYPE_METADATA.get(ct, ContentTypeMetadata(
            name=ct.value.replace('_', ' ').title(),
            description="",
            typical_sections=[],
            ideal_length="",
            tone=""
        )).name
        for ct in ContentType
    }


def get_content_type_metadata(content_type: str) -> ContentTypeMetadata:
    """
    Get metadata for a content type.

    Args:
        content_type: Content type value

    Returns:
        ContentTypeMetadata
    """
    try:
        ct = ContentType(content_type)
        return CONTENT_TYPE_METADATA.get(ct, ContentTypeMetadata(
            name=content_type.replace('_', ' ').title(),
            description="Custom content type",
            typical_sections=["Introduction", "Main Content", "Conclusion"],
            ideal_length="1000-1500 words",
            tone="Informative"
        ))
    except ValueError:
        return ContentTypeMetadata(
            name=content_type,
            description="Custom content type",
            typical_sections=["Introduction", "Main Content", "Conclusion"],
            ideal_length="1000-1500 words",
            tone="Informative"
        )
