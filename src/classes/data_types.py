from dataclasses import dataclass, field
from typing import List


@dataclass
class Article:
    """Data class for an article.
    """
    title: str
    type: str
    year: int
    embedding: List[float]

@dataclass
class Embeddings:
    """Data class for an embedding.
    """
    urls: List[str] = field(default_factory=list)
    embeddings: List[List[float]] = field(default_factory=list)
    texts: List[str] = field(default_factory=list)

@dataclass
class EmbeddingsWithLabels:
    """Data class for an embedding with labels.
    """
    urls: List[str]
    embeddings: List[float]
    labels: List[int]