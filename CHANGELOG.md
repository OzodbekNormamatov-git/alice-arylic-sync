# Changelog

Barcha muhim o'zgarishlar shu faylda qayd etiladi.
Format [Keep a Changelog](https://keepachangelog.com/) asosida.

## [1.1.0] - 2026-06-11

### Qo'shildi
- **To'laqonli custom integratsiya** (`custom_components/alice_arylic_sync/`) —
  HACS'dan `Integration` sifatida o'rnatiladi, **Settings → Devices & Services →
  Add Integration** ro'yxatida chiqadi:
  - UI orqali kolonka tanlash (Arylic ro'yxatida faqat Music Assistant playerlari);
  - **barcha** sozlamalar (sync offset, boshlash kechikishi, qadamlar, head-start,
    ovoz darajalari, stop sozlamalari, timeoutlar, URI prefiksi) **Configure**
    oynasida;
  - har juftlik uchun **Sync** switch (vaqtincha o'chirish);
  - inglizcha va ruscha tarjimalar.
- CI: hassfest + HACS (integration) tekshiruvlari.
- Yangi sozlama: **Boshlash kechikishi (handoff delay)** — musiqa boshlangach
  qancha kutib uzatish.

### O'zgartirildi
- Minimal Home Assistant: integratsiya uchun **2024.12**, blueprintlar uchun
  2024.10 (o'zgarmagan).
- README: integratsiya asosiy o'rnatish usuli, blueprintlar muqobil.

## [1.0.0] - 2026-06-11

### Qo'shildi
- **Smooth Handoff (Start)** blueprint — Alice → Arylic navbatma-navbat
  crossfade (Arylic oldinda), sinxron `media_seek` (manfiy bo'lmaydigan qilib
  chegaralangan) va seekdan keyin player yangi pozitsiyani qabul qilishini kutish.
- **Smooth Stop & Restore** blueprint — Arylic yumshoq fade-down + pauza,
  Alice ovozini tiklash. Shartlar: faqat Arylic chalayotganda va Alice'da aynan
  MUSIQA to'xtaganda ishlaydi (ovozli javob/yangilik/budilnikda emas).
- To'liq UI sozlamalari (sections): speaker tanlash, ovoz darajalari, sync offset,
  qadamlar, head-start, advanced (URI prefiksi, media_type, timeoutlar).
- "My Home Assistant" import tugmalari (HACS blueprint'larni qo'llab-quvvatlamaydi,
  shuning uchun o'rnatish HA'ning o'z Import Blueprint mexanizmi orqali).
- GitHub Actions CI — yamllint + blueprint sxema tekshiruvi.
- O'zbekcha va inglizcha README, TUNING.md, TROUBLESHOOTING.md.
- `examples/` — namuna (entity ID'lari almashtiriladigan) tayyor avtomatikalar.
- Minimal Home Assistant versiyasi: **2024.10** (zamonaviy `triggers:`/`actions:`
  sintaksisi).
