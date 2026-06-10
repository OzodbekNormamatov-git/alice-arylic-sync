# 🎶 Alice ↔ Arylic — Smooth Sync

> Yandex Station (**Alice**) da boshlangan musiqani **Music Assistant** orqali
> **Arylic** (Hi-Fi) speakerga *xuddi shu sekunddan*, yumshoq crossfade bilan
> uzatadigan va to'xtaganda yana yumshoq qaytaradigan Home Assistant blueprint
> to'plami.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![type](https://img.shields.io/badge/type-Blueprints-blue)
![ha](https://img.shields.io/badge/Home%20Assistant-2024.6%2B-41BDF5)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 📌 Bu nima?

Yandex Station ovozi unchalik kuchli emas. Ko'pchilik Alice bilan **boshqarib**,
ovozni esa **Arylic / LinkPlay** kabi Hi-Fi tizimdan chiqarishni xohlaydi.
Muammo — ikki qurilma sinxron emas: biri oldinda, biri orqada yangraydi yoki
ikkalasi bir vaqtda gapirib, "echo" bo'ladi.

Bu to'plam ikkita masalani hal qiladi:

| Blueprint | Vazifasi |
|---|---|
| **Smooth Handoff (Start)** | Alice'da trek boshlansa, o'sha trekni Arylic'da aynan shu sekunddan qo'yadi va **navbatma-navbat** crossfade qiladi: Arylic bir pog'ona ko'tariladi → Alice bir pog'ona tushadi → ... Oxirida Alice **0** (jim), Arylic **to'liq** ovoz. |
| **Smooth Stop & Restore** | Alice'da musiqa to'xtasa, Arylic ovozi yumshoq pasayib pauza bo'ladi, Alice ovozi esa belgilangan darajaga (mas. **50%**) qaytadi. |

---

## 🆚 Alice va Arylic — farqi (qaysi entity'ni tanlash kerak)

Bu yerda **ikki xil "kolonka"** bor va ularni adashtirmaslik muhim:

| | **Alice (Yandex Station)** | **Arylic (Music Assistant)** |
|---|---|---|
| **Roli** | MANBA + boshqaruv | CHIQISH (Hi-Fi) |
| **Nima qiladi** | Musiqani topadi, ovoz bilan boshqariladi | Sifatli ovoz chiqaradi |
| **Qaysi entity** | `media_player.yandex_station_...` | Arylic'ning **Music Assistant'dagi** `media_player` entity'si |
| **Diqqat** | — | ❗ Xom LinkPlay/Arylic entity emas, aynan **Music Assistant** entity bo'lsin — chunki `music_assistant.play_media` faqat MA entity bilan ishlaydi |

> **Soddasi:** Alice — "kim qo'shiqni tanlaydi va boshqaradi". Arylic — "kim qo'shiqni
> sifatli chalib beradi". Blueprint Alice'dagi trekni ID orqali olib, Music Assistant
> orqali Arylic'da boshlaydi va ovozlarni almashtiradi.

---

## ✅ Talablar (Requirements)

1. **Home Assistant** 2024.6 yoki undan yangi (sozlamalar `sections` ko'rinishi uchun).
2. **[Music Assistant](https://music-assistant.io/)** integratsiyasi o'rnatilgan.
3. **Arylic / LinkPlay** speaker Music Assistant'ga player sifatida qo'shilgan.
4. **Yandex Station** Home Assistant'ga ulangan (mas.
   [AlexxIT/YandexStation](https://github.com/AlexxIT/YandexStation)) va uning
   `media_player` entity'si `media_content_id`, `media_position` atributlarini beradi.
5. Music Assistant'da Yandex Music provayderi sozlangan bo'lsa, `yandex_music://track/<id>`
   URI'lari to'g'ri ochiladi. Boshqa provayder ishlatsangiz — pastdagi
   **Advanced → Track URI prefiksi** ni o'zgartiring.

---

## 🚀 O'rnatish

### A-variant — Blueprint URL orqali (eng oson, HACS shart emas)

1. Repo'ni GitHub'ga push qiling (pastda buyruqlar bor).
2. Home Assistant'da: **Settings → Automations & Scenes → Blueprints → Import Blueprint**.
3. Quyidagi URL'larni navbatma-navbat qo'ying (`OzodbekNormamatov-git` ni o'zingiznikiga almashtiring):

   **Start:**
   ```
   https://github.com/OzodbekNormamatov-git/alice-arylic-sync/blob/main/blueprints/automation/alice_arylic/alice_arylic_handoff_start.yaml
   ```
   **Stop:**
   ```
   https://github.com/OzodbekNormamatov-git/alice-arylic-sync/blob/main/blueprints/automation/alice_arylic/alice_arylic_smooth_stop.yaml
   ```

> 💡 Yoki to'g'ridan-to'g'ri "My Home Assistant" havolasi:
> `https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=<YUQORIDAGI_URL>`

### B-variant — HACS orqali (yangilanishlarni oson olish uchun)

1. **HACS → ⋮ (yuqori o'ng) → Custom repositories**.
2. Repo URL: `https://github.com/OzodbekNormamatov-git/alice-arylic-sync`, **Type / Category: `Automation`** (Blueprint).
3. **Add** → so'ng ro'yxatdan **Alice ↔ Arylic Smooth Sync** ni **Download**.
4. HACS blueprintlarni `config/blueprints/automation/alice_arylic/` ga joylaydi.

### Avtomatika yaratish (ikkala variantdan keyin ham)

1. **Settings → Automations & Scenes → Create Automation → Use blueprint**.
2. **Smooth Handoff (Start)** ni tanlang → Alice va Arylic entity'larini belgilang →
   ovoz va timing sozlamalarini xohlovingizga moslang → **Save**.
3. Xuddi shunday **Smooth Stop & Restore** uchun ham bitta avtomatika yarating.

---

## ⚙️ Sozlamalar (to'liq ma'lumotnoma)

### Smooth Handoff (Start)

| Sozlama | Default | Ma'nosi |
|---|---|---|
| **Alice player** | — | Manba (Yandex Station) `media_player` |
| **Arylic player** | — | Chiqish (Music Assistant) `media_player` |
| **Arylic floor** | `0.05` | Arylic qaysi ovozdan boshlab ko'tariladi (5%) |
| **Arylic target** | `0.35` | Arylic yakuniy ovozi (35%) |
| **Alice end volume** | `0` | Alice qayergacha tushadi (0 = jim) |
| **Sync offset (s)** | `5.0` | ⭐ Eng muhim: Arylic'ni Alice bilan bir sekundga moslash |
| **Steps** | `12` | Crossfade qadamlari (ko'p = silliq, kam = tez) |
| **Arylic head-start (ms)** | `350` | ⭐ Arylic Alice'dan qancha oldinda yursin (kechikishni yopadi) |
| **Alice gap (ms)** | `180` | Alice tushgach keyingi qadamgacha pauza |
| **Track URI prefiksi** | `yandex_music://track/` | media_content_id oldiga qo'shiladigan URI |
| **media_type** | `track` | MA media turi |
| **Play wait timeout (s)** | `12` | Arylic "playing" bo'lishini kutish |
| **Buffer wait timeout (s)** | `6` | Seekdan keyin bufer to'lishini kutish |

**Boshlanish/oxiri (default qiymatlar bilan):**
- Arylic: `5% → 7.5% → 10% → ... → 35%` (har qadam **+2.5%**)
- Alice (mas. 60% dan): `60% → 55% → ... → 0%` (har qadam **−5%**, boshlang'ich ovozga bog'liq)

### Smooth Stop & Restore

| Sozlama | Default | Ma'nosi |
|---|---|---|
| **Alice player** | — | Start'dagi bir xil Alice entity |
| **Arylic player** | — | Start'dagi bir xil Arylic entity |
| **Arylic fade floor** | `0.01` | Pauzadan oldin Arylic shu darajaga tushadi |
| **Alice restore volume** | `0.5` | To'xtagach Alice shu ovozga qaytadi |
| **Steps** | `10` | Pasayish qadamlari |
| **Step delay (ms)** | `200` | Har qadam orasidagi kutish |

---

## 🎚 Tezkor tuning (uchta tugma yetarli)

1. **Arylic orqada eshitiladimi?** → `Sync offset` ni oshiring (6–7) **va/yoki**
   `Arylic head-start` ni oshiring (450–600 ms).
2. **Ovoz pog'onalab emas, bittada sakrab chiqyaptimi?** → `Arylic head-start` ni
   oshiring; LinkPlay ketma-ket volume buyruqlarini sekin qabul qiladi.
3. **O'tish juda tez/sekinmi?** → `Steps` ni o'zgartiring (silliqroq = ko'proq qadam).

To'liq qo'llanma: [`docs/TUNING.md`](docs/TUNING.md).

---

## 🔧 Qanday ishlaydi (Start ketma-ketligi)

1. Alice'da trek almashadi yoki ijro boshlanadi → blueprint ishga tushadi.
2. Arylic `floor` ovozga qo'yiladi, o'sha trek `music_assistant.play_media` bilan boshlanadi.
3. Arylic `playing` bo'lguncha kutiladi.
4. Alice turgan sekund hisoblanib (`sync_offset` qo'shilib), Arylic shu joyga `media_seek` qilinadi.
5. ❗ Seekdan keyin Arylic streamni qayta buferlaydi — ovoz **chiqquncha** kutiladi.
6. Navbatma-navbat crossfade: har qadam → **Arylic +** → head-start pauza → **Alice −**.
7. Oxirida Alice `end volume` (0), Arylic `target` ovozga ega bo'ladi.

---

## 🩺 Muammolarni hal qilish

- **Arylic doim 0:00 dan boshlanadi (seek ishlamaydi):** bu ko'pincha LinkPlay/MA
  cheklovi. Bunda aniq sinxron bo'lmaydi — `docs/TROUBLESHOOTING.md` da "seeksiz"
  muqobil keltirilgan.
- **O'tish o'rtada uzilib qayta boshlanadi:** `mode: restart` + tez-tez triggerlar
  sababli. `media_position` triggerini ishlatmang (bu blueprintda yo'q).
- **Alice 0 da pauza bo'lib qoladi:** ba'zi firmware'larda 0 = pauza. `Alice end volume` ni
  `0.01` qiling.

To'liq ro'yxat: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

---

## 📂 Repo tuzilishi

```
alice-arylic-sync/
├── blueprints/automation/alice_arylic/
│   ├── alice_arylic_handoff_start.yaml     # Start (crossfade handoff)
│   └── alice_arylic_smooth_stop.yaml       # Stop (fade + restore)
├── examples/                               # entity'lar to'ldirilgan tayyor avtomatikalar
├── docs/
│   ├── TUNING.md
│   └── TROUBLESHOOTING.md
├── hacs.json
├── info.md
├── README.md  /  README.en.md
├── CHANGELOG.md
└── LICENSE
```

---

## 📝 Litsenziya

MIT — [`LICENSE`](LICENSE). Erkin foydalaning, o'zgartiring, ulashing.

English version: [`README.en.md`](README.en.md).
