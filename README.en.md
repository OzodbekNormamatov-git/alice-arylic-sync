# 🎶 Alice ↔ Arylic — Smooth Sync

> Home Assistant blueprints that hand music off from a Yandex Station
> (**Alice**) to an **Arylic** (Hi-Fi) speaker through **Music Assistant** —
> starting at the *exact same second*, with a smooth crossfade — and gracefully
> bring it back when playback stops.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![type](https://img.shields.io/badge/type-Blueprints-blue)
![ha](https://img.shields.io/badge/Home%20Assistant-2024.6%2B-41BDF5)
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

1. Home Assistant **2024.6+** (for input `sections`).
2. **[Music Assistant](https://music-assistant.io/)** integration installed.
3. Arylic / LinkPlay added to Music Assistant as a player.
4. Yandex Station connected to HA (e.g. [AlexxIT/YandexStation](https://github.com/AlexxIT/YandexStation)), exposing `media_content_id` and `media_position`.
5. A matching music provider in MA (Yandex Music for the default `yandex_music://track/` URIs; change **Advanced → Track URI prefix** otherwise).

---

## Install

### Option A — Blueprint URL (easiest, no HACS)

Settings → Automations & Scenes → Blueprints → **Import Blueprint**, then paste
(replace `YOUR_GH_USER`):

```
https://github.com/YOUR_GH_USER/alice-arylic-sync/blob/main/blueprints/automation/alice_arylic/alice_arylic_handoff_start.yaml
https://github.com/YOUR_GH_USER/alice-arylic-sync/blob/main/blueprints/automation/alice_arylic/alice_arylic_smooth_stop.yaml
```

### Option B — HACS

HACS → ⋮ → **Custom repositories** → URL `https://github.com/YOUR_GH_USER/alice-arylic-sync`,
category **Automation** → Add → Download.

Then create one automation from each blueprint (Use blueprint → pick your entities).

---

## Key settings & tuning

Three knobs solve almost everything:

1. **Arylic lagging behind?** → raise **Sync offset** (6–7s) and/or **Arylic head-start** (450–600 ms).
2. **Volume jumps instead of stepping?** → raise **Arylic head-start** (LinkPlay debounces rapid volume commands).
3. **Crossfade too fast/slow?** → change **Steps**.

Full reference and tuning: [`docs/TUNING.md`](docs/TUNING.md) ·
Troubleshooting: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

---

## How it works (Start)

1. Track changes / playback starts on Alice → blueprint runs.
2. Arylic set to `floor`, the track is started via `music_assistant.play_media`.
3. Wait for Arylic to be `playing`.
4. Compute Alice's current second (+ `sync_offset`) and `media_seek` Arylic there.
5. ❗ Seeking re-buffers the stream — wait until audio actually resumes.
6. Sequential crossfade: each step → **Arylic up** → head-start delay → **Alice down**.
7. Ends with Alice at `end volume` (0) and Arylic at `target`.

---

## License

MIT — see [`LICENSE`](LICENSE).
