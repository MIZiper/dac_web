"""Import replacement framework.

When importing a desktop DAC project into the web version, certain actions
need to be replaced (e.g. local file loading → data-source loading).

This module provides a registry-based system where developers define
replacement rules. The two-phase import pipeline (preview + apply) lets
users review and approve each proposed change.

Rules may perform I/O (e.g. querying external mapping APIs), so
``transform()`` is async and the registry methods are coroutines.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum


class ReplacementStatus(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNCHANGED = "unchanged"


@dataclass
class ReplaceOutcome:
    """Result of running a rule against one action.

    Attributes:
        action: The replacement action dict, or None to keep original.
        summary: Human-readable description of the change.
        status: resolved | unresolved | unchanged.
        reason: Explanation when unresolved (e.g. mapping not found).
    """
    action: dict | None
    summary: str
    status: ReplacementStatus
    reason: str = ""


class ActionReplacementRule:
    """Base class for action replacement rules.

    Subclasses set ``source_class`` (the fully-qualified ``_class_`` path
    to match) and implement ``transform()``.

    ``transform()`` is an ``async`` method — rules that call external APIs
    can ``await`` inside it; purely synchronous rules can omit ``await``
    and return directly (Python permits this).

    Override ``match()`` for more complex matching logic beyond class path
    comparison.
    """

    source_class: str
    name: str = ""
    description: str = ""

    def match(self, action: dict) -> bool:
        return action.get("_class_") == self.source_class

    async def transform(self, action: dict) -> ReplaceOutcome:
        raise NotImplementedError


class ReplacementRegistry:
    """Singleton registry of replacement rules.

    Usage::

        registry = ReplacementRegistry()
        registry.register(MyRule())
        outcome = await registry.process(action_dict)
    """

    _instance: "ReplacementRegistry | None" = None

    def __init__(self):
        self._rules: list[ActionReplacementRule] = []

    def __bool__(self):
        return bool(self._rules)

    @classmethod
    def instance(cls) -> "ReplacementRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, rule: ActionReplacementRule):
        self._rules.append(rule)

    async def process(self, action: dict) -> ReplaceOutcome:
        for rule in self._rules:
            if rule.match(action):
                return await rule.transform(action)
        action_class = action.get("_class_", "unknown")
        return ReplaceOutcome(
            action=None,
            summary=f"Keep {action_class} unchanged",
            status=ReplacementStatus.UNCHANGED,
        )

    async def process_all(
        self,
        config: dict,
        concurrency: int | None = None,
    ) -> list[ReplaceOutcome]:
        """Run all rules against every action in *config*.

        Parameters:
            concurrency: Maximum number of actions to process concurrently
                (via ``asyncio.Semaphore``).  ``None`` means sequential.
        """
        actions = config.get("actions", [])
        if concurrency is not None and concurrency > 1:
            sem = asyncio.Semaphore(concurrency)
            async def _one(a):
                async with sem:
                    return await self.process(a)
            return await asyncio.gather(*(_one(a) for a in actions))
        return [await self.process(a) for a in actions]

    @property
    def rule_count(self) -> int:
        return len(self._rules)
