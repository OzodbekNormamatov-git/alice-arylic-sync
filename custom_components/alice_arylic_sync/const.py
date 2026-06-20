"""Constants for the Alice <-> Arylic Sync integration."""

DOMAIN = "alice_arylic_sync"

CONF_ALICE_ENTITY = "alice_entity"
CONF_ARYLIC_ENTITY = "arylic_entity"  # v1 entries (single output) — migrated
CONF_ARYLIC_ENTITIES = "arylic_entities"  # v2: one or more outputs (multi-room)

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
OPT_STOP_CONFIRM_DELAY = "stop_confirm_delay"  # debounce real stops vs voice-command blips
# Multi-room robustness levers (v1.3.0).
OPT_REGROUP_EACH_TRACK = "regroup_each_track"  # force re-join on every handoff
OPT_SEEK_EACH_OUTPUT = "seek_each_output"  # seek every output, not just the leader
OPT_REDIRECT_VOLUME = "redirect_volume"  # Alice "louder/quieter" -> outputs when handed off
# v1.5.0 hardening: some Arylic/LinkPlay firmwares abort the stream on a Music
# Assistant seek (HA core #136905 — progress jumps to 0:00, stream aborts with
# code 255, MA needs a restart). Skip the seek entirely on those players.
OPT_SKIP_SEEK = "skip_seek"

DEFAULTS: dict[str, float | int | str | bool] = {
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
    OPT_STOP_CONFIRM_DELAY: 1.0,
    OPT_REGROUP_EACH_TRACK: False,
    OPT_SEEK_EACH_OUTPUT: False,
    OPT_REDIRECT_VOLUME: True,
    OPT_SKIP_SEEK: False,
}

INVALID_CONTENT_IDS = (None, "", "unknown", "unavailable")
STOP_STATES = ("idle", "paused", "standby", "off")
