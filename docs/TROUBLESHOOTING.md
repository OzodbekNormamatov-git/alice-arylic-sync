# 🩺 Muammolarni hal qilish

## Arylic doim 0:00 dan boshlanadi (seek ishlamaydi)

LinkPlay/Arylic ba'zi rejimlarda `media_seek` ni Music Assistant orqali to'liq
qo'llab-quvvatlamaydi. Bunda trek har doim boshidan chiqadi va aniq sinxron
bo'lmaydi.

**Yechim — "seeksiz" rejim:** Start avtomatikasida `media_seek` qadamini va
undan keyingi "buffer wait" qadamini olib tashlang. Sinxron bo'lmaydi, lekin
crossfade silliq ishlaydi (yangi trek 0:00 dan boshlangani uchun normal his beradi).

---

## O'tish o'rtada uzilib qayta boshlanadi

Sabab: ko'p triggerlar + `mode: restart`. Bu blueprintda atayin faqat ikki
trigger bor:
- `media_content_id` o'zgarishi (yangi trek),
- `to: playing`.

Agar baribir uzilsa, `to: playing` triggerini vaqtincha olib turing va faqat
trek almashganda ishlasin.

> ❌ `media_position below: 2` triggerini **qo'shmang** — u trek o'rtasida ham
> yonib, o'tishni uzib qo'yadi.

---

## Alice 0 ga tushganda pauza bo'lib qoladi

Ba'zi Yandex firmware'larida `volume = 0` pauzani anglatadi. Start blueprintda
**Alice end volume** ni `0.01` qiling.

---

## Ikkala speaker bir vaqtda gapiryapti (echo) — Start boshida

Bu odatda head-start juda kichik yoki Arylic juda erta ko'tarilganda bo'ladi.
- **Arylic floor** ni pasaytiring (0.05 → 0.03).
- **Steps** ni biroz oshiring (12 → 14), shunda boshlanish yumshoqroq.

---

## Arylic ovozi pog'onalab emas, oxirida bittada sakrab chiqadi

LinkPlay ketma-ket volume buyruqlarini "debounce" qiladi (juda tez kelganini
o'tkazib yuboradi).
- **Arylic head-start** ni oshiring (350 → 500–600 ms).
- **Steps** ni kamaytiring (kamroq, lekin ishonchli sakrash).

---

## music_assistant.play_media xato beradi

- Chiqish entity'si haqiqatan **Music Assistant** `media_player` ekanini tekshiring
  (xom LinkPlay emas).
- **Track URI prefiksi** to'g'rimi? Yandex Music uchun `yandex_music://track/`.
  Boshqa provayder bo'lsa, MA hujjatlaridagi to'g'ri URI sxemasini qo'ying.
- MA'da o'sha provayder (mas. Yandex Music) ulanganini tekshiring.

---

## Trek ID topilmayapti / bo'sh

Start blueprintdagi shartlar `media_content_id` `none/''/unknown/unavailable`
bo'lsa ishlamaydi. Alice ba'zan radio yoki podkast chalganda `media_content_type`
`music` bo'lmaydi — bu holda blueprint ataylab ishlamaydi (faqat musiqa uchun).

---

## Logni qanday ko'rish

Avtomatika sahifasida **⋮ → Traces** orqali har bir qadamni va template
qiymatlarini ko'rishingiz mumkin — qaysi qadamda timeout bo'lganini aniqlash uchun
juda foydali.
