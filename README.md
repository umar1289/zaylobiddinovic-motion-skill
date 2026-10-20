# zaylobiddinovic-motion

[English](README.en.md) · **O'zbekcha**

Claude Code uchun skill: videolaringiz uchun rejissyor, motion dizayner, montajchi va ovoz dizayneri vazifasini bajaradi. Videoni tasvirlab berasiz, Claude esa namuna (reference) videolaringizni tahlil qiladi, ovoz uchun ssenariy va storyboard yozadi, tasdiqlash uchun vizual dizayn faylini tayyorlaydi, kod bilan chizilgan animatsiyani headless Chrome'da deterministik render qiladi, har bir o'zgarishni vaqt belgili kontakt varaqlarda tekshiradi va versiyalangan tayyor faylni topshiradi. After Effects kerak emas.

**Nimalar qila oladi**

- Motion grafika: kinetik tipografiya, tushuntiruvchi videolar, UI/SaaS promolar, logotip animatsiyalari, 2D va 3D (Three.js / React Three Fiber) sahnalar
- Uchta pipeline: A, kod bilan chizilgan; B, AI rasmlar va kod aralash; C, tayyor footage montaji (gapiruvchi shaxs, darsliklar, UGC)
- Reference tahlili: vaqt belgili kontakt varaqlar, hook'ning har bir kadri, sahna kesimlari, spektrogramma, tovush boshlanish (onset) nomzodlari
- Ovoz yozuvi (voiceover): ElevenLabs'ga qo'yishga tayyor ssenariylar va so'z byudjeti; vaqt sizning yakuniy yozuvingizga qulflanadi
- Ovoz dizayni: bir xil seed bilan har safar bir xil chiqadigan protsedurali SFX, tekshiriladigan katalogli o'z litsenziyali kutubxonangiz, ixtiyoriy ElevenLabs generatsiyasi, ixtiyoriy lokal CLAP/PANNs tahlili
- Loyiha xotirasi (`TASTE.md`, `PROGRESS.md`, `LOG.md`, `manifest.json`): yangi chatda ham uslub saqlanadi
- Sifat nazorati va topshirish: xavfsiz zonalar, kontrast, sinxronlik, ovoz balandligi (−14 LUFS / −1,5 dBTP), litsenziyalar, versiyalangan fayllar

## O'rnatish

Claude Code ichida:

```
/plugin marketplace add umar1289/zaylobiddinovic-motion-skill
/plugin install zaylobiddinovic-motion@zaylobiddinovic-motion
```

Yoki `skills/zaylobiddinovic-motion/` papkasini `~/.claude/skills/` (hamma loyihalar uchun) yoki `<loyiha>/.claude/skills/` (bitta loyiha uchun) ichiga nusxalang. Claude ilovasi va muhit cheklovlari haqida `skills/zaylobiddinovic-motion/reference/installation.md` ga qarang.

## Talablar

- Python 3.10+ (yordamchi skriptlar uchun)
- FFmpeg va ffprobe
- Node.js 18+, Playwright va Chromium (kod bilan chizilgan sahnalarni render qilish uchun)
- Ixtiyoriy: NumPy + SciPy (protsedurali SFX), librosa + soundfile (to'lqin shakli tahlili), Pillow (yorliqli reference varaqlar)
- Ixtiyoriy: ElevenLabs API kaliti (`ELEVENLABS_API_KEY`), generatsiya qilingan ovoz effektlari uchun

Tekshirish:

```bash
python3 skills/zaylobiddinovic-motion/scripts/preflight.py
```

Bu tekshiruv faqat o'qiydi, hech narsani o'zgartirmaydi. Claude paket o'rnatishdan, model yuklab olishdan yoki pullik API chaqirishdan oldin ruxsat so'raydi.

## Sinab ko'ring

- "10 soniyalik kinetik tipografiya videosi yasab ber."
- "Mana namuna reel. Uni tahlil qilib, mening ilovam uchun shunga o'xshash video yasab ber."
- "Mahsulotim haqida ElevenLabs uchun 30 soniyalik ovoz ssenariysi yoz."
- "Faqat shu loyihadagi 0:04 dagi sarlavha o'lchamini tuzat."
- "Ovoz effektlari qo'sh: har bir so'zga yumshoq tik, kartochka tushganda pop."

## Ichida nima bor

```
skills/zaylobiddinovic-motion/
  SKILL.md            Claude amal qiladigan ish jarayoni
  reference/          rejalashtirish, vizual dizayn, ovoz yozuvi, 3D, ovoz, shriftlar, retseptlar, topshirish qo'llanmalari
  scripts/            preflight, reference tahlili, oraliq previewlar, SFX vositalari, env yordamchilari
  templates/          TASTE.md, design.html, SFX katalogi, deterministik render starteri
```

`SKILL.md` va `reference/` ichidagi qo'llanmalar ingliz tilida yozilgan. Claude bilan o'zbekcha gaplashishingiz mumkin.

## Litsenziya

MIT litsenziyasi (`LICENSE` ga qarang). Uchinchi tomon dasturlari, modellari, shriftlari, footage, musiqa va ovoz effektlari o'z litsenziyalari ostida qoladi; videolaringizda ishlatgan materiallar huquqlari uchun o'zingiz javobgarsiz.
