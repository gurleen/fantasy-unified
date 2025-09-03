from __future__ import annotations

from collections import defaultdict
from datetime import datetime, date
from typing import Dict, Iterable, List, Optional
from uuid import UUID, NAMESPACE_URL, uuid5

from sleeper_wrapper import League as SleeperLeague
from sleeper_wrapper import Players as SleeperPlayers
from sleeper_wrapper import Stats as SleeperStats
from sleeper_wrapper import User as SleeperUser

from .base import BaseFetcher, ProviderError
from ..models import (
    Draft,
    DraftPick,
    Franchise,
    League,
    Matchup,
    Player,
    PlayerMovement,
    Projection,
    Roster,
    RosterRecord,
    StatLine,
    Transaction,
)
from ..types import (
    DraftType,
    InjuryStatus,
    LineupSlot,
    MatchupStatus,
    NFLTeam,
    Platform,
    Position,
    TransactionType,
)


NAMESPACE = uuid5(NAMESPACE_URL, "fantasy-unified-sleeper")


def _deterministic_uuid(kind: str, provider_id: str) -> UUID:
    return uuid5(NAMESPACE, f"{kind}:{provider_id}")


_LINEUP_SLOT_MAP: Dict[str, LineupSlot] = {
    "QB": LineupSlot.QB,
    "RB": LineupSlot.RB,
    "WR": LineupSlot.WR,
    "TE": LineupSlot.TE,
    "K": LineupSlot.K,
    "DEF": LineupSlot.DEF,
    "FLEX": LineupSlot.FLEX,
    "SUPER_FLEX": LineupSlot.SUPER_FLEX,
    "WRRB": LineupSlot.WR_RB,
    "WRRBTE": LineupSlot.WR_RB_TE,
    "RBWRTE": LineupSlot.RB_WR_TE,
    "IDP_FLEX": LineupSlot.IDP_FLEX,
    "DL": LineupSlot.DL,
    "LB": LineupSlot.LB,
    "DB": LineupSlot.DB,
    "BN": LineupSlot.BENCH,
    "BENCH": LineupSlot.BENCH,
    "IR": LineupSlot.IR,
    "TAXI": LineupSlot.TAXI,
}


_POSITION_MAP: Dict[str, Position] = {
    "QB": Position.QB,
    "RB": Position.RB,
    "WR": Position.WR,
    "TE": Position.TE,
    "K": Position.K,
    "DEF": Position.DEF,
    "DL": Position.DL,
    "LB": Position.LB,
    "DB": Position.DB,
}


def _map_lineup_slot(slot: str) -> LineupSlot:
    return _LINEUP_SLOT_MAP.get(slot.upper(), LineupSlot.BENCH)


def _map_position(pos: Optional[str]) -> Optional[Position]:
    if not pos:
        return None
    return _POSITION_MAP.get(pos.upper())


def _map_team(team: Optional[str]) -> Optional[NFLTeam]:
    if not team:
        return None
    try:
        return NFLTeam(team.upper())
    except Exception:
        return NFLTeam.FA


def _map_injury(status: Optional[str]) -> Optional[InjuryStatus]:
    if not status:
        return None
    key = status.upper()
    try:
        return InjuryStatus(key)
    except Exception:
        return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


