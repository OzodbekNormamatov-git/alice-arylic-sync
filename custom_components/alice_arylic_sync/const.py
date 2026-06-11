"""Constants for the Alice <-> Arylic Sync integration."""

DOMAIN = "alice_arylic_sync"

CONF_ALICE_ENTITY = "alice_entity"
CONF_ARYLIC_ENTITY = "arylic_entity"

# Options (all tunable from the UI). Defaults mirror the blueprint defaults.
OPT_SYNC_OFFSET = "sync_offset"
OPT_HANDOFF_DELAY = "handoff_delay"
OPT_STEPS = "steps"
OPT_HEADSTART_MS = "arylic_headstart_ms"
OPT_ALICE_GAP_MS = "alice_gap_ms"
OPT_ARYLIC_FLOOR = "arylic_floor"
OPT_ARYLIC_TARGET = "arylic_target"
OPT_ALICE_END_VOLUME = "alice_end_volume"
OPT_TRACK_URI_PREFIX = "track_uri_prefix"
OPT_MEDIA_TYPE = "media_type"
OPT_PLAY_WAIT_TIMEOUT = "play_wait_timeout"
OPT_BUFFER_WAIT_TIMEOUT = "buffer_wait_timeout"
OPT_STOP_FADE_FLOOR = "stop_fade_floor"
OPT_ALICE_RESTORE_VOLUME = "alice_restore_volume"
OPT_STOP_STEPS = "stop_steps"
OPT_STOP_STEP_DELAY_MS = "stop_step_delay_ms"

DEFAULTS: dict[str, float | int | str] = {
    OPT_SYNC_OFFSET: 5.0,
    OPT_HANDOFF_DELAY: 0.0,
    OPT_STEPS: 12,
    OPT_HEADSTART_MS: 350,
    OPT_ALICE_GAP_MS: 180,
    OPT_ARYLIC_FLOOR: 0.05,
    OPT_ARYLIC_TARGET: 0.35,
    OPT_ALICE_END_VOLUME: 0.0,
    OPT_TRACK_URI_PREFIX: "yandex_music://track/",
    OPT_MEDIA_TYPE: "track",
    OPT_PLAY_WAIT_TIMEOUT: 12,
    OPT_BUFFER_WAIT_TIMEOUT: 6,
    OPT_STOP_FADE_FLOOR: 0.01,
    OPT_ALICE_RESTORE_VOLUME: 0.5,
    OPT_STOP_STEPS: 10,
    OPT_STOP_STEP_DELAY_MS: 200,
}

INVALID_CONTENT_IDS = (None, "", "unknown", "unavailable")
STOP_STATES = ("idle", "paused", "standby", "off")
