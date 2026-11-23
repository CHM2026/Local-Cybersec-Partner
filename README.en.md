# CyberSec Dashboard

[![Python app](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)
[![Python 3.15+](https://img.shields.io/badge/python-3.15%2B-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/Qt-PySide6%20%E2%89%A5%206.12-green.svg)](https://pypi.org/project/PySide6/)
[![Tests](https://img.shields.io/badge/tests-21%20passed-brightgreen.svg)](https://github.com/CHM2026/Local-Cybersec-Partner/actions/workflows/python-app.yml)

> Languages: [Français](README.md) · **English** · [العربية](README.ar.md)

Local dashboard bringing together several cybersecurity utilities, built with **PySide6**.

> ⚠️ **Requirement: Python 3.15 or later.** The code uses the `lazy import` syntax (PEP 810) and nested f-strings (PEP 701). On Python ≤ 3.14, startup fails with a `SyntaxError`.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For development (tests included):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.dev.txt
```

## Running

```powershell
.\.venv\Scripts\python.exe main.py
```

If the project was installed with `pip install -e .`:

```powershell
cybersec-dashboard
```

## Modules

| Module | Description |
|---|---|
| ⬡ Dashboard | System information and prioritized access to the modules |
| 🔑 Passwords | CSPRNG generation via `secrets` (length, character set, quantity) |
| 💪 Password strength | Criteria analysis, score, indicative entropy |
| 🔒 Hashing | MD5, SHA-1, SHA-256, SHA-384, SHA-512 of a text |
| 📄 File integrity | File hash (outside the GUI thread) and comparison with a reference hash |
| 🔍 Port scanner | TCP Connect scan of a port range (resolved host and validated timeout) |
| ⚙️ Base64 | Strict encoding/decoding, with hexadecimal display for binary data |
| 🌐 Network | Local information, asynchronous DNS resolution, ping |
| 📋 Log | Action history, clearing and text export |

## Multilingual (FR / EN / AR)

The **🌐 Language** selector at the bottom of the sidebar switches between **Français**, **English** and **العربية**. The choice is saved (`QSettings`) and restored on the next launch.

- **Complete interface**: titles, labels, buttons, messages, tooltips and log entries are translated.
- **Retroactive log**: entries are stored as keys with their parameters; they are re-translated on display when the language changes, including in the text export.
- **Automatic RTL**: selecting Arabic reverses the layout (`RightToLeft`) and alignments (`text-align: start`).
- **State preservation**: in-progress inputs are kept and results are recalculated without creating a new log entry.

To add or fix a translation, edit `src/i18n.py`: each key in the `STRINGS` dictionary holds the `(français, english, العربية)` triplet.

## Security and scope

- No password, file or hash is sent to a third-party service: everything is processed locally.
- Port scanning, DNS resolution and ping contact **only the target you enter**.
- Only use the scanner on hosts you own or are explicitly authorized to test.
- MD5 and SHA-1 are kept for compatibility; **SHA-256 is recommended** for any integrity check.
- The exported log is an unencrypted text file: do not store it in a shared location.
- On exit, the application stops its threads and clears sensitive data (fields, hashes, log, clipboard if the application owned it).

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Tests run in Qt `offscreen` mode: no window is opened.

## Structure

```
main.py              Application (window, pages, worker threads)
src/constants.py     Palette, port table, app name and version
src/i18n.py          FR/EN/AR dictionaries, translation engine, RTL selector
tests/               Automated tests
requirements.txt     Runtime dependency
requirements.dev.txt Development dependencies
pyproject.toml       Metadata, entry point, pytest configuration
```
