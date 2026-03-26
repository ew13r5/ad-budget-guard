# Redis key prefixes
SIM_STATE_KEY = "simulation:state"
SIM_SPEND_PREFIX = "simulation:spend:"
SIM_PATTERN_PREFIX = "simulation:pattern:"
SIM_FORCED_ANOMALY_PREFIX = "simulation:forced_anomaly:"
SIM_TICK_LOCK_KEY = "simulation:tick_lock"
SIM_PUBSUB_CHANNEL = "simulation:updates"


# Event types for SimulationLog
class SimEventType:
    TICK = "tick"
    PAUSE = "pause"
    RESUME = "resume"
    ANOMALY = "anomaly"
    SCENARIO_CHANGE = "scenario_change"
    SPEED_CHANGE = "speed_change"
    RESET = "reset"
    BUDGET_EXCEEDED = "budget_exceeded"
    CAMPAIGN_PAUSED = "campaign_paused"


# Default configuration
DEFAULT_TICK_INTERVAL = 2
DEFAULT_SPEED_MULTIPLIER = 1
VALID_SPEED_MULTIPLIERS = (1, 5, 10)
DEFAULT_SCENARIO = "normal"
FLUSH_EVERY_N_TICKS = 5
TICK_LOCK_TTL = 5
FORCED_ANOMALY_TTL = 5
WS_QUEUE_MAX_SIZE = 100
WS_CLOSE_CODE_AUTH_FAILED = 4001

# Pattern type names
PATTERN_STEADY = "steady"
PATTERN_PEAK_HOURS = "peak_hours"
PATTERN_ANOMALY = "anomaly"
PATTERN_DECLINING = "declining"
