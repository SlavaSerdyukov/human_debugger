from collections import Counter
from dataclasses import dataclass
from hashlib import blake2b
from math import sqrt
from typing import Any

from app.analytics.metrics import average, split_tags
from app.models import Entry, Project

EMBEDDING_DIMENSIONS = 32


@dataclass(frozen=True)
class MemoryItem:
    date: str
    tags: tuple[str, ...]
    focus: int
    energy: int
    vector: tuple[float, ...]


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(character.lower() if character.isalnum() else " " for character in text)
    return [token for token in cleaned.split() if len(token) > 2]


def local_hash_embedding(text: str, dimensions: int = EMBEDDING_DIMENSIONS) -> tuple[float, ...]:
    vector = [0.0] * dimensions
    for token in _tokenize(text):
        digest = blake2b(token.encode("utf-8"), digest_size=4).digest()
        bucket = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[bucket] += sign

    magnitude = sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return tuple(vector)
    return tuple(round(value / magnitude, 4) for value in vector)


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    return round(sum(a * b for a, b in zip(left, right, strict=True)), 4)


def _memory_items(entries: list[Entry]) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    for entry in sorted(entries, key=lambda item: item.date):
        tags = tuple(split_tags(entry.tags))
        local_text = " ".join([entry.text, " ".join(tags)])
        items.append(
            MemoryItem(
                date=entry.date.isoformat(),
                tags=tags,
                focus=entry.focus,
                energy=entry.energy,
                vector=local_hash_embedding(local_text),
            )
        )
    return items


def semantic_memory_summary(entries: list[Entry], projects: list[Project]) -> dict[str, Any]:
    items = _memory_items(entries)
    tag_counts = Counter(tag for item in items for tag in item.tags)
    negative_tag_count = sum(tag_counts[tag] for tag in ("stuck", "procrastination", "overwhelmed", "bored"))

    similar_pairs = 0
    for index, item in enumerate(items):
        for other in items[index + 1 :]:
            if cosine_similarity(item.vector, other.vector) >= 0.45:
                similar_pairs += 1

    active_project_names = [project.name for project in projects if project.status == "active"]
    return {
        "embedding_model": "local-hash-v1",
        "item_count": len(items),
        "active_projects": len(active_project_names),
        "top_tags": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(6)],
        "recurring_context_pairs": similar_pairs,
        "average_focus": average([item.focus for item in items]),
        "average_energy": average([item.energy for item in items]),
        "negative_tag_count": negative_tag_count,
        "privacy_note": "Embeddings are computed locally and raw journal text is not sent to the LLM layer.",
    }
