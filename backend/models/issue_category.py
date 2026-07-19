from enum import Enum


class IssueCategory(str, Enum):
    OOM_KILL = "oom_kill"
    DISK_SPACE_EXHAUSTION = "disk_space_exhaustion"
    AUTH_FAILURE = "auth_failure"
    TIMEOUT = "timeout"
    DATABASE_CONNECTION_ERROR = "database_connection_error"
    HTTP_5XX_SPIKE = "http_5xx_spike"
    UNKNOWN = "unknown"
