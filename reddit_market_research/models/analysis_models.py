"""
Data models for analysis results and statistics.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalysisResult(BaseModel):
    """Result of text analysis."""
    sentiment: str = Field(..., description="positive, neutral, or negative")
    category: str = Field(..., description="Content category")
    subcategory: Optional[str] = Field(default=None, description="Optional subcategory label")
    is_question: Optional[bool] = Field(default=None, description="Legacy question flag (optional)")
    confidence: float = Field(default=0.0, description="Analysis confidence 0.0-1.0")
    reasoning: Optional[str] = Field(default=None, description="Explanation for analysis")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_level: str = Field(..., description="toy, nlp, or llm")
    llm_response: Optional[str] = Field(default=None, description="Raw LLM response")


class EnrichedObject(BaseModel):
    """Reddit object with analysis."""
    # Original fields (minimal)
    id: str
    url: str
    title: Optional[str] = None
    communityName: str
    body: Optional[str] = None
    dataType: str
    createdAt: str
    upVotes: int

    # Additional fields for comments
    postId: Optional[str] = None
    parentId: Optional[str] = None

    # Analysis results
    analysis: AnalysisResult

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FileStats(BaseModel):
    """Statistics for a single file."""
    level: str = "file"
    file_name: str
    community: str
    total_objects: int
    posts: int
    comments: int
    positive_posts: int
    negative_posts: int
    neutral_posts: int
    positive_percent: float
    questions: int
    answers: int
    praise: int
    complaint: int
    category_counts_json: str
    top_category: str
    issues_found: int
    solutions_found: int
    issues_json: str  # JSON string of issues frequency
    solutions_json: str  # JSON string of solutions frequency


class CommunityStats(BaseModel):
    """Statistics aggregated by community."""
    level: str = "community"
    community: str
    product: str
    total_files: int
    total_objects: int
    posts: int
    comments: int
    positive_posts: int
    negative_posts: int
    neutral_posts: int
    positive_percent: float
    questions: int
    answers: int
    answer_rate: float
    praise: int
    complaint: int
    top_category: str
    category_counts_json: str
    issues_count: int
    solutions_count: int
    top_pain_point: str
    top_solution: str


class ProductStats(BaseModel):
    """Statistics aggregated by target product."""
    level: str = "product"
    target_product: str
    total_communities: int
    total_files: int
    total_objects: int
    posts: int
    comments: int
    positive_posts: int
    negative_posts: int
    neutral_posts: int
    positive_percent: float
    questions: int
    answers: int
    answer_rate: float
    top_pain_point: str
    top_solution: str
    market_share_percent: float
    category_counts_json: str
