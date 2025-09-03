from __future__ import annotations

from enum import Enum


class Platform(str, Enum):
    SLEEPER = "sleeper"
    ESPN = "espn"
    YAHOO = "yahoo"
    MFL = "mfl"
    FLEAFLICKER = "fleaflicker"
    CUSTOM = "custom"


class Position(str, Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"
    DL = "DL"
    LB = "LB"
    DB = "DB"


class LineupSlot(str, Enum):
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"
    FLEX = "FLEX"
    SUPER_FLEX = "SUPER_FLEX"
    WR_RB = "WR_RB"
    WR_RB_TE = "WR_RB_TE"
    RB_WR_TE = "RB_WR_TE"
    IDP_FLEX = "IDP_FLEX"
    DL = "DL"
    LB = "LB"
    DB = "DB"
    BENCH = "BENCH"
    IR = "IR"
    TAXI = "TAXI"


class NFLTeam(str, Enum):
    ARI = "ARI"
    ATL = "ATL"
    BAL = "BAL"
    BUF = "BUF"
    CAR = "CAR"
    CHI = "CHI"
    CIN = "CIN"
    CLE = "CLE"
    DAL = "DAL"
    DEN = "DEN"
    DET = "DET"
    GB = "GB"
    HOU = "HOU"
    IND = "IND"
    JAX = "JAX"
    KC = "KC"
    LAC = "LAC"
    LAR = "LAR"
    LV = "LV"
    MIA = "MIA"
    MIN = "MIN"
    NE = "NE"
    NO = "NO"
    NYG = "NYG"
    NYJ = "NYJ"
    PHI = "PHI"
    PIT = "PIT"
    SEA = "SEA"
    SF = "SF"
    TB = "TB"
    TEN = "TEN"
    WAS = "WAS"
    FA = "FA"  # Free Agent / no team


class TransactionType(str, Enum):
    ADD = "ADD"
    DROP = "DROP"
    TRADE = "TRADE"
    WAIVER_ADD = "WAIVER_ADD"
    WAIVER_DROP = "WAIVER_DROP"
    COMMISH_EDIT = "COMMISH_EDIT"
    IR_MOVE = "IR_MOVE"


class DraftType(str, Enum):
    SNAKE = "SNAKE"
    AUCTION = "AUCTION"
    LINEAR = "LINEAR"


class LeagueType(str, Enum):
    REDRAFT = "REDRAFT"
    DYNASTY = "DYNASTY"
    KEEPER = "KEEPER"
    BESTBALL = "BESTBALL"


class ScoringType(str, Enum):
    PPR = "PPR"
    HALF_PPR = "HALF_PPR"
    STANDARD = "STANDARD"
    CUSTOM = "CUSTOM"


class InjuryStatus(str, Enum):
    HEALTHY = "HEALTHY"
    QUESTIONABLE = "QUESTIONABLE"
    DOUBTFUL = "DOUBTFUL"
    OUT = "OUT"
    IR = "IR"
    SUSPENDED = "SUSPENDED"


class MatchupStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    FINAL = "FINAL"

