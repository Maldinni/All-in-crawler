from dataclasses import dataclass
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
    urls: List[str]
    embeddings: List[float]


@dataclass
class EmbeddingsWithLabels:
    """Data class for an embedding with labels.
    """
    urls: List[str]
    embeddings: List[float]
    labels: List[int]