# Changelog

Barcha muhim o'zgarishlar shu faylda qayd etiladi.
Format [Keep a Changelog](https://keepachangelog.com/) asosida.

## [1.5.0] - 2026-06-20

Multi-room ishonchliligini mustahkamlash (arxitektura o'zgartirilmadi —
mavjud "har Arylic'ni guruhlash" yo'li tuzatildi va bardoshliroq qilindi).

### Tuzatildi
- **To'xtagandan keyin bir xona musiqa chalishda davom etardigan bug.** Avval
  pauza uchun faqat yetakchining `group_members`'iga tayanilardi; agar guruh
  "bo'shashib", lekin ro'yxat hali hammани ko'rsatib tursa, haqiqatda guruhdan
  chiqib ketgan xona pauza qilinmasdan qolardi. Endi **har bir kolonka alohida**
  pauza qilinadi (guruhdagilarga zararsiz, idempotent).
- **Bitta o'lik/yo'q kolonka butun crossfade'ni to'xtatib qo'yardi.** Volume
  endi har bir kolonkaga alohida, xatoga chidamli (`return_exceptions`) yuboriladi
  va har qadamda faqat **mavjud** kolonkalarga qo'llanadi — bitta xona tushib
  qolsa, qolganlari to'xtamaydi va Alice to'liq pasayadi. Ovoz yo'naltirishda
  (`redirect_volume`) ham shu — bitta kolonka xato bersa, Alice baribir jim
  holatga qaytariladi.
- **Seekdan oldin a'zolar hali eski trekda bo'lsa drift bo'lardi.** Endi seekdan
  oldin har bir kolonka faqat `playing` emas, **yangi trekka o'tgani**
  (content_id o'zgargani yoki pozitsiya 0 ga tushgani) kutiladi.

### Qo'shildi
- **Leader failover:** yetakchi sifatida endi har safar **birinchi mavjud**
  kolonka olinadi (avval doim `arylic_entities[0]` edi — agar o'sha offline
  bo'lsa, butun tizim ishlamasdi). Hech qaysi kolonka mavjud bo'lmasa, handoff
  toza o'tkazib yuboriladi.
- **Guruhlash imkoniyatini oldindan tekshirish:** `media_player.join` chaqirishdan
  oldin kolonkaning `GROUPING` bayrog'i (supported_features) tekshiriladi —
  qo'llab-quvvatlamaydigan yoki mavjud bo'lmagan kolonka aniq ogohlantirish bilan
  guruhdan chiqariladi (avvalgi "join, keyin xato" o'rniga).
- Yangi sozlama: **«Seekni o'tkazib yuborish»** (`skip_seek`, standart o'chiq).
  Ba'zi Arylic/LinkPlay firmware'larida MA orqali seek stream'ni uzadi (progress
  0:00 ga qaytadi, MA restart kerak — HA core #136905). Shu kolonkalar uchun
  yoqing: trek 0:00 dan boshlanadi, sinxron faqat «Sinxron offset» bilan
  taxminiy, lekin stream uzilmaydi.
- **Integratsiya o'chirilganda guruh tarqatiladi** (`unjoin`). Reload va Sync
  switch'ni o'chirish guruhni ataylab saqlaydi (kolonkalar chalishda davom etadi)
  — faqat to'liq o'chirishda guruh tarqatiladi, orfan guruhlar qolmaydi.

## [1.4.1] - 2026-06-18

### Tuzatildi
- **"Balandlat/pasaytir" deganda kolonkalar floorga tushib qaytadigan muammo
  (ovoz oshmasdi, Alice baland eshitilardi).** Handoffdan keyin Alice'ga ovoz
  buyrug'i berilganda stansiya bir lahzaga `playing` holatidan chiqib-qaytar (yoki
  o'sha trekni qayta e'lon qilar). Bu **yangi trek boshlandi** yoki **musiqa
  to'xtadi** deb hisoblanib, butun handoff yoki stop-fade qaytadan ishga tushardi:
  kolonkalar floor (masalan 6%) ga tushib yana target (16%) ga ko'tarilardi,
  ovoz aslida o'smasdi, Alice esa crossfade paytida baland eshitilardi. Ikki yo'l
  ham tuzatildi:
  - **Handoff trigger:** topshirilgan trek o'zgarmagan va kolonkalar hali
    chalayotgan bo'lsa, bunday qayta-kirish **resume** deb qabul qilinadi —
    handoff qaytadan ishga tushmaydi.
  - **Stop trigger (debounce):** musiqa to'xtaganda endi qisqa vaqt
    (**«To'xtashni tasdiqlash kechikishi»**, standart 1.0s) kutib qaytadan
    tekshiriladi. Agar shu oraliqda musiqa qaytsa (ovozli buyruq sababli yuz
    bergan lahzalik to'xtash), stop **bekor qilinadi** — kolonkalar to'xtamaydi.
  - Natijada ovoz buyrug'i to'g'ri kolonkalarga qo'llanadi va orta boradi
    (6→16→26…), Alice jim qoladi.

### Qo'shildi
- Yangi sozlama: **«To'xtashni tasdiqlash kechikishi»** (`stop_confirm_delay`,
  standart 1.0s). Ovozli buyruqlaringiz uzunroq bo'lsa (masalan "ob-havo qanaqa")
  oshiring; 0 qilsangiz, eski (darhol to'xtash) xatti-harakatga qaytadi.

### O'zgartirildi
- Sync switch o'chirib-yoqilganda (kolonkalar chalishda davom etayotgan bo'lsa)
  topshirilgan trek xotirasi **saqlanadi** — qayta yoqqaningizdan keyingi ovozli
  buyruq behuda to'liq handoffni qo'zg'atmaydi.
- Diagnostika: har bir muhim Alice o'zgarishi (state/volume/content + topshirilgan
  trek) DEBUG logga yoziladi (pozitsiya-yangilanish "shovqini"siz).

### Ma'lum cheklov
- **Ovozli "pasaytir"** faqat **«Alice yakuniy ovozi» > 0** bo'lganda ishlaydi
  (masalan 0.05). Standart 0 da Alice 0 dan pastga tusholmaydi, shuning uchun
  "pasaytir" sezilmaydi; "balandlat" esa har doim ishlaydi.

## [1.4.0] - 2026-06-18

### Qo'shildi
- **Ovoz buyrug'ini yo'naltirish:** handoff bo'lgandan keyin (Alice jim,
  Arylic'lar chalayotganda) Alice'ga **"ovozni balandlat / pasaytir"** desangiz,
  o'zgarish endi **Alice'ga emas, Arylic kolonkalarга** qo'llanadi — Alice jim
  qoladi. Alice ovozidagi o'zgarish miqdori (delta) barcha chiqishlarга
  qo'shiladi/ayiriladi. Faqat *Alice yakuniy ovozi* past (≤0.15) bo'lganda, ya'ni
  handoff-rejimida ishlaydi. Yangi **«Alice ovoz buyrug'ini kolonkalarga
  yo'naltirish»** sozlamasi bilan o'chirib qo'yish mumkin (standart: yoqilgan).

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
