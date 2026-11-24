# لوحة تحكم الأمان السيبراني

[![Python app](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)
[![Python 3.15+](https://img.shields.io/badge/python-3.15%2B-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/Qt-PySide6%20%E2%89%A5%206.12-green.svg)](https://pypi.org/project/PySide6/)
[![Tests](https://img.shields.io/badge/tests-54%20passed-brightgreen.svg)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)
[![Release](https://img.shields.io/badge/release-v1.1.1-blue.svg)](https://github.com/CHM2026/Local-Cybersec-Partner/releases/latest)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)

> اللغات: [Français](README.md) · [English](README.en.md) · **العربية**

لوحة تحكم محلية تجمع عدة أدوات الأمان السيبراني، مبنية باستخدام **PySide6**.

## معاينة

داكن (السمة الأصلية):

![لوحة التحكم بالعربية — داكنة](docs/screenshots/dashboard-ar-dark.png)

فاتح 2026:

![لوحة التحكم بالعربية — فاتحة 2026](docs/screenshots/dashboard-ar-light.png)

صفحة **🆕 التحديث** (السمة الداكنة):

![صفحة التحديث بالعربية — داكنة](docs/screenshots/update-ar-dark.png)

> ⚠️ **المتطلب: Python 3.15 أو أحدث.** يستخدم الكود صيغة `lazy import` (PEP 810) والسلاسل النصية المتداخلة f-strings (PEP 701). على Python ≤ 3.14 يفشل التشغيل مع ظهور `SyntaxError`.

## التثبيت

مطلوب Python 3.15 أو أحدث. حسب نظام التشغيل:

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

على Windows، إذا كان `python` يشير إلى إصدار أقدم، استخدم `py -3.15` بدلاً منه.

للتطوير (بما في ذلك الاختبارات)، استبدل `requirements.txt` بـ `requirements.dev.txt` في أمر التثبيت أعلاه.

### ويندوز: محمول أو مثبّت (بدون بايثون)

من صفحة [Releases](https://github.com/CHM2026/Local-Cybersec-Partner/releases)،
نزّل أحد ملفات ويندوز:

- `CyberSecDashboard-<version>-portable.zip`: استخرجه ثم شغّل `CyberSecDashboard.exe`.
  يؤدي وجود `portable.txt` إلى حفظ التفضيلات في `settings.ini` بجانب الملف التنفيذي
  (دون كتابة أي شيء في سجل النظام)؛
- `CyberSecDashboard-<version>-setup.exe`: تثبيت عادي مع اختصار في قائمة ابدأ؛
  يُلغى التثبيت من *الإعدادات ← التطبيقات*.

لا حاجة إلى بايثون لأي من الصيغتين. يتيح ملف `SHA256SUMS.txt` المرفق بالإصدار
التحقق من سلامة الملفات المنزّلة.

## التشغيل

### من المستودع (للتطوير)

```powershell
# Windows
.\.venv\Scripts\python.exe main.py
```

```bash
# macOS / Linux
./.venv/bin/python main.py
```

### بعد التثبيت عبر pip (للمستخدم النهائي)

أي تثبيت للحزمة عبر pip ينشئ الأمر **`cybersec-dashboard`**، سواء من
`pip install -e .` أو من ملف wheel التابع للإصدار أو من وسم Git :

```bash
cybersec-dashboard
```

**ويندوز — « الأمر غير معروف »؟** مجلد `Scripts` الخاص ببايثون غير موجود في
`PATH`. حلّان :

- بدون أي إعداد : `py -3.15 -m main`
- أو أضفه مرة واحدة نهائيًا (ثم **أعد فتح PowerShell**) :

```powershell
$p = "$env:LOCALAPPDATA\Python\pythoncore-3.15-64\Scripts"
$old = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$old;$p", "User")
```

اضبط `3.15-64` إذا كانت بايثون مثبتة في مكان آخر على جهازك.

## إلغاء التثبيت

```powershell
# ويندوز (بايثون 3.15 العام)
py -3.15 -m pip uninstall local-cybersec-partner
```

```bash
# macOS / Linux
python3 -m pip uninstall local-cybersec-partner
```

استخدم **اسم الحزمة** (`local-cybersec-partner`) وليس اسم الأمر
(`cybersec-dashboard`). يقوم pip أيضًا بإزالة الأمر من مجلد `Scripts`.
تبقى تفضيلات اللغة والسمة محفوظة لديك.

## الوحدات

| الوحدة | الوصف |
|---|---|
| ⬡ لوحة التحكم | معلومات النظام والوصول السريع إلى الوحدات |
| 🔑 كلمات المرور | توليد عشوائي آمن عبر `secrets` (الطول، مجموعة الأحرف، الكمية) |
| 💪 قوة كلمة المرور | تحليل المعايير، النقاط، والإنتروبيا التقديرية |
| 🔒 التجزئة | MD5 و SHA-1 و SHA-256 و SHA-384 و SHA-512 لنص ما |
| 📄 سلامة الملف | بصمة الملف (خارج خيط الواجهة) ومقارنتها ببصمة مرجعية |
| 🔍 ماسح المنافذ | فحص TCP Connect لمدى من المنافذ (مضيف تم حله ومهلة زمنية مُتحقّق منها) |
| ⚙️ Base64 | ترميز/فك ترميز صارم، مع عرض سداسي عشري للبيانات الثنائية |
| 🌐 الشبكة | معلومات محلية، حل DNS غير متزامن، ping |
| 🆕 التحديث | البحث عن إصدارات GitHub، تنزيل موجّه، والتحقق من SHA-256 |
| 📋 السجل | سجل الإجراءات، مسحه، وتصديره كنص |

## تعدد اللغات (FR / EN / AR)

يتيح محدد **🌐 اللغة** في أسفل الشريط الجانبي التبديل بين **Français** و **English** و **العربية**. يتم حفظ الاختيار (`QSettings`) واستعادته عند التشغيل التالي.

- **واجهة كاملة**: العناوين، التسميات، الأزرار، الرسائل، التلميحات، وإدخالات السجل مترجمة.
- **سجل بأثر رجعي**: تُخزّن الإدخالات كمفاتيح مع معاملاتها؛ وتُترجم مجددًا عند العرض عند تغيير اللغة، بما في ذلك التصدير النصي.
- **اتجاه RTL تلقائي**: اختيار العربية يعكس تخطيط الواجهة (`RightToLeft`) والمحاذات (`text-align: start`).
- **حوارات Qt مترجمة**: تستخدم النصوص الخاصة بـ Qt (أزرار موافق/إلغاء، نوافذ اختيار الملفات) ملفات `qtbase_*.qm` المُثبّتة عبر `QTranslator` من مسار الترجمة الافتراضي في Qt.
- **الحفاظ على الحالة**: تُحفظ الإدخالات الجارية وتُعاد حساب النتائج دون إنشاء إدخال جديد في السجل.

لإضافة ترجمة أو تصحيحها، عدّل `src/i18n.py`: كل مفتاح في قاموس `STRINGS` يحتوي على الثلاثية `(français, english, العربية)`.

## السمات

تتوفر لوحتان عبر محدد **🎨 السمة** في الشريط الجانبي:

- **داكن**: السمة السيبرانية الأصلية (خلفية `#0d1117`، ألوان أخضر/سماوي).
- **فاتح 2026**: لوحة عصرية بخلفية فاتحة `#f6f8fb`، ألوان أزرق/سماوي وخط `Segoe UI`.

يُحفظ الاختيار (`QSettings`) ويُستعاد عند التشغيل. زر **📸 لقطة شاشة** يحفظ العرض الحالي بصيغة PNG.

## التحديث

تستعلم صفحة **🆕 التحديث** واجهة GitHub العامة مرة واحدة يومياً عند التشغيل
(يمكن تعطيلها عبر مربع الاختيار)، أو عند الطلب بزر **تحقق الآن**. تعرض الصفحة
الإصدار المثبّت والإصدار المتاح وملاحظات الإصدار.

يزر **تنزيل التحديث** الملف المناسب لوضع التثبيت الحالي:

- تثبيت **pip**: يظهر الأمر `py -3.15 -m pip install --upgrade …` ويمكن نسخه؛
- **محمول**: يُستخرج أرشيف ZIP في مجلد مجاور باسم `CyberSecDashboard-vX.Y.Z`؛
- **مثبّت ويندوز**: يُنزّل ملف `-setup.exe` إلى مجلد التنزيلات، ثم يُشغَّل بعد تأكيدك فقط.

الاتصال **HTTPS فقط**، وتُتحقق بصمة `SHA256SUMS.txt` عند نشرها، ولا يُثبَّت أي
شيء دون موافقتك. في الوضع المحمول تُحفظ التفضيلات في `settings.ini` بجانب
الملف التنفيذي (بوجود الملف `portable.txt`)؛ وفي الوضعين الآخرين تبقى في سجل النظام.

## الأمان والنطاق

- لا تُرسل أي كلمة مرور أو ملف أو بصمة إلى خدمة خارجية: تُعالَج كل البيانات محليًا.
- فحص المنافذ وحل DNS و ping تتصل **بالهدف الذي تُدخله فقط**.
- استخدم الماسح فقط على المضيفين الذين تملكهم أو الذين لديك إذن صريح باختبارهم.
- تُبقى MD5 و SHA-1 لأغراض التوافق؛ **يُنصح بـ SHA-256** لأي تحقق من السلامة.
- السجل المُصدَّر ملف نصي غير مشفر: لا تخزّنه في موقع مشترك.
- عند الإغلاق، توقف التطبيق خيوطه وتمسح البيانات الحساسة (الحقول، البصمات، السجل، الحافظة إذا كان التطبيق هو من كتبها).
- يُجري فاحص التحديثات **طلب HTTPS واحداً** إلى GitHub (لا قياس عن بُعد ولا إرسال لأي بيانات محلية) ولا يثبّت أي شيء تلقائياً.

## الاختبارات

```powershell
# Windows
.\.venv\Scripts\python.exe -m pytest
```

```bash
# macOS / Linux
./.venv/bin/python -m pytest
```

تُشغّل الاختبارات في وضع Qt `offscreen`: لا تُفتح أي نافذة.

## لقطات الشاشة

- **من التطبيق**: انقر على **📸 لقطة شاشة** في الشريط الجانبي، ثم اختر مسار ملف PNG.
- **من الطرفية** (مثالي للتوثيق و CI):

```bash
python tools/screenshots.py
python tools/screenshots.py --native --theme light
python tools/screenshots.py --pages dashboard,update --out docs/screenshots
```

يُنشئ السكربت `docs/screenshots/<page>-<language>-<theme>.png` للفرنسية والإنجليزية والعربية، بالسمة الداكنة والفاتحة. افتراضياً يعمل في وضع `offscreen` (بدون نافذة، مثالي لـ CI)، لكن الرموز التعبيرية تظهر بالأبيض والأسود.

للحصول على **رموز تعبيرية ملوّنة**، أضف `--native` (يتطلب وجود شاشة):

```bash
python tools/screenshots.py --native
```

الصور المعروضة أعلاه أُنشئت باستخدام `--native`. على Windows استخدم `.\.venv\Scripts\python.exe tools\screenshots.py --native` عند الحاجة.

**الخصوصية:** يتم استبدال اسم الجهاز والمعالج بـ `DEMO-PC` و `Synthetic CPU (demo)`، لذا يمكن نشر اللقطات دون بيانات شخصية. الخيار `--real-data` يوقف هذا التمويه (للاستخدام المحلي فقط). تجنّب التقاط صفحة **الشبكة** عناوين IP حقيقية.

## البنية

```
main.py              التطبيق (النافذة، الصفحات، خيوط العمل)
src/constants.py     الألوان، جدول المنافذ، اسم التطبيق وإصداره
src/i18n.py          قواميس FR/EN/AR، محرك الترجمة، محدد RTL
src/runtime.py       أوضاع pip/المثبّت/المحمول، الإعدادات
src/updater.py       إصدارات GitHub، البصمات، الأرشيف الآمن
tests/               الاختبارات الآلية
tools/screenshots.py مُولّد لقطات FR/EN/AR (بدون نافذة)
tools/build_windows.py   PyInstaller + أرشيف محمول
tools/write_sha256sums.py بصمات الملفات المنشورة
installer/           سكربت Inno Setup (مثبّت ويندوز)
requirements.txt     تبعية التشغيل
requirements.dev.txt تبعيات التطوير
pyproject.toml       البيانات الوصفية، نقطة الدخول، إعداد pytest
```

## الترخيص والنشر

يُوزّع هذا المشروع بموجب [ترخيص MIT](LICENSE). سجل الإصدارات في
[CHANGELOG.md](CHANGELOG.md)، وإجراء نشر الوسوم (`v1.0.0` و`v1.1.0` و`v1.1.1`) في
[docs/RELEASE.md](docs/RELEASE.md).
