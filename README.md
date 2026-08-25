# KEYGEN

#### Description:

KEYGEN is an offline Windows desktop app written only in Python. It creates strong passwords, passphrases, and PINs, estimates how hard they are to guess, can lengthen a weak password with extra random characters, and stores logins in a local encrypted vault. There is no website, no account, and no internet use while it runs.

You start it with `python project.py`. A native window opens (PySide6 / Qt Widgets). The Generator page is the home screen: pick Password, Passphrase, or PIN, press Generate, then Copy or Save to Vault. The Vault page looks like a password list even when locked; rows stay blurred until you enter the master password. There is no recovery for that password — only a full wipe.

---

## What it does

- **Password** — 4–64 characters, optional upper / lower / digits / symbols, optional skip of look-alike characters (`0 O o 1 l I |`). Randomness comes from Python’s `secrets` module, not `random`.
- **Passphrase** — 3–12 words from a fixed 512-word list (9 bits per word), with a chosen separator.
- **PIN** — numeric only, length 4–12.
- **Fortifier** — appends extra CSPRNG characters to a string you type.
- **Strength** — entropy bits, a level (WEAK … VERY STRONG), and a short crack-time estimate. Only very short, low-diversity strings are called weak.
- **Vault** — AES-256-GCM file on disk (`%USERPROFILE%\.keygen\vault.bin`). The master password is never stored.
- **Export / import** — encrypted `.bin` for KEYGEN only; Chrome-style CSV (`name,url,username,password`) for browsers; JSON; readable TXT or Markdown. CSV / JSON / TXT / MD are **not** encrypted.

---

## How it works

1. Generate uses `secrets` so each output is cryptographically random.
2. If several character classes are on, the generator forces at least one character from each class, then shuffles.
3. Strength is `length × log2(pool)` for passwords and `words × 9` for passphrases. Times are estimates, not promises.
4. Unlocking the vault derives a key with PBKDF2-HMAC-SHA256 (200 000 iterations) and decrypts the file. Wrong password fails cleanly.
5. A forgotten master password cannot be reset except by deleting the vault file.

---

## Files

- `project.py` — `main()` starts the GUI. Also defines top-level `generate_password`, `generate_passphrase`, and `calculate_strength` (required by CS50P), plus `generate_pin` and `fortify_password`.
- `test_project.py` — `test_generate_password`, `test_generate_passphrase`, `test_calculate_strength`.
- `requirements.txt` — `PySide6`, `cryptography`, `pytest`, `pyinstaller`.
- `app/` — window, custom widgets, painted icons, themes, dialogs, animations.
- `core/` — generator, word list, strength math, crypto, vault file I/O.
- `packaging/` — PyInstaller spec, Inno Setup script, icon, `build.bat`.
- `tools/make_icon.py` — builds `packaging/app.ico`.

---

## Design choices

- **Desktop, not a web page** — the course and the product both need Python-only, offline code. A browser UI would have broken that rule.
- **Custom-painted widgets** — default Qt looks like a class demo; KEYGEN is meant to look like a small real utility (orange `#FF5A1F` on near-black).
- **Icons drawn in Python** — no CDN, no icon fonts, works offline.
- **Blurred vault instead of an empty lock screen** — you see the layout; secrets stay hidden until unlock.
- **Wipe instead of “forgot password”** — recovering a vault without the master key would mean storing that key, which we refuse to do.
- **Browser CSV as its own export** — Chrome/Edge/Firefox expect `name,url,username,password` and a real `https://` URL. A `.bin` file is useless to a browser.

---

## Why the project folder and the installed app differ in size

- The **source tree** is small: Python files plus one icon.
- The **installed app** is large (tens of megabytes) because PyInstaller copies the Python runtime and Qt. That is the toolkit, not extra features.
- `packaging/keygen.spec` drops unused Qt pieces (WebEngine, QML, Multimedia). Visual quality stays the same. Going much smaller would mean leaving Qt.

---

## For users

**Run from source (Windows):**

1. Install Python 3.12+.
2. Open a terminal in this folder.
3. `python -m venv .venv` then `.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. `python project.py`

**Install a built copy:**

- Double-click `dist\keygen-setup.exe` if you have a build (picks a folder; optional desktop shortcut; no license page).
- Or run `dist\KEYGEN\KEYGEN.exe` directly (portable).
- Unsigned builds may show Windows SmartScreen. That is normal without a paid code-signing certificate. Use **More info → Run anyway** on your own PC.

Vault data stays on your machine. JSON/CSV/TXT exports are readable by anyone who has the file — delete them after use.

---

## For developers

**Tests (required for CS50):**

```text
pytest test_project.py -q
```

**Build on Windows** (needs [Inno Setup 6](https://jrsoftware.org/isinfo.php) for the setup program):

```text
packaging\build.bat
```

Output:

- `dist\KEYGEN\KEYGEN.exe` — the application
- `dist\keygen-setup.exe` — the installer (only if Inno Setup is installed)

Optional local signing (this computer only): the build script can create a self-signed cert. It will **not** clear SmartScreen for other people. Public release needs a paid Authenticode certificate (`packaging\sign.bat`).

---

KEYGEN is a CS50P final project: one `project.py`, three tested helpers, a real desktop program, and more work than a single problem set. Paste the YouTube demo URL on the Video Demo line before you submit.
