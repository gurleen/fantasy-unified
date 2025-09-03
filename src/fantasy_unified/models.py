from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

from .types import (
    DraftType,
    InjuryStatus,
    LeagueType,
    LineupSlot,
    MatchupStatus,
    NFLTeam,
    Platform,
    Position,
    ScoringType,
    TransactionType,
)


class ModelBase(BaseModel):
    """Base Pydantic model config for all entities.

    - Allows extra keys from providers (ignored during validation but preserved via model_dump)
    - Uses snake_case field names suitable for databases
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ExternalId(ModelBase):
    platform: Platform = Field(description="Source platform for the external identifier")
    value: str = Field(description="Identifier value on the source platform")


class User(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    display_name: str
    email: Optional[str] = None
    external_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of platform (e.g., 'sleeper') to user id on that platform",
    )


class Player(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[Position] = None
    nfl_team: Optional[NFLTeam] = None
    jersey_number: Optional[int] = None
    bye_week: Optional[int] = None
    birth_date: Optional[date] = None
    years_exp: Optional[int] = None
    height_in: Optional[int] = None
    weight_lb: Optional[int] = None
    college: Optional[str] = None
    injury_status: Optional[InjuryStatus] = None
    active: bool = True
    source_platform: Optional[Platform] = None
    external_ids: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific fields not represented explicitly"
    )


class Franchise(ModelBase):
    """Represents a fantasy team within a league (often called 'team' or 'roster' on providers)."""

    id: UUID = Field(default_factory=uuid4)
    league_id: UUID
    name: str
    abbreviation: Optional[str] = None
    owner_user_id: Optional[UUID] = None
    external_ids: Dict[str, str] = Field(default_factory=dict)


class ScoringSettings(ModelBase):
    """Flexible scoring configuration. Store only what is non-default for the league.

    Example keys: passing_yards, passing_tds, interceptions, rushing_yards, receptions, etc.
    """

    scoring_type: ScoringType = ScoringType.CUSTOM
    rules: Dict[str, float] = Field(default_factory=dict)


class League(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    name: str
    season_year: int
    type: LeagueType = LeagueType.REDRAFT
    source_platform: Optional[Platform] = None
    num_teams: Optional[int] = None
    scoring_settings: Optional[ScoringSettings] = None
    roster_slots: List[LineupSlot] = Field(default_factory=list)
    external_ids: Dict[str, str] = Field(default_factory=dict)


class RosterRecord(ModelBase):
    wins: int = 0
    losses: int = 0
    ties: int = 0


class Roster(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    league_id: UUID
    franchise_id: UUID
    starters: List[UUID] = Field(default_factory=list)
    bench: List[UUID] = Field(default_factory=list)
    ir: List[UUID] = Field(default_factory=list)
    taxi: List[UUID] = Field(default_factory=list)
    record: Optional[RosterRecord] = None
    points_for: float = 0.0
    points_against: float = 0.0


class Matchup(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    league_id: UUID
    week: int
    home_franchise_id: UUID
    away_franchise_id: UUID
    home_points: float = 0.0
    away_points: float = 0.0
    status: MatchupStatus = MatchupStatus.SCHEDULED


class PlayerMovement(ModelBase):
    player_id: UUID
    from_franchise_id: Optional[UUID] = None
    to_franchise_id: Optional[UUID] = None


class Transaction(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    league_id: UUID
    type: TransactionType
    executed_at: Optional[datetime] = None
    adds: List[PlayerMovement] = Field(default_factory=list)
    drops: List[PlayerMovement] = Field(default_factory=list)
    notes: Optional[str] = None


class Draft(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    league_id: UUID
    type: DraftType = DraftType.SNAKE
    order: List[UUID] = Field(
        default_factory=list, description="Sequence of franchise_ids representing pick order"
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DraftPick(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    draft_id: UUID
    round: int
    pick_in_round: int
    overall_pick: int
    franchise_id: UUID
    player_id: Optional[UUID] = None
    auction_cost: Optional[float] = None


class StatLine(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    league_id: Optional[UUID] = None
    player_id: UUID
    week: Optional[int] = None
    season_year: Optional[int] = None
    points: float = 0.0
    stats: Dict[str, float] = Field(default_factory=dict)


class Projection(ModelBase):
    id: UUID = Field(default_factory=uuid4)
    league_id: Optional[UUID] = None
    player_id: UUID
    week: Optional[int] = None
    season_year: Optional[int] = None
    projected_points: float = 0.0
    stats: Dict[str, float] = Field(default_factory=dict)


class Week(ModelBase):
    league_id: Optional[UUID] = None
    week_number: int
    start: Optional[datetime] = None
    end: Optional[datetime] = None

