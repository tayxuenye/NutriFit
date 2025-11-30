"""Embedding engine for semantic search and matching."""

import hashlib
import re
from pathlib import Path

import numpy as np


class EmbeddingEngine:
    """
    Lightweight embedding engine for recipe and workout matching.

    Uses pre-computed embeddings or a simple TF-IDF-like approach
    for offline semantic matching without heavy model dependencies.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_cache_size_mb: int = 100,
        max_memory_cache_items: int = 1000,
    ):
        """Initialize the embedding engine.

        Args:
            cache_dir: Directory for caching embeddings. Defaults to ~/.nutrifit/embeddings
            max_cache_size_mb: Maximum disk cache size in MB (default: 100)
            max_memory_cache_items: Maximum number of items in memory cache (default: 1000)
        """
        self.cache_dir = cache_dir or Path.home() / ".nutrifit" / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._embeddings_cache: dict[str, np.ndarray] = {}
        self._max_cache_size_mb = max_cache_size_mb
        self._max_memory_cache_items = max_memory_cache_items
        self._model = None
        self._model_name = "all-MiniLM-L6-v2"
        self._use_transformer = False

        # Try to load sentence-transformers, fall back to TF-IDF-like approach
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the embedding model."""
        # Always initialize vocab for fallback mode
        self._vocab: dict[str, int] = {}
        self._idf: dict[str, float] = {}

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            self._use_transformer = True
        except ImportError:
            # Fall back to simple word-based embeddings
            self._use_transformer = False

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    def _simple_tokenize(self, text: str) -> list[str]:
        """Simple tokenization for fallback embeddings."""
        # Convert to lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r"[a-z0-9]+", text)
        return tokens

    def _simple_embed(self, text: str) -> np.ndarray:
        """Generate simple bag-of-words style embedding."""
        tokens = self._simple_tokenize(text)

        # Update vocabulary
        for token in tokens:
            if token not in self._vocab:
                self._vocab[token] = len(self._vocab)

        # Create embedding vector (using word frequency)
        # Limit dimension to 384 to match transformer output
        dim = 384
        embedding = np.zeros(dim)

        for token in tokens:
            idx = self._vocab.get(token, 0) % dim
            embedding[idx] += 1.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def embed(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Generate embedding for text.

        Args:
            text: Text to embed
            use_cache: Whether to use cached embeddings

        Returns:
            Embedding vector as numpy array
        """
        cache_key = self._get_cache_key(text)

        # Check in-memory cache first
        if use_cache and cache_key in self._embeddings_cache:
            return self._embeddings_cache[cache_key]

        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.npy"
        if use_cache and cache_file.exists():
            embedding = np.load(cache_file)
            self._embeddings_cache[cache_key] = embedding
            return embedding

        # Generate embedding
        if self._use_transformer and self._model is not None:
            embedding = self._model.encode(text, convert_to_numpy=True)
        else:
            embedding = self._simple_embed(text)

        # Cache the embedding only if use_cache is True
        if use_cache:
            self._embeddings_cache[cache_key] = embedding
            np.save(cache_file, embedding)

            # Enforce cache limits
            self._enforce_cache_limits()

        return embedding

    def embed_batch(self, texts: list[str], use_cache: bool = True) -> np.ndarray:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use cached embeddings

        Returns:
            Stacked embedding vectors as numpy array
        """
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if use_cache and cache_key in self._embeddings_cache:
                embeddings.append((i, self._embeddings_cache[cache_key]))
            else:
                cache_file = self.cache_dir / f"{cache_key}.npy"
                if use_cache and cache_file.exists():
                    embedding = np.load(cache_file)
                    self._embeddings_cache[cache_key] = embedding
                    embeddings.append((i, embedding))
                else:
                    texts_to_embed.append(text)
                    indices_to_embed.append(i)

        # Batch embed remaining texts
        if texts_to_embed:
            if self._use_transformer and self._model is not None:
                new_embeddings = self._model.encode(
                    texts_to_embed, convert_to_numpy=True
                )
            else:
                new_embeddings = np.array(
                    [self._simple_embed(t) for t in texts_to_embed]
                )

            # Cache and add to results
            for idx, text, embedding in zip(
                indices_to_embed, texts_to_embed, new_embeddings, strict=False
            ):
                cache_key = self._get_cache_key(text)
                if use_cache:
                    self._embeddings_cache[cache_key] = embedding
                    cache_file = self.cache_dir / f"{cache_key}.npy"
                    np.save(cache_file, embedding)
                embeddings.append((idx, embedding))

            # Enforce cache limits after batch operation
            if use_cache:
                self._enforce_cache_limits()

        # Sort by original index and stack
        embeddings.sort(key=lambda x: x[0])
        return np.array([e[1] for e in embeddings])

    def similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def find_similar(
        self,
        query: str,
        items: list[str],
        item_ids: list[str] | None = None,
        top_k: int = 5,
    ) -> list[tuple[int, str, float]]:
        """Find most similar items to a query.

        Args:
            query: Query text
            items: List of item texts to search
            item_ids: Optional list of item IDs
            top_k: Number of top results to return

        Returns:
            List of tuples (index, id/text, similarity_score)
        """
        query_embedding = self.embed(query)
        item_embeddings = self.embed_batch(items)

        similarities = []
        for i, item_emb in enumerate(item_embeddings):
            sim = self.similarity(query_embedding, item_emb)
            item_id = item_ids[i] if item_ids else items[i]
            similarities.append((i, item_id, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[2], reverse=True)

        return similarities[:top_k]

    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        self._embeddings_cache.clear()
        for cache_file in self.cache_dir.glob("*.npy"):
            cache_file.unlink()

    def get_cache_size_mb(self) -> float:
        """Get current disk cache size in MB.

        Returns:
            Cache size in megabytes
        """
        total_size = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.npy") if f.is_file()
        )
        return total_size / (1024 * 1024)

    def get_cache_stats(self) -> dict[str, int | float]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        disk_files = list(self.cache_dir.glob("*.npy"))
        return {
            "memory_cache_items": len(self._embeddings_cache),
            "disk_cache_files": len(disk_files),
            "disk_cache_size_mb": self.get_cache_size_mb(),
            "max_cache_size_mb": self._max_cache_size_mb,
            "max_memory_cache_items": self._max_memory_cache_items,
        }

    def _enforce_cache_limits(self) -> None:
        """Enforce cache size limits by removing oldest entries."""
        # Enforce memory cache limit
        if len(self._embeddings_cache) > self._max_memory_cache_items:
            # Remove oldest entries (simple FIFO)
            items_to_remove = (
                len(self._embeddings_cache) - self._max_memory_cache_items
            )
            keys_to_remove = list(self._embeddings_cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del self._embeddings_cache[key]

        # Enforce disk cache limit
        current_size_mb = self.get_cache_size_mb()
        if current_size_mb > self._max_cache_size_mb:
            # Remove oldest files by modification time
            cache_files = sorted(
                self.cache_dir.glob("*.npy"), key=lambda f: f.stat().st_mtime
            )
            for cache_file in cache_files:
                cache_file.unlink()
                current_size_mb = self.get_cache_size_mb()
                if current_size_mb <= self._max_cache_size_mb * 0.8:  # 80% threshold
                    break

    def is_using_transformer(self) -> bool:
        """Check if using transformer model or fallback.

        Returns:
            True if using transformer model, False if using fallback
        """
        return self._use_transformer
