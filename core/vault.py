"""Local encrypted credential vault (single file, no network)."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from core import crypto

VAULT_VERSION = 1
CATEGORIES = ("Personal", "Work", "Finance", "Social", "Other")


@dataclass
class Credential:
    id: str
    service: str
    website: str
    username: str
    password: str
    category: str = "Personal"
    notes: str = ""
    created: str = ""
    updated: str = ""

    @staticmethod
    def create(
        service: str,
        website: str = "",
        username: str = "",
        password: str = "",
        category: str = "Personal",
        notes: str = "",
    ) -> "Credential":
        now = datetime.now(timezone.utc).isoformat()
        return Credential(
            id=str(uuid.uuid4()),
            service=service.strip() or "Untitled",
            website=website.strip(),
            username=username.strip(),
            password=password,
            category=category if category in CATEGORIES else "Other",
            notes=notes,
            created=now,
            updated=now,
        )


@dataclass
class VaultPayload:
    version: int = VAULT_VERSION
    entries: list[dict] = field(default_factory=list)


class VaultError(Exception):
    pass


class Vault:
    def __init__(self, path: Path | None = None) -> None:
        base = Path(os.environ.get("KEYGEN_HOME", Path.home() / ".keygen"))
        base.mkdir(parents=True, exist_ok=True)
        self.path = path or (base / "vault.bin")
        self._key: bytes | None = None
        self._salt: bytes | None = None
        self.entries: list[Credential] = []

    @property
    def exists(self) -> bool:
        return self.path.exists() and self.path.stat().st_size > 0

    @property
    def unlocked(self) -> bool:
        return self._key is not None

    def lock(self) -> None:
        self._key = None
        self.entries = []

    def wipe(self) -> None:
        """Irreversibly delete the vault file and clear memory."""
        self.lock()
        self._salt = None
        for p in (self.path, self.path.with_suffix(".tmp")):
            try:
                if p.exists():
                    p.write_bytes(b"\x00" * max(p.stat().st_size, 1))
                    p.unlink()
            except OSError:
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass

    def create_new(self, master: str) -> None:
        if len(master) < 8:
            raise VaultError("Master password must be at least 4 characters.")
        self._salt = crypto.new_salt()
        self._key = crypto.derive_key(master, self._salt)
        self.entries = []
        self.save()

    def unlock(self, master: str) -> None:
        if not self.exists:
            raise VaultError("No vault file found.")
        raw = self.path.read_bytes()
        if len(raw) < crypto.SALT_LEN + 20:
            raise VaultError("Vault file is corrupt.")
        salt, blob = raw[: crypto.SALT_LEN], raw[crypto.SALT_LEN :]
        key = crypto.derive_key(master, salt)
        try:
            plain = crypto.decrypt(blob, key)
        except crypto.CryptoError as exc:
            raise VaultError(str(exc)) from exc
        try:
            data = json.loads(plain.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise VaultError("Vault payload is not valid JSON.") from exc
        if not isinstance(data, dict) or "entries" not in data:
            raise VaultError("Vault structure is invalid.")
        self._salt = salt
        self._key = key
        self.entries = [Credential(**e) for e in data.get("entries", [])]

    def save(self) -> None:
        if self._key is None or self._salt is None:
            raise VaultError("Vault is locked.")
        payload = VaultPayload(
            version=VAULT_VERSION,
            entries=[asdict(e) for e in self.entries],
        )
        plain = json.dumps(asdict(payload), indent=0).encode("utf-8")
        blob = crypto.encrypt(plain, self._key)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_bytes(self._salt + blob)
        tmp.replace(self.path)

    def add(self, cred: Credential) -> None:
        self.entries.append(cred)
        self.save()

    def update(self, cred: Credential) -> None:
        for i, e in enumerate(self.entries):
            if e.id == cred.id:
                cred.updated = datetime.now(timezone.utc).isoformat()
                self.entries[i] = cred
                self.save()
                return
        raise VaultError("Credential not found.")

    def delete(self, cred_id: str) -> None:
        self.entries = [e for e in self.entries if e.id != cred_id]
        self.save()

    def search(self, query: str, category: str | None = None) -> list[Credential]:
        q = query.strip().lower()
        out = []
        for e in self.entries:
            if category and category != "All" and e.category != category:
                continue
            blob = f"{e.service} {e.website} {e.username} {e.category}".lower()
            if not q or q in blob:
                out.append(e)
        return out

    def export_backup(self, dest: Path) -> None:
        if not self.exists:
            raise VaultError("Nothing to export.")
        dest.write_bytes(self.path.read_bytes())

    def export_json(self, dest: Path) -> int:
        if not self.unlocked:
            raise VaultError("Unlock the vault first.")
        payload = {
            "version": VAULT_VERSION,
            "encrypted": False,
            "entries": [asdict(e) for e in self.entries],
        }
        dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return len(self.entries)

    def export_browser_csv(self, dest: Path) -> int:
        """Chrome / Edge / Firefox password-manager CSV: name,url,username,password."""
        if not self.unlocked:
            raise VaultError("Unlock the vault first.")
        import csv

        with dest.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["name", "url", "username", "password"])
            w.writeheader()
            for e in self.entries:
                w.writerow(
                    {
                        "name": e.service,
                        "url": _browser_url(e.website, e.service),
                        "username": e.username,
                        "password": e.password,
                    }
                )
        return len(self.entries)

    def export_csv(self, dest: Path) -> int:
        return self.export_browser_csv(dest)

    def export_txt(self, dest: Path) -> int:
        if not self.unlocked:
            raise VaultError("Unlock the vault first.")
        lines = ["KEYGEN export (not encrypted)", ""]
        for i, e in enumerate(self.entries, 1):
            lines += [
                f"{i}. {e.service}",
                f"   Website : {_browser_url(e.website, e.service)}",
                f"   Username: {e.username or '—'}",
                f"   Password: {e.password}",
                f"   Category: {e.category}",
            ]
            if e.notes:
                lines.append(f"   Notes   : {e.notes}")
            lines.append("")
        dest.write_text("\n".join(lines), encoding="utf-8")
        return len(self.entries)

    def export_markdown(self, dest: Path) -> int:
        if not self.unlocked:
            raise VaultError("Unlock the vault first.")
        lines = ["# KEYGEN export", "", "> Not encrypted. Delete this file after use.", ""]
        for e in self.entries:
            url = _browser_url(e.website, e.service)
            lines += [
                f"## {e.service}",
                "",
                f"- **Website:** {url}",
                f"- **Username:** `{e.username or '—'}`",
                f"- **Password:** `{e.password}`",
                f"- **Category:** {e.category}",
            ]
            if e.notes:
                lines.append(f"- **Notes:** {e.notes}")
            lines.append("")
        dest.write_text("\n".join(lines), encoding="utf-8")
        return len(self.entries)

    def import_backup(self, src: Path, master: str | None = None, merge: bool = True) -> tuple[int, str]:
        """Import KEYGEN encrypted backup, JSON, CSV, or loose text. Returns (count, kind)."""
        creds, kind = load_any(src, master)
        if not creds:
            raise VaultError("No credentials found in that file.")
        if not self.unlocked:
            raise VaultError("Unlock or create the vault first, then import.")
        if merge:
            self.entries.extend(creds)
        else:
            self.entries = creds
        self.save()
        return len(creds), kind


def _browser_url(website: str, service: str = "") -> str:
    """Chrome/Firefox expect a full URL, not a bare name."""
    u = (website or "").strip()
    if u.startswith(("http://", "https://")):
        return u
    if u and "." in u and " " not in u:
        return "https://" + u
    slug = (service or "imported").strip().replace(" ", "-")
    return f"https://{slug}.invalid"


_SERVICE = ("service", "name", "title", "site", "label", "account", "app")
_USER = ("username", "user", "login", "email", "userid", "account")
_PASS = ("password", "pass", "passwd", "pwd", "secret", "passphrase", "pin")
_URL = ("website", "url", "uri", "origin", "host", "domain")
_NOTE = ("notes", "note", "comment", "extra")
_CAT = ("category", "folder", "group", "type")


def _pick(row: dict, keys: tuple[str, ...]) -> str:
    lower = {str(k).strip().lower(): v for k, v in row.items()}
    for k in keys:
        v = lower.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


def _row_to_cred(row: dict) -> Credential | None:
    # Bitwarden-style nested login
    if isinstance(row.get("login"), dict):
        login = row["login"]
        row = {
            **row,
            "username": login.get("username", ""),
            "password": login.get("password", ""),
            "url": (login.get("uris") or [{}])[0].get("uri", "") if login.get("uris") else login.get("uri", ""),
        }
    pw = _pick(row, _PASS)
    service = _pick(row, _SERVICE) or _pick(row, _URL) or "Imported"
    if not pw and not service:
        return None
    if not pw:
        return None
    return Credential.create(
        service=service,
        website=_pick(row, _URL),
        username=_pick(row, _USER),
        password=pw,
        category=_pick(row, _CAT) or "Other",
        notes=_pick(row, _NOTE),
    )


def _from_json(text: str) -> list[Credential]:
    data = json.loads(text)
    rows: list = []
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        for key in ("entries", "items", "passwords", "accounts", "logins", "credentials"):
            if isinstance(data.get(key), list):
                rows = data[key]
                break
        else:
            rows = [data]
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        c = _row_to_cred(row)
        if c:
            out.append(c)
    return out


def _from_csv(text: str) -> list[Credential]:
    import csv
    import io

    sample = text[:2000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    has_header = True
    try:
        has_header = csv.Sniffer().has_header(sample)
    except csv.Error:
        has_header = True
    f = io.StringIO(text)
    out: list[Credential] = []
    if has_header:
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            if not row:
                continue
            c = _row_to_cred({(k or ""): (v or "") for k, v in row.items()})
            if c:
                out.append(c)
        return out
    reader = csv.reader(f, dialect=dialect)
    for cols in reader:
        cols = [c.strip() for c in cols]
        if len(cols) >= 3:
            c = Credential.create(service=cols[0] or "Imported", username=cols[1], password=cols[2])
        elif len(cols) == 2:
            c = Credential.create(service=cols[0] or "Imported", password=cols[1])
        else:
            continue
        if c.password:
            out.append(c)
    return out


def _from_text(text: str) -> list[Credential]:
    out: list[Credential] = []
    # blocks: name: / password:
    block: dict[str, str] = {}

    def flush():
        nonlocal block
        if block:
            c = _row_to_cred(block)
            if c:
                out.append(c)
        block = {}

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            flush()
            continue
        if ":" in line and not line.startswith("http"):
            k, _, v = line.partition(":")
            key = k.strip().lower()
            block[key] = v.strip()
            continue
        flush()
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
        elif " | " in line:
            parts = [p.strip() for p in line.split("|")]
        else:
            parts = line.split(None, 1)
        if len(parts) >= 2:
            out.append(Credential.create(service=parts[0], password=parts[-1], username=parts[1] if len(parts) > 2 else ""))
    flush()
    return out


def load_any(src: Path, master: str | None = None) -> tuple[list[Credential], str]:
    raw = src.read_bytes()
    if master and len(raw) >= crypto.SALT_LEN + 20:
        try:
            return _decrypt_keygen(raw, master)
        except VaultError:
            pass
    for enc in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        stripped = text.lstrip()
        if stripped[:1] in "{[":
            try:
                creds = _from_json(text)
                if creds:
                    return creds, "json"
            except json.JSONDecodeError:
                pass
        if "," in text or ";" in text or "\t" in text:
            try:
                creds = _from_csv(text)
                if creds:
                    return creds, "csv"
            except Exception:
                pass
        creds = _from_text(text)
        if creds:
            return creds, "text"
        break
    if len(raw) >= crypto.SALT_LEN + 20:
        if not master:
            raise VaultError("This looks like an encrypted KEYGEN backup. Enter the master password.")
        return _decrypt_keygen(raw, master)
    raise VaultError("Unrecognized file. Use JSON, CSV, text, or a KEYGEN backup.")


def _decrypt_keygen(raw: bytes, master: str) -> tuple[list[Credential], str]:
    salt, blob = raw[: crypto.SALT_LEN], raw[crypto.SALT_LEN :]
    key = crypto.derive_key(master, salt)
    try:
        plain = crypto.decrypt(blob, key)
        data = json.loads(plain.decode("utf-8"))
    except Exception as exc:
        raise VaultError("Could not decrypt. Check the master password.") from exc
    creds = []
    rows = data.get("entries", []) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise VaultError("Backup structure is invalid.")
    for e in rows:
        if isinstance(e, dict):
            try:
                creds.append(Credential(**{k: e.get(k, "") for k in Credential.__dataclass_fields__}))
            except TypeError:
                c = _row_to_cred(e)
                if c:
                    creds.append(c)
    return creds, "keygen"
