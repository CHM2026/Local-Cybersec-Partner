# لوحة تحكم الأمان السيبراني

[![Python app](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)
[![Python 3.15+](https://img.shields.io/badge/python-3.15%2B-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/Qt-PySide6%20%E2%89%A5%206.12-green.svg)](https://pypi.org/project/PySide6/)
[![Tests](https://img.shields.io/badge/tests-21%20passed-brightgreen.svg)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)

> اللغات: [Français](README.md) · [English](README.en.md) · **العربية**

لوحة تحكم محلية تجمع عدة أدوات الأمان السيبراني، مبنية باستخدام **PySide6**.

> ⚠️ **المتطلب: Python 3.15 أو أحدث.** يستخدم الكود صيغة `lazy import` (PEP 810) والسلاسل النصية المتداخلة f-strings (PEP 701). على Python ≤ 3.14 يفشل التشغيل مع ظهور `SyntaxError`.

## التثبيت

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

للتطوير (بما في ذلك الاختبارات):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.dev.txt
```

## التشغيل

```powershell
.\.venv\Scripts\python.exe main.py
```

إذا تم تثبيت المشروع باستخدام `pip install -e .`:

```powershell
cybersec-dashboard
```

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
| 📋 السجل | سجل الإجراءات، مسحه، وتصديره كنص |

## تعدد اللغات (FR / EN / AR)

يتيح محدد **🌐 اللغة** في أسفل الشريط الجانبي التبديل بين **Français** و **English** و **العربية**. يتم حفظ الاختيار (`QSettings`) واستعادته عند التشغيل التالي.

- **واجهة كاملة**: العناوين، التسميات، الأزرار، الرسائل، التلميحات، وإدخالات السجل مترجمة.
- **سجل بأثر رجعي**: تُخزّن الإدخالات كمفاتيح مع معاملاتها؛ وتُترجم مجددًا عند العرض عند تغيير اللغة، بما في ذلك التصدير النصي.
- **اتجاه RTL تلقائي**: اختيار العربية يعكس تخطيط الواجهة (`RightToLeft`) والمحاذات (`text-align: start`).
- **الحفاظ على الحالة**: تُحفظ الإدخالات الجارية وتُعاد حساب النتائج دون إنشاء إدخال جديد في السجل.

لإضافة ترجمة أو تصحيحها، عدّل `src/i18n.py`: كل مفتاح في قاموس `STRINGS` يحتوي على الثلاثية `(français, english, العربية)`.

## الأمان والنطاق

- لا تُرسل أي كلمة مرور أو ملف أو بصمة إلى خدمة خارجية: تُعالَج كل البيانات محليًا.
- فحص المنافذ وحل DNS و ping تتصل **بالهدف الذي تُدخله فقط**.
- استخدم الماسح فقط على المضيفين الذين تملكهم أو الذين لديك إذن صريح باختبارهم.
- تُبقى MD5 و SHA-1 لأغراض التوافق؛ **يُنصح بـ SHA-256** لأي تحقق من السلامة.
- السجل المُصدَّر ملف نصي غير مشفر: لا تخزّنه في موقع مشترك.
- عند الإغلاق، توقف التطبيق خيوطه وتمسح البيانات الحساسة (الحقول، البصمات، السجل، الحافظة إذا كان التطبيق هو من كتبها).

## الاختبارات

```powershell
.\.venv\Scripts\python.exe -m pytest
```

تُشغّل الاختبارات في وضع Qt `offscreen`: لا تُفتح أي نافذة.

## البنية

```
main.py              التطبيق (النافذة، الصفحات، خيوط العمل)
src/constants.py     الألوان، جدول المنافذ، اسم التطبيق وإصداره
src/i18n.py          قواميس FR/EN/AR، محرك الترجمة، محدد RTL
tests/               الاختبارات الآلية
requirements.txt     تبعية التشغيل
requirements.dev.txt تبعيات التطوير
pyproject.toml       البيانات الوصفية، نقطة الدخول، إعداد pytest
```
