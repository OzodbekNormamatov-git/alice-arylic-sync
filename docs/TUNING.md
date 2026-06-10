# 🎚 Tuning qo'llanmasi

Bu yerda har bir sozlamani qanday his bilan moslash kerakligi tushuntirilgan.
Eng ko'p ta'sir qiladigan uchta narsa: **Sync offset**, **Arylic head-start**, **Steps**.

---

## 1. Sync offset (soniya) — eng muhim

Arylic Alice bilan **bir xil sekunddan** chiqishi uchun. Seek qilinganda Arylic
biroz buferlanadi, shuning uchun unga "oldinroq" pozitsiya berib, vaqt yo'qotishini
qoplaymiz.

| Belgisi | Yechim |
|---|---|
| Arylic Alice'dan **orqada** (kechroq) eshitiladi | offset'ni **oshiring** (mas. 5 → 6.5) |
| Arylic Alice'dan **oldinda** (ertaroq) | offset'ni **kamaytiring** (mas. 5 → 3.5) |
| Har safar har xil | tarmoq beqaror — `Buffer wait timeout` ni 8 ga oshirib ko'ring |

> Aniq moslash uchun bir trekni qo'ying, ikkala speakerni yonma-yon eshiting va
> 0.5s qadam bilan offsetni surib boring.

---

## 2. Arylic head-start (ms)

Har crossfade qadamida **avval Arylic ko'tariladi**, keyin shu `head-start`
millisekunddan **keyin** Alice tushadi. Bu Arylic'ning buyruq qabul qilish
kechikishini yopadi — quloqqa Arylic doim biroz oldinda bo'lib eshitiladi.

| Belgisi | Yechim |
|---|---|
| Arylic baribir orqada | **oshiring** → 450, 550, 600 ms |
| O'tish juda cho'zilyapti | **kamaytiring** → 250, 200 ms |
| Ovoz pog'onalab emas, sakrab chiqyapti | **oshiring** (LinkPlay sekin qabul qiladi) |

---

## 3. Steps (qadamlar soni)

Ovoz necha bo'lakka bo'linib o'zgaradi.

| Qiymat | Natija |
|---|---|
| Kam (6–8) | Tez, lekin pog'onalar sezilarli |
| O'rta (12) | Muvozanat (tavsiya) |
| Ko'p (18–24) | Juda silliq, lekin sekinroq + LinkPlay debounce xavfi ortadi |

**O'tish umumiy davomiyligi (taxminan):**
`steps × (Arylic head-start + Alice gap)`.
Mas. `12 × (350 + 180) ms ≈ 6.4 soniya`.

---

## 4. Ovoz darajalari

- **Arylic floor (0.05):** 0 emas, 5% — chunki 0 dan boshlansa, birinchi qadam
  juda sezilarli sakraydi. Xohlasangiz 0.02–0.08 oralig'ida o'ynang.
- **Arylic target (0.35):** xonangizga qarab 0.30–0.60. Avval pastroqdan boshlang.
- **Alice end volume (0):** to'liq jim. Ba'zi firmware 0 da pauza qiladi —
  unda **0.01** qiling.

Arylic qadami = `(target − floor) / steps`.
Alice qadami = `alice_start_volume / steps` (boshlang'ich ovozga bog'liq).

---

## 5. Stop blueprint

- **Arylic fade floor (0.01):** pauzadan oldingi eng past ovoz.
- **Alice restore volume (0.5):** to'xtagach Alice qaytadigan ovoz — odatda
  Start'dagi tipik Alice ovozi bilan bir xil qo'ying, shunda keyingi safar
  crossfade bir xil his beradi.
- **Step delay (200ms) × Steps (10) = 2s** pasayish.

---

## Tavsiya etilgan startlar (presetlar)

| Vaziyat | Sync offset | Head-start | Steps |
|---|---|---|---|
| Tezkor, sezgir tarmoq | 4.0 | 300 | 10 |
| Muvozanat (default) | 5.0 | 350 | 12 |
| Sekin/beqaror Wi-Fi, Arylic kechikadi | 6.5 | 550 | 14 |
