# 🎶 Alice ↔ Arylic — Smooth Sync

> Home Assistant blueprints that hand music off from a Yandex Station
> (**Alice**) to an **Arylic** (Hi-Fi) speaker through **Music Assistant** —
> starting at the *exact same second*, with a smooth crossfade — and gracefully
> bring it back when playback stops.

[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://hacs.xyz/)
![type](https://img.shields.io/badge/type-Integration%20%2B%20Blueprints-blue)
![ha](https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5)
![license](https://img.shields.io/badge/license-MIT-green)

🇺🇿 O'zbekcha: [`README.md`](README.md)

---

## What it does

A Yandex Station isn't very loud. Many people want to **control** music with
Alice but **play** it through a Hi-Fi system like an **Arylic / LinkPlay**.
The problem: the two devices are out of sync — one leads, one lags, or both
play at once and you get an echo.

| Blueprint | Purpose |
|---|---|
| **Smooth Handoff (Start)** | When a track starts on Alice, it plays the same track on Arylic from the same second and crossfades **step-by-step**: Arylic steps up → Alice steps down → … Ends with Alice **muted** and Arylic at **full** volume. |
| **Smooth Stop & Restore** | When music stops on Alice, Arylic fades down and pauses, and Alice's volume is restored to a set level (e.g. **50%**). |

---

## Alice vs Arylic — which entity to pick

| | **Alice (Yandex Station)** | **Arylic (Music Assistant)** |
|---|---|---|
| **Role** | Source + control | Output (Hi-Fi) |
| **Entity** | `media_player.yandex_station_...` | Arylic's **Music Assistant** `media_player` |
| **Note** | — | ❗ Must be the **Music Assistant** entity, not the raw LinkPlay one — `music_assistant.play_media` only works with the MA entity |

---

## Requirements

1. Home Assistant **2024.12+** (for the integration; the blueprints only need 2024.10).
2. **[Music Assistant](https://music-assistant.io/)** integration installed.
3. Arylic / LinkPlay added to Music Assistant as a player.
4. Yandex Station connected to HA (e.g. [AlexxIT/YandexStation](https://github.com/AlexxIT/YandexStation)), exposing `media_content_id` and `media_position`.
5. A matching music provider in MA (Yandex Music for the default `yandex_music://track/` URIs; change **Advanced → Track URI prefix** otherwise).

---

## Install

Two ways: the **Integration** (recommended — everything in the UI, like any
other integration) or the **Blueprints** (lighter, YAML automations).

### Option 1 — Integration (via HACS, recommended) ⭐

1. **HACS → ⋮ (top right) → Custom repositories**.
2. **Repository:** `https://github.com/OzodbekNormamatov-git/alice-arylic-sync`
   · **Type:** `Integration` → **Add**.
3. Find **Alice ↔ Arylic Sync** in HACS, **Download**, then restart Home Assistant.
4. **Settings → Devices & Services → Add Integration** → search for
   "**Alice ↔ Arylic Sync**".
5. Pick your players: **Alice (Yandex Station)** as the source and **one or
   more** Music Assistant entities as outputs (the picker only shows Music
   Assistant players). Selecting several outputs enables **multi-room**: they
   are auto-grouped and play the same track in sync.
6. Done — it starts working immediately. **Every setting** (sync offset, start
   delay, steps, head-start, volumes, timeouts) lives behind the **Configure**
   button on the integration card.

> Without HACS: copy `custom_components/alice_arylic_sync/` into
> `config/custom_components/` and restart Home Assistant.

> 💡 The integration also creates a **Sync** switch per pair so you can
> temporarily disable the handoff.

### Option 2 — Blueprints (YAML automations)

#### Import buttons

| Blueprint | Import |
|---|---|
| **Smooth Handoff (Start)** | [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FOzodbekNormamatov-git%2Falice-arylic-sync%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Falice_arylic%2Falice_arylic_handoff_start.yaml) |
| **Smooth Stop & Restore** | [![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FOzodbekNormamatov-git%2Falice-arylic-sync%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Falice_arylic%2Falice_arylic_smooth_stop.yaml) |

Or manually: Settings → Automations & Scenes → Blueprints → **Import Blueprint**, then paste:

```
https://github.com/OzodbekNormamatov-git/alice-arylic-sync/blob/main/blueprints/automation/alice_arylic/alice_arylic_handoff_start.yaml
https://github.com/OzodbekNormamatov-git/alice-arylic-sync/blob/main/blueprints/automation/alice_arylic/alice_arylic_smooth_stop.yaml
```

> ℹ️ Note: HACS has no blueprint category — blueprints install via HA's native
> **Import Blueprint** (buttons above). What HACS installs is the
> **integration** from Option 1.

#### Manual copy

Copy both `.yaml` files from `blueprints/automation/alice_arylic/` into
`config/blueprints/automation/alice_arylic/` in your HA configuration and
restart Home Assistant.

Then create one automation from each blueprint (Use blueprint → pick your entities).

> If you use the blueprints, don't also install the integration (running both
> would hand each track off twice).

---

## Multi-room (same music in every room)

Two ways:

**Option 1 — select several outputs in the integration (easiest).** When adding
the integration, tick all your speakers in the **Arylic players** picker. On
handoff they are auto-joined into a Music Assistant group (the first one is the
leader) and play the same track in sync; volume steps go to all of them in a
single call.

**Option 2 — a permanent Music Assistant group.** In Music Assistant create a
group player (**Settings → Players → Add group player**) and select that single
group entity as the output.

> ⚠️ Speakers must be groupable in Music Assistant (e.g. all AirPlay, or all in
> the same LinkPlay family). For mixed types, create a Universal Group in MA
> and use Option 2.

---

## Key settings & tuning

Three knobs solve almost everything:

1. **Arylic lagging behind?** → raise **Sync offset** (6–7s) and/or **Arylic head-start** (450–600 ms).
2. **Volume jumps instead of stepping?** → raise **Arylic head-start** (LinkPlay debounces rapid volume commands).
3. **Crossfade too fast/slow?** → change **Steps**.

Full tuning guide: [`docs/TUNING.md`](docs/TUNING.md) ·
Troubleshooting: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
*(both currently in Uzbek)*.

---

## Settings reference

### Smooth Handoff (Start)

| Setting | Default | Meaning |
|---|---|---|
| **Alice player** | — | Source (Yandex Station) `media_player` |
| **Arylic player** | — | Output (Music Assistant) `media_player` |
| **Arylic floor** | `0.05` | Volume Arylic starts rising from (5%) |
| **Arylic target** | `0.35` | Arylic's final volume (35%) |
| **Alice end volume** | `0` | Where Alice ends up (0 = fully silent) |
| **Sync offset (s)** | `5.0` | ⭐ Most important: aligns Arylic to Alice's playback second |
| **Steps** | `12` | Crossfade steps (more = smoother, fewer = faster) |
| **Arylic head-start (ms)** | `350` | ⭐ How far Arylic leads Alice on each step (covers device latency) |
| **Alice gap (ms)** | `180` | Pause after Alice steps down before the next step |
| **Track URI prefix** | `yandex_music://track/` | URI prepended to `media_content_id` |
| **media_type** | `track` | Media type for `music_assistant.play_media` |
| **Play wait timeout (s)** | `12` | How long to wait for Arylic to report `playing` |
| **Buffer wait timeout (s)** | `6` | Wait for the player to accept the new position after the seek |

### Smooth Stop & Restore

| Setting | Default | Meaning |
|---|---|---|
| **Alice player** | — | Same Alice entity as in Start |
| **Arylic player** | — | Same Arylic entity as in Start |
| **Arylic fade floor** | `0.01` | Arylic fades down to this level before pausing |
| **Alice restore volume** | `0.5` | Alice returns to this volume after the stop |
| **Steps** | `10` | Fade-down steps |
| **Step delay (ms)** | `200` | Delay between steps |

---

## How it works (Start)

1. Track changes / playback starts on Alice → blueprint runs.
2. Arylic set to `floor`, the track is started via `music_assistant.play_media`.
3. Wait for Arylic to be `playing`.
4. Compute Alice's current second (+ `sync_offset`) and `media_seek` Arylic there.
5. ❗ Seeking re-buffers the stream — wait until the player accepts the new
   position (plus a short buffer delay).
6. Sequential crossfade: each step → **Arylic up** → head-start delay → **Alice down**.
7. Ends with Alice at `end volume` (0) and Arylic at `target`.

---

## License

MIT — see [`LICENSE`](LICENSE).
