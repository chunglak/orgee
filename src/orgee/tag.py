from __future__ import annotations  # PEP 585

from collections.abc import MutableSet
from dataclasses import dataclass, field


@dataclass
class OrgTags(MutableSet):
    tags: set[str] = field(default_factory=set)

    def __contains__(self, x) -> bool:
        return x in self.tags

    def __iter__(self):
        return iter(self.tags)

    def __len__(self) -> int:
        return len(self.tags)

    def add(self, value) -> None:
        return self.tags.add(value)

    def discard(self, value) -> None:
        return self.tags.remove(value)
