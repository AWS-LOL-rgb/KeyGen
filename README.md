<div align="center">

# 🔐 KEYGEN

### A fast, offline password & credential vault for Windows — built entirely with Python.

<p>
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/PySide6-Qt%20Widgets-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6" />
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows" />
  <img src="https://img.shields.io/badge/Offline-100%25-111111?style=for-the-badge&logo=protonvpn&logoColor=white" alt="Offline" />
</p>

<p>
  Generate strong passwords, memorable passphrases and secure PINs, estimate strength, and keep credentials inside a local encrypted vault — with no account and no network connection required.
</p>

</div>

---

## ✨ Overview

**KEYGEN** is a lightweight Windows desktop application designed to make secure credential generation simple and pleasant to use.

It runs locally, uses Python's cryptographically secure `secrets` module for generated values, and stores vault data on your own machine. There is no website, no account system, and no cloud service involved while the application is running.

The home screen is the **Generator**, where you can create a password, passphrase, or PIN and then copy it or save it to the vault. The **Vault** keeps its entries visually blurred while locked, so the interface remains useful without exposing the secrets behind it.

> 🔒 **Privacy by design:** KEYGEN does not send generated credentials or vault contents to a server.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🔑 **Password Generator** | Generate 4–64 character passwords with configurable uppercase, lowercase, digits, symbols, and look-alike character exclusion. |
| 🧩 **Passphrase Generator** | Create 3–12 word passphrases from a fixed 512-word list with a selectable separator. |
| 🔢 **PIN Generator** | Generate numeric PINs from 4–12 digits. |
| 🛠️ **Fortifier** | Strengthen an existing string by appending additional cryptographically random characters. |
| 📊 **Strength Estimation** | Shows estimated entropy, a strength level, and a rough crack-time estimate. |
| 🗄️ **Encrypted Vault** | Store credentials locally in an AES-256-GCM encrypted vault. |
| 📤 **Export / Import** | KEYGEN encrypted `.bin`, browser CSV, JSON, TXT, and Markdown formats. |
| 🎨 **Custom UI** | Custom-painted controls, icons, dark theme, and small animations instead of stock-looking Qt widgets. |
| 🌐 **Offline First** | Designed to work without a website, account, API, CDN, or internet connection. |

---

## 🧠 How it works

### Secure generation

Password generation uses Python's [`secrets`](https://docs.python.org/3/library/secrets.html) module rather than the non-cryptographic `random` module.

When multiple character classes are enabled, KEYGEN makes sure every selected class is represented before shuffling the final result.

For password strength, the project estimates entropy using:

```text
length × log2(character_pool_size)
```

Passphrase strength is estimated as:

```text
words × 9 bits
```

These calculations are estimates, not guarantees about real-world attack time.

### Encrypted vault

Vault unlocking derives a key from the master password using **PBKDF2-HMAC-SHA256 with 200,000 iterations**, then decrypts the local vault using **AES-256-GCM**.

The master password is never stored by KEYGEN.

That also means there is no "forgot password" recovery path. Losing the master password means the vault can only be discarded by deleting it.

---

## 🗂️ Project structure

```text
KeyGen/
├── project.py                  # Application entry point + CS50P-required helpers
├── test_project.py             # Tests for core required helpers
├── requirements.txt            # Python dependencies
│
├── app/                        # GUI, widgets, themes, dialogs, animations
│
├── core/                       # Generation, word list, strength, crypto, vault I/O
│
├── packaging/                 # PyInstaller + Inno Setup build files
│   ├── keygen.spec
│   ├── build.bat
│   ├── sign.bat
│   └── ...
│
└── tools/
    └── make_icon.py            # Generates the application icon
```

---

## 🖥️ Run from source

KEYGEN is currently intended for **Windows**.

### Requirements

Python **3.12+** is recommended.

### Install

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```powershell
python project.py
```

A native **PySide6 / Qt Widgets** window will open.

---

## 🧪 Tests

The project includes the helpers required for the CS50P final project along with tests for the core generation and strength logic.

Run:

```powershell
pytest test_project.py -q
```

---

## 📦 Build a Windows application

The repository includes a PyInstaller specification and an Inno Setup installer script.

Run the build script from Windows:

```powershell
packaging\build.bat
```

Expected output:

```text
dist\KEYGEN\KEYGEN.exe
dist\keygen-setup.exe
```

`dist\KEYGEN\KEYGEN.exe` is the portable application build. The setup executable is produced when **Inno Setup 6** is available.

Unsigned builds may trigger Windows SmartScreen warnings. That is expected for binaries without a trusted public code-signing certificate.

---

## 📤 Export formats

KEYGEN supports the following export and import formats:

| Format | Intended use |
|---|---|
| `.bin` | KEYGEN encrypted backup/import |
| `.csv` | Browser password import workflows |
| `.json` | Structured local data |
| `.txt` | Human-readable export |
| `.md` | Human-readable Markdown export |

---

## 🎨 Design philosophy

KEYGEN deliberately avoids looking like a default Qt demo.

The interface uses a near-black background with the project's orange accent (`#FF5A1F`), custom-painted widgets, hand-drawn icons, blurred vault rows, and small animations to make a compact security utility feel like a real desktop product.

The project also keeps its visual assets local. There are no icon CDNs, remote fonts, or online UI dependencies required to render the application.

---

## 🔐 Security notes

KEYGEN is built around a few simple rules: generate secrets with a cryptographically secure random source, keep vault data local, never store the master password, and don't pretend that an export format is encrypted when it isn't.

The encrypted vault is stored at:

```text
%USERPROFILE%\.keygen\vault.bin
```

A forgotten master password cannot be recovered by the application.

---

## 🎓 CS50P

**KEYGEN is my CS50P final project.** It started as a course requirement and grew into a complete native Windows application with its own UI, vault, cryptography, testing, and packaging workflow.

---

## 📌 Project notes

The source tree stays relatively small because the application is mostly Python code plus a small set of assets.

The installed application is much larger because PyInstaller bundles the Python runtime and Qt dependencies with the program. The packaging configuration removes unused Qt components such as WebEngine, QML, and Multimedia where possible without changing the interface.

