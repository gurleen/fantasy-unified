from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional

from ..models import Draft, Franchise, League, Matchup, Player, Projection, Roster, StatLine, Transaction
from ..types import Platform


class ProviderError(RuntimeError):
    """Base exception for provider/fetcher errors."""


class BaseFetcher(ABC):
    """Abstract interface to normalize provider SDKs into unified models.

    Implementations should wrap existing provider SDKs/clients (Sleeper, Yahoo, ESPN, etc.)
    and map their responses to the Pydantic models in this package.
    """

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Platform implemented by this fetcher."""

    # High-level league discovery
    @abstractmethod
    def list_user_leagues(self, user_external_id: str, season_year: int) -> List[League]:
        """Return leagues for a given user on the provider for the season."""

    @abstractmethod
    def get_league(self, league_external_id: str) -> League:
        """Return a single league by provider identifier."""

    # League members and rosters
    @abstractmethod
    def get_franchises(self, league_external_id: str) -> List[Franchise]:
        """Return fantasy franchises (league teams/owners)."""

    @abstractmethod
    def get_rosters(self, league_external_id: str) -> List[Roster]:
        """Return rosters for the league, including starters/bench/IR/taxi if available."""

    # Players
    @abstractmethod
    def get_players(self, season_year: int, league_external_id: Optional[str] = None) -> List[Player]:
        """Return player directory for a season. Some providers require league context."""

    # Matchups and stats
    @abstractmethod
    def get_matchups(self, league_external_id: str, week: int) -> List[Matchup]:
        """Return scheduled/completed matchups for a given week."""

    @abstractmethod
    def get_week_stats(self, league_external_id: str, week: int) -> List[StatLine]:
        """Return player stat lines for a given week (actuals)."""

    @abstractmethod
    def get_week_projections(self, league_external_id: str, week: int) -> List[Projection]:
        """Return player projections for a given week."""

    # Transactions
    @abstractmethod
    def get_transactions(self, league_external_id: str, week: Optional[int] = None) -> List[Transaction]:
        """Return transactions, optionally filtered to a given week."""

    # Draft
    @abstractmethod
    def get_draft(self, league_external_id: str) -> Optional[Draft]:
        """Return basic draft metadata if available."""

    @abstractmethod
    def get_draft_picks(self, league_external_id: str) -> Iterable:
        """Return an iterable of draft picks mapped to DraftPick models or raw if streaming.

        Implementations may return a list of DraftPick for convenience or a generator for large drafts.
        """

