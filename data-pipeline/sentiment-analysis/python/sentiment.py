"""
LLM-Based Sentiment Analysis

A standalone, multi-source sentiment analysis module that uses an LLM (Claude)
to classify text sentiment with source-aware calibration. Designed for data
pipelines processing content from Reddit, Hacker News, news articles, academic
papers, and more.

No project-specific imports. Requires ``anthropic`` SDK and the Python standard
library.

Usage:
    from sentiment import SentimentAnalyzer, SentimentConfig

    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("This product is amazing!", source="review")
    print(result.sentiment, result.confidence, result.reasoning)

Batch usage:
    results = analyzer.analyze_batch([
        ("Great update!", "reddit"),
        ("Earnings missed estimates.", "news"),
    ])
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Union

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Sentiment = Literal["positive", "negative", "neutral", "mixed"]

VALID_SENTIMENTS: set[str] = {"positive", "negative", "neutral", "mixed"}

VALID_SOURCES: set[str] = {
    "reddit",
    "hackernews",
    "news",
    "academic",
    "social_media",
    "review",
    "general",
}

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt_template() -> str:
    """Load the classify prompt template from disk."""
    prompt_path = _PROMPT_DIR / "classify-prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Classify prompt not found at {prompt_path}. "
            "Ensure the prompts/ directory is alongside the python/ directory."
        )
    return prompt_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SentimentResult:
    """Result of a single sentiment analysis.

    Attributes:
        sentiment: One of positive, negative, neutral, or mixed.
        confidence: Confidence score between 0.0 and 1.0.
        reasoning: Brief explanation of the classification.
        source: The source platform used for calibration.
        text_preview: First 80 characters of the analyzed text.
    """

    sentiment: Sentiment
    confidence: float
    reasoning: str
    source: str
    text_preview: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "source": self.source,
            "text_preview": self.text_preview,
        }


@dataclass
class SentimentConfig:
    """Configuration for the sentiment analyzer.

    Attributes:
        model: Claude model to use (default: claude-sonnet-4-6).
        max_tokens: Maximum response tokens (default: 256).
        temperature: Sampling temperature (default: 0.0 for deterministic).
        api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        default_source: Source to use when none is specified (default: general).
        max_text_length: Truncate input text beyond this length (default: 4000).
    """

    model: str = "claude-sonnet-4-6"
    max_tokens: int = 256
    temperature: float = 0.0
    api_key: Optional[str] = None
    default_source: str = "general"
    max_text_length: int = 4000


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SentimentAnalysisError(Exception):
    """Raised when sentiment analysis fails."""

    def __init__(
        self,
        message: str,
        text_preview: str = "",
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.text_preview = text_preview
        self.cause = cause


class InvalidResponseError(SentimentAnalysisError):
    """Raised when the LLM response cannot be parsed into a valid result."""

    pass


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


class SentimentAnalyzer:
    """LLM-based sentiment analyzer with source-aware calibration.

    Uses Claude to classify text sentiment. Each analysis call sends the text
    and source type to the LLM with a carefully calibrated prompt that adjusts
    for platform-specific norms (e.g., Reddit sarcasm, HN understatement,
    academic hedging).

    Args:
        config: Optional SentimentConfig. Uses defaults if not provided.
    """

    def __init__(self, config: Optional[SentimentConfig] = None) -> None:
        self.config = config or SentimentConfig()
        self._client: Any = None
        self._prompt_template: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        text: str,
        source: Optional[str] = None,
    ) -> SentimentResult:
        """Analyze sentiment of a single text.

        Args:
            text: The text to analyze.
            source: Source platform for calibration. One of: reddit,
                hackernews, news, academic, social_media, review, general.
                Defaults to config.default_source.

        Returns:
            SentimentResult with sentiment, confidence, and reasoning.

        Raises:
            SentimentAnalysisError: If the API call or parsing fails.
            ValueError: If text is empty or source is invalid.
        """
        if not text or not text.strip():
            raise ValueError("Text must be non-empty.")

        source = self._validate_source(source)
        truncated = self._truncate(text)
        prompt = self._build_prompt(truncated, source)
        preview = text[:80].replace("\n", " ")

        try:
            raw = self._call_llm(prompt)
            parsed = self._parse_response(raw)
        except InvalidResponseError:
            raise
        except Exception as exc:
            raise SentimentAnalysisError(
                f"Sentiment analysis failed: {exc}",
                text_preview=preview,
                cause=exc,
            ) from exc

        return SentimentResult(
            sentiment=parsed["sentiment"],
            confidence=parsed["confidence"],
            reasoning=parsed["reasoning"],
            source=source,
            text_preview=preview,
        )

    def analyze_batch(
        self,
        items: Sequence[Union[str, Tuple[str, str]]],
    ) -> List[SentimentResult]:
        """Analyze sentiment for multiple texts.

        Args:
            items: Sequence of texts or (text, source) tuples.

        Returns:
            List of SentimentResult, one per input. Failed analyses raise
            immediately — use try/except per item if you need partial results.
        """
        results: List[SentimentResult] = []
        for item in items:
            if isinstance(item, str):
                text, source = item, None
            else:
                text, source = item[0], item[1]
            results.append(self.analyze(text, source=source))
        return results

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "The 'anthropic' package is required. "
                    "Install it with: pip install anthropic"
                )
            api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise SentimentAnalysisError(
                    "No API key provided. Pass api_key in SentimentConfig "
                    "or set the ANTHROPIC_API_KEY environment variable."
                )
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _get_prompt_template(self) -> str:
        """Load and cache the prompt template."""
        if self._prompt_template is None:
            self._prompt_template = _load_prompt_template()
        return self._prompt_template

    def _validate_source(self, source: Optional[str]) -> str:
        """Validate and return the source string."""
        source = source or self.config.default_source
        if source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source '{source}'. Must be one of: {sorted(VALID_SOURCES)}"
            )
        return source

    def _truncate(self, text: str) -> str:
        """Truncate text to max_text_length, preserving word boundaries."""
        if len(text) <= self.config.max_text_length:
            return text
        truncated = text[: self.config.max_text_length]
        # Try to break at last space to avoid cutting mid-word
        last_space = truncated.rfind(" ")
        if last_space > self.config.max_text_length * 0.8:
            truncated = truncated[:last_space]
        return truncated + " [truncated]"

    def _build_prompt(self, text: str, source: str) -> str:
        """Build the full prompt from template + text + source."""
        template = self._get_prompt_template()
        return template.replace("{source}", source).replace("{text}", text)

    def _call_llm(self, prompt: str) -> str:
        """Send prompt to Claude and return the raw text response."""
        client = self._get_client()
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract text from the first content block
        if not response.content:
            raise SentimentAnalysisError("Empty response from LLM.")
        return response.content[0].text

    def _parse_response(self, raw: str) -> Dict[str, Any]:
        """Parse the LLM response into a validated dictionary.

        Extracts JSON from the response, handling cases where the LLM
        wraps the JSON in markdown code fences or adds surrounding text.
        """
        # Try to extract JSON from code fences first
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON object
            json_match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise InvalidResponseError(
                    f"No JSON object found in LLM response: {raw[:200]}"
                )

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise InvalidResponseError(f"Invalid JSON in LLM response: {exc}") from exc

        # Validate required fields
        sentiment = data.get("sentiment", "").lower().strip()
        if sentiment not in VALID_SENTIMENTS:
            raise InvalidResponseError(
                f"Invalid sentiment '{sentiment}'. "
                f"Must be one of: {sorted(VALID_SENTIMENTS)}"
            )

        confidence = data.get("confidence")
        if confidence is None:
            raise InvalidResponseError("Missing 'confidence' field in response.")
        try:
            confidence = float(confidence)
        except (TypeError, ValueError) as exc:
            raise InvalidResponseError(
                f"Invalid confidence value: {confidence}"
            ) from exc
        confidence = max(0.0, min(1.0, confidence))

        reasoning = data.get("reasoning", "").strip()
        if not reasoning:
            raise InvalidResponseError("Missing or empty 'reasoning' field.")

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "reasoning": reasoning,
        }


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def analyze_sentiment(
    text: str,
    source: str = "general",
    model: str = "claude-sonnet-4-6",
    api_key: Optional[str] = None,
) -> SentimentResult:
    """One-shot convenience function for sentiment analysis.

    Args:
        text: The text to analyze.
        source: Source platform for calibration.
        model: Claude model to use.
        api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var).

    Returns:
        SentimentResult with sentiment, confidence, and reasoning.
    """
    config = SentimentConfig(model=model, api_key=api_key)
    analyzer = SentimentAnalyzer(config=config)
    return analyzer.analyze(text, source=source)
