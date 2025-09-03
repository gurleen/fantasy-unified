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

from fantasy_unified.fetchers import SleeperFetcher

fetcher = SleeperFetcher()
leagues = fetcher.list_user_leagues(user_external_id="12345", season_year=2025)
league = fetcher.get_league(league_external_id="9876543210")
franchises = fetcher.get_franchises(league_external_id="9876543210")
rosters = fetcher.get_rosters(league_external_id="9876543210")
players = fetcher.get_players(season_year=2025)
matchups_w1 = fetcher.get_matchups(league_external_id="9876543210", week=1)
transactions = fetcher.get_transactions(league_external_id="9876543210")
```

## Notes

- All models have UUID primary keys suitable for DBs; store provider IDs in `external_ids`.
- Keep provider-specific fields in `metadata` maps where applicable.
- `model_dump(by_alias=False)` will return snake_case names for DB serialization.