class SleeperFetcher(BaseFetcher):
    @property
    def platform(self) -> Platform:
        return Platform.SLEEPER

    # High-level league discovery
    def list_user_leagues(self, user_external_id: str, season_year: int) -> List[League]:
        try:
            user = SleeperUser(user_external_id)
            leagues = user.get_all_leagues("nfl", str(season_year))
        except Exception as exc:
            raise ProviderError(f"Sleeper user leagues fetch failed: {exc}") from exc

        results: List[League] = []
        for lg in leagues or []:
            league_id = str(lg.get("league_id") or lg.get("leagueId") or "")
            if not league_id:
                continue
            results.append(self._map_league_dict(lg))
        return results

    def get_league(self, league_external_id: str) -> League:
        try:
            league = SleeperLeague(league_external_id)
            lg = league.get_league()
        except Exception as exc:
            raise ProviderError(f"Sleeper league fetch failed: {exc}") from exc
        return self._map_league_dict(lg)

    def _map_league_dict(self, lg: Dict) -> League:
        league_id = str(lg.get("league_id") or lg.get("leagueId") or "")
        season = int(lg.get("season") or lg.get("season_year") or 0)
        roster_positions = lg.get("roster_positions") or []
        num_teams = int(lg.get("total_rosters") or lg.get("total_teams") or 0)
        return League(
            id=_deterministic_uuid("league", league_id) if league_id else None,  # type: ignore[arg-type]
            name=str(lg.get("name") or ""),
            season_year=season,
            type=None,  # default in model is REDRAFT
            source_platform=Platform.SLEEPER,
            num_teams=num_teams or None,
            roster_slots=[_map_lineup_slot(s) for s in roster_positions],
            external_ids={"sleeper": league_id} if league_id else {},
        )

    # League members and rosters
    def get_franchises(self, league_external_id: str) -> List[Franchise]:
        try:
            league = SleeperLeague(league_external_id)
            rosters = league.get_rosters() or []
            users = league.get_users() or []
        except Exception as exc:
            raise ProviderError(f"Sleeper franchises fetch failed: {exc}") from exc

        user_id_to_name: Dict[str, str] = {}
        for u in users:
            user_id = str(u.get("user_id") or "")
            if user_id:
                user_id_to_name[user_id] = str(u.get("display_name") or u.get("username") or user_id)

        league_uuid = _deterministic_uuid("league", league_external_id)
        franchises: List[Franchise] = []
        for r in rosters:
            roster_id = str(r.get("roster_id") or r.get("rosterId") or "")
            owner_id = str(r.get("owner_id") or r.get("ownerId") or "")
            name = user_id_to_name.get(owner_id) or f"Roster {roster_id}"
            franchises.append(
                Franchise(
                    id=_deterministic_uuid("franchise", f"{league_external_id}:{roster_id}") if roster_id else None,  # type: ignore[arg-type]
                    league_id=league_uuid,
                    name=name,
                    abbreviation=None,
                    owner_user_id=None,
                    external_ids={
                        "sleeper_roster_id": roster_id,
                        "sleeper_owner_id": owner_id,
                        "sleeper": roster_id,
                    },
                )
            )
        return franchises

    def get_rosters(self, league_external_id: str) -> List[Roster]:
        try:
            league = SleeperLeague(league_external_id)
            rosters = league.get_rosters() or []
        except Exception as exc:
            raise ProviderError(f"Sleeper rosters fetch failed: {exc}") from exc

        league_uuid = _deterministic_uuid("league", league_external_id)
        results: List[Roster] = []
        for r in rosters:
            roster_id = str(r.get("roster_id") or r.get("rosterId") or "")
            starters_raw = r.get("starters") or []
            all_players_raw = r.get("players") or []
            starters = [
                _deterministic_uuid("player", str(pid)) for pid in starters_raw if pid is not None
            ]
            bench = [
                _deterministic_uuid("player", str(pid))
                for pid in all_players_raw
                if pid is not None and pid not in starters_raw
            ]
            settings = r.get("settings") or {}
            record = RosterRecord(
                wins=int(settings.get("wins") or 0),
                losses=int(settings.get("losses") or 0),
                ties=int(settings.get("ties") or 0),
            )
            points_for = float(settings.get("fpts") or settings.get("points_for") or 0)
            results.append(
                Roster(
                    league_id=league_uuid,
                    franchise_id=_deterministic_uuid("franchise", f"{league_external_id}:{roster_id}"),
                    starters=starters,
                    bench=bench,
                    ir=[],
                    taxi=[],
                    record=record,
                    points_for=points_for,
                    points_against=0.0,
                )
            )
        return results

    # Players
    def get_players(self, season_year: int, league_external_id: Optional[str] = None) -> List[Player]:
        try:
            players_client = SleeperPlayers()
            try:
                players_dict = players_client.get_players()
            except Exception:
                players_dict = players_client.get_all_players()
        except Exception as exc:
            raise ProviderError(f"Sleeper players fetch failed: {exc}") from exc

        results: List[Player] = []
        for pid, pd in (players_dict or {}).items():
            try:
                pid_str = str(pid)
                full_name = str(pd.get("full_name") or (f"{pd.get('first_name','')} {pd.get('last_name','')}".strip()) or pd.get("last_name") or pid_str)
                player = Player(
                    id=_deterministic_uuid("player", pid_str),
                    full_name=full_name,
                    first_name=pd.get("first_name"),
                    last_name=pd.get("last_name"),
                    position=_map_position(pd.get("position")),
                    nfl_team=_map_team(pd.get("team")),
                    jersey_number=int(pd.get("number")) if pd.get("number") is not None else None,
                    bye_week=int(pd.get("bye_week") or pd.get("bye")) if (pd.get("bye_week") or pd.get("bye")) is not None else None,
                    birth_date=_parse_date(pd.get("birth_date")),
                    years_exp=int(pd.get("years_exp")) if pd.get("years_exp") is not None else None,
                    height_in=int(pd.get("height")) if pd.get("height") is not None else None,
                    weight_lb=int(pd.get("weight")) if pd.get("weight") is not None else None,
                    college=pd.get("college"),
                    injury_status=_map_injury(pd.get("injury_status")),
                    active=bool(pd.get("active", True)),
                    source_platform=Platform.SLEEPER,
                    external_ids={"sleeper": pid_str},
                    metadata={k: v for k, v in pd.items() if k not in {
                        "full_name","first_name","last_name","position","team","number","bye_week","bye","birth_date","years_exp","height","weight","college","injury_status","active"
                    }},
                )
                results.append(player)
            except Exception:
                # Skip malformed records
                continue
        return results

    # Matchups and stats
    def get_matchups(self, league_external_id: str, week: int) -> List[Matchup]:
        try:
            league = SleeperLeague(league_external_id)
            matchups = league.get_matchups(week) or []
        except Exception as exc:
            raise ProviderError(f"Sleeper matchups fetch failed: {exc}") from exc

        league_uuid = _deterministic_uuid("league", league_external_id)
        by_matchup: Dict[str, List[Dict]] = defaultdict(list)
        for m in matchups:
            mid = str(m.get("matchup_id") or m.get("matchupId") or "0")
            by_matchup[mid].append(m)

        results: List[Matchup] = []
        for mid, teams in by_matchup.items():
            if not teams:
                continue
            teams_sorted = sorted(teams, key=lambda t: int(t.get("roster_id") or 0))
            home = teams_sorted[0]
            away = teams_sorted[1] if len(teams_sorted) > 1 else None
            home_franchise = _deterministic_uuid("franchise", f"{league_external_id}:{home.get('roster_id')}")
            away_franchise = _deterministic_uuid("franchise", f"{league_external_id}:{away.get('roster_id') if away else '0'}")
            results.append(
                Matchup(
                    league_id=league_uuid,
                    week=week,
                    home_franchise_id=home_franchise,
                    away_franchise_id=away_franchise,
                    home_points=float(home.get("points") or 0.0),
                    away_points=float((away or {}).get("points") or 0.0),
                    status=MatchupStatus.FINAL if (home.get("points") is not None and (away or {}).get("points") is not None) else MatchupStatus.SCHEDULED,
                )
            )
        return results

    def get_week_stats(self, league_external_id: str, week: int) -> List[StatLine]:
        # Best-effort: the wrapper offers various stats endpoints; keep minimal for now
        try:
            _ = SleeperStats()
        except Exception:
            pass
        return []

    def get_week_projections(self, league_external_id: str, week: int) -> List[Projection]:
        return []

    # Transactions
    def get_transactions(self, league_external_id: str, week: Optional[int] = None) -> List[Transaction]:
        try:
            league = SleeperLeague(league_external_id)
            txns = league.get_transactions(week) if week is not None else league.get_transactions()
        except Exception as exc:
            raise ProviderError(f"Sleeper transactions fetch failed: {exc}") from exc

        league_uuid = _deterministic_uuid("league", league_external_id)
        results: List[Transaction] = []
        for t in txns or []:
            ttype = str(t.get("type") or "").lower()
            if ttype in {"waiver", "free_agent", "add"}:
                tx_type = TransactionType.WAIVER_ADD if ttype == "waiver" else TransactionType.ADD
            elif ttype in {"drop"}:
                tx_type = TransactionType.DROP
            elif ttype in {"trade"}:
                tx_type = TransactionType.TRADE
            else:
                tx_type = TransactionType.COMMISH_EDIT

            executed = t.get("status_updated") or t.get("created")
            executed_dt = None
            if executed:
                try:
                    executed_dt = datetime.fromtimestamp(int(executed) / 1000)
                except Exception:
                    try:
                        executed_dt = datetime.fromtimestamp(int(executed))
                    except Exception:
                        executed_dt = None

            adds: List[PlayerMovement] = []
            drops: List[PlayerMovement] = []
            add_map = t.get("adds") or {}
            drop_map = t.get("drops") or {}
            for pid, roster_id in add_map.items():
                adds.append(
                    PlayerMovement(
                        player_id=_deterministic_uuid("player", str(pid)),
                        to_franchise_id=_deterministic_uuid("franchise", f"{league_external_id}:{roster_id}"),
                    )
                )
            for pid, roster_id in drop_map.items():
                drops.append(
                    PlayerMovement(
                        player_id=_deterministic_uuid("player", str(pid)),
                        from_franchise_id=_deterministic_uuid("franchise", f"{league_external_id}:{roster_id}"),
                    )
                )

            results.append(
                Transaction(
                    league_id=league_uuid,
                    type=tx_type,
                    executed_at=executed_dt,
                    adds=adds,
                    drops=drops,
                    notes=str(t.get("notes") or "") or None,
                )
            )
        return results

    # Draft
    def get_draft(self, league_external_id: str) -> Optional[Draft]:
        try:
            league = SleeperLeague(league_external_id)
            drafts = league.get_drafts() or []
        except Exception as exc:
            raise ProviderError(f"Sleeper draft fetch failed: {exc}") from exc

        if not drafts:
            return None
        d = drafts[0]
        draft_id = str(d.get("draft_id") or d.get("draftId") or "")
        league_uuid = _deterministic_uuid("league", league_external_id)
        draft_uuid = _deterministic_uuid("draft", draft_id) if draft_id else _deterministic_uuid("draft", f"{league_external_id}:default")
        dtype_raw = str(d.get("type") or "").upper()
        try:
            dtype = DraftType[dtype_raw]  # type: ignore[index]
        except Exception:
            dtype = DraftType.SNAKE
        started = d.get("start_time") or d.get("start_time_ms")
        completed = d.get("end_time") or d.get("end_time_ms")
        def _to_dt(v: Optional[int]) -> Optional[datetime]:
            if not v:
                return None
            try:
                return datetime.fromtimestamp(int(v) / 1000)
            except Exception:
                try:
                    return datetime.fromtimestamp(int(v))
                except Exception:
                    return None
        return Draft(
            id=draft_uuid,
            league_id=league_uuid,
            type=dtype,
            order=[],
            started_at=_to_dt(started),
            completed_at=_to_dt(completed),
        )

    def get_draft_picks(self, league_external_id: str) -> Iterable[DraftPick]:
        try:
            league = SleeperLeague(league_external_id)
            drafts = league.get_drafts() or []
        except Exception as exc:
            raise ProviderError(f"Sleeper draft picks fetch failed: {exc}") from exc

        if not drafts:
            return []
        d = drafts[0]
        draft_id = str(d.get("draft_id") or d.get("draftId") or "")
        try:
            picks = league.get_draft_picks(draft_id) if draft_id else []
        except Exception as exc:
            raise ProviderError(f"Sleeper draft picks fetch failed: {exc}") from exc

        league_uuid = _deterministic_uuid("league", league_external_id)
        draft_uuid = _deterministic_uuid("draft", draft_id) if draft_id else _deterministic_uuid("draft", f"{league_external_id}:default")
        results: List[DraftPick] = []
        for p in picks or []:
            round_no = int(p.get("round") or 0)
            pick_in_round = int(p.get("pick_no") or p.get("pick") or 0)
            overall = int(p.get("overall") or ((round_no - 1) * int(d.get("rounds") or 0) + pick_in_round))
            roster_id = str(p.get("roster_id") or "")
            player_id = p.get("player_id")
            results.append(
                DraftPick(
                    draft_id=draft_uuid,
                    round=round_no,
                    pick_in_round=pick_in_round,
                    overall_pick=overall,
                    franchise_id=_deterministic_uuid("franchise", f"{league_external_id}:{roster_id}"),
                    player_id=_deterministic_uuid("player", str(player_id)) if player_id else None,
                    auction_cost=None,
                )
            )
        return results

