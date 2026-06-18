# Changelog

Barcha muhim o'zgarishlar shu faylda qayd etiladi.
Format [Keep a Changelog](https://keepachangelog.com/) asosida.

## [1.3.0] - 2026-06-18

### Tuzatildi
- **Multi-room drift:** bir nechta Arylic kolonka **trek almashganda yoki
  stop→qayta qo'yilganda bir-biridan ajralib (kech qolib)** ketadigan muammo
  tuzatildi. Sabablar: (1) to'xtashdan keyin guruh "eskirgan" deb belgilanib,
  qayta birlashtirilmas edi; (2) faqat **yetakchi** 'playing' bo'lishi kutilib,
  hali buferlanayotgan boshqa kolonkalar seekka ergashmасdi; (3) seek faqat
  yetakchiga yuborilardi.

### O'zgartirildi
- Endi handoff **sovuq startda** (yetakchi avval chalmayotgan bo'lsa: birinchi
  ijro yoki to'xtashdan keyin) guruhni **majburiy qayta tuzadi**, ammo ijro
  davom etayotganda trek almashsa — uzilishsiz o'tkazib yuboradi.
- Seekdan oldin **barcha** chiqishlar 'playing' bo'lishini kutadi (faqat yetakchi emas).
- Sinxrondan keyin xonalar pozitsiyasi tekshiriladi: 2.5s dan ko'p farq bo'lsa,
  **ogohlantirish** (DEBUG'da har xonaning pozitsiyasi) chiqaradi.

### Qo'shildi
- **Har bir chiqishni alohida seek qilish** sozlamasi — kolonkalar
  namuna-aniq sinxron qilolmaydigan holatlar uchun (seekni hammaga yuboradi).
- **Har trekda qayta guruhlash** sozlamasi — guruh vaqt o'tib buzilsa, har
  trekda majburiy qayta birlashtirish.

## [1.2.0] - 2026-06-11

### Qo'shildi
- **Multi-room:** integratsiyada endi **bir nechta Arylic kolonka** tanlash
  mumkin. Musiqa boshlanganda ular Music Assistant orqali avtomatik guruhlanadi
  (birinchi tanlangani yetakchi) va barcha xonalarda **bir xil trek sinxron**
  chaladi; ovoz qadamlari hammasiga bitta buyruqda yuboriladi.
- Eski (bitta kolonkali) sozlamalar avtomatik yangi formatga o'tkaziladi —
  hech narsa qilish shart emas.

### O'zgartirildi
- Config oynasida "Arylic (chiqish)" maydoni endi ko'p tanlovli
  (`arylic_entities`).

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
- Integratsiya UI'si (config flow + Configure oynasi) **to'liq o'zbek tilida**.
  HA qaysi tilda bo'lishidan qat'i nazar o'zbekcha ko'rinadi (`en` fallback
  ham o'zbekcha).

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
