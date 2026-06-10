# Changelog

Barcha muhim o'zgarishlar shu faylda qayd etiladi.
Format [Keep a Changelog](https://keepachangelog.com/) asosida.

## [1.0.0] - 2026-06-10

### Qo'shildi
- **Smooth Handoff (Start)** blueprint — Alice → Arylic navbatma-navbat
  crossfade (Arylic oldinda), sinxron `media_seek` va seekdan keyin bufer kutish.
- **Smooth Stop & Restore** blueprint — Arylic yumshoq fade-down + pauza,
  Alice ovozini tiklash.
- To'liq UI sozlamalari (sections): speaker tanlash, ovoz darajalari, sync offset,
  qadamlar, head-start, advanced (URI prefiksi, media_type, timeoutlar).
- HACS qo'llab-quvvatlash (`hacs.json`, blueprint category).
- O'zbekcha va inglizcha README, TUNING.md, TROUBLESHOOTING.md.
- `examples/` — entity'lar to'ldirilgan tayyor (blueprintsiz) avtomatikalar.
