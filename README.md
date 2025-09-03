# fantasy-unified

Unified Pydantic data models and fetcher interface for fantasy football platforms (Sleeper, Yahoo, ESPN, etc.).

## Install

Using uv (recommended):

```bash
uv sync
```

For an editable install during development:

```bash
uv pip install -e .
```

Build distributables (wheel and sdist):

```bash
uv build
```

Publish to an index (optional):

```bash
# Set credentials, then:
uv publish
```

## Goals

- Platform-agnostic Pydantic models that can map to database tables
- A common `BaseFetcher` interface so providers can plug in existing SDKs

## Usage

### Models

```python
from fantasy_unified import League, Player, Roster, Position

league = League(name="My League", season_year=2025)
player = Player(full_name="Justin Jefferson", position=Position.WR)
```

### Implementing a Provider Fetcher

```python
from fantasy_unified.fetchers import BaseFetcher
from fantasy_unified.types import Platform
from fantasy_unified.models import League

class SleeperFetcher(BaseFetcher):
    @property
    def platform(self) -> Platform:
        return Platform.SLEEPER

    def list_user_leagues(self, user_external_id: str, season_year: int):
        # call sleeper SDK, map to League models
        return []

    def get_league(self, league_external_id: str):
        return League(name="", season_year=2025)

    def get_franchises(self, league_external_id: str):
        return []

    def get_rosters(self, league_external_id: str):
        return []

    def get_players(self, season_year: int, league_external_id: str | None = None):
        return []

    def get_matchups(self, league_external_id: str, week: int):
        return []

    def get_week_stats(self, league_external_id: str, week: int):
        return []

    def get_week_projections(self, league_external_id: str, week: int):
        return []

    def get_transactions(self, league_external_id: str, week: int | None = None):
        return []

    def get_draft(self, league_external_id: str):
        return None

    def get_draft_picks(self, league_external_id: str):
        return []
```

## Notes

- All models have UUID primary keys suitable for DBs; store provider IDs in `external_ids`.
- Keep provider-specific fields in `metadata` maps where applicable.
- `model_dump(by_alias=False)` will return snake_case names for DB serialization.