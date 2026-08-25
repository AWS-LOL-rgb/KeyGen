"""Add / edit credential dialogs."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.animations import shake
from app.theme import Palette
from app.widgets import PillButton, StyledLine
from core.vault import CATEGORIES, Credential


class CredentialDialog(QDialog):
    def __init__(self, pal: Palette, existing: Credential | None = None, seed: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit credential" if existing else "Add credential")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.result_cred: Credential | None = None
        self.existing = existing
        self.pal = pal

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(10)
        title = QLabel("Edit credential" if existing else "Save to vault")
        title.setStyleSheet(f"color:{pal.text.name()}; font: 700 16px 'Segoe UI';")
        root.addWidget(title)

        def field(label: str, widget: QWidget) -> None:
            l = QLabel(label)
            l.setStyleSheet(f"color:{pal.muted.name()}; font: 600 10px 'Segoe UI';")
            root.addWidget(l)
            root.addWidget(widget)

        self.service = StyledLine()
        self.website = StyledLine()
        self.username = StyledLine()
        self.password = StyledLine()
        self.notes = StyledLine()
        for w in (self.service, self.website, self.username, self.password, self.notes):
            w.apply(pal)
        self.password.setEchoMode(StyledLine.EchoMode.Password)
        self.cat = QComboBox()
        self.cat.addItems(CATEGORIES)
        self.cat.setStyleSheet(
            f"QComboBox {{ background:{pal.input.name()}; color:{pal.text.name()};"
            f"border:1px solid {pal.border.name()}; border-radius:10px; padding:8px 10px; }}"
        )

        if existing:
            self.service.setText(existing.service)
            self.website.setText(existing.website)
            self.username.setText(existing.username)
            self.password.setText(existing.password)
            self.notes.setText(existing.notes)
            idx = CATEGORIES.index(existing.category) if existing.category in CATEGORIES else 0
            self.cat.setCurrentIndex(idx)
        elif seed:
            self.password.setText(seed)

        field("SERVICE", self.service)
        field("WEBSITE", self.website)
        field("USERNAME", self.username)
        field("PASSWORD", self.password)
        field("CATEGORY", self.cat)
        field("NOTES", self.notes)

        row = QHBoxLayout()
        cancel = PillButton("Cancel")
        save = PillButton("Save", "save", primary=True)
        cancel.pal = save.pal = pal
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._ok)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(save)
        root.addLayout(row)
        self.setStyleSheet(f"QDialog {{ background:{pal.panel.name()}; }}")

    def _ok(self) -> None:
        if self.existing:
            c = self.existing
            c.service = self.service.text().strip() or "Untitled"
            c.website = self.website.text().strip()
            c.username = self.username.text().strip()
            c.password = self.password.text()
            c.category = self.cat.currentText()
            c.notes = self.notes.text()
            self.result_cred = c
        else:
            self.result_cred = Credential.create(
                service=self.service.text(),
                website=self.website.text(),
                username=self.username.text(),
                password=self.password.text(),
                category=self.cat.currentText(),
                notes=self.notes.text(),
            )
        self.accept()


class UnlockDialog(QDialog):
    """Create / unlock / reset the vault. Reset wipes the encrypted file."""

    reset_requested = Signal()

    def __init__(self, pal: Palette, creating: bool, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setMinimumWidth(440)
        self.password = ""
        self.pal = pal
        self.creating = creating

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.panel = QWidget()
        pl = QVBoxLayout(self.panel)
        pl.setContentsMargins(28, 26, 28, 22)
        pl.setSpacing(10)
        title = "Create master password" if creating else "Unlock vault"
        body = (
            "Choose a master password (4+ characters). There is no recovery — only a full reset."
            if creating
            else "Enter your master password to reveal credentials. Forgotten? Reset wipes the vault forever."
        )
        self.title = QLabel(title)
        self.body = QLabel(body)
        self.body.setWordWrap(True)
        self.master = StyledLine()
        self.master.setEchoMode(StyledLine.EchoMode.Password)
        self.master.setPlaceholderText("Master password")
        self.master.returnPressed.connect(self._ok)
        self.err = QLabel("")
        self.err.setWordWrap(True)
        unlock = PillButton("Create vault" if creating else "Unlock", "unlock", primary=True)
        cancel = PillButton("Cancel")
        unlock.pal = cancel.pal = pal
        unlock.clicked.connect(self._ok)
        cancel.clicked.connect(self.reject)
        row = QHBoxLayout()
        row.addWidget(cancel)
        row.addWidget(unlock)
        self.reset_btn = PillButton("Reset vault…", "warning")
        self.reset_btn.pal = pal
        self.reset_btn.setVisible(not creating)
        self.reset_btn.clicked.connect(self._ask_reset)
        self.confirm = QLabel("")
        self.confirm.setWordWrap(True)
        self.confirm.hide()
        self.wipe = PillButton("Erase everything", "delete", primary=True)
        self.wipe.pal = pal
        self.wipe.hide()
        self.wipe.clicked.connect(self.reset_requested.emit)
        pl.addWidget(self.title)
        pl.addWidget(self.body)
        pl.addWidget(self.master)
        pl.addWidget(self.err)
        pl.addLayout(row)
        pl.addWidget(self.reset_btn)
        pl.addWidget(self.confirm)
        pl.addWidget(self.wipe)
        root.addWidget(self.panel)
        self.panel.setStyleSheet(
            f"background:{pal.elevated.name()}; border:1px solid {pal.border.name()}; border-radius:18px;"
        )
        self.title.setStyleSheet(f"color:{pal.text.name()}; font: 800 18px 'Segoe UI';")
        self.body.setStyleSheet(f"color:{pal.secondary.name()}; font: 12px 'Segoe UI';")
        self.err.setStyleSheet(f"color:{pal.error.name()}; font: 11px 'Segoe UI';")
        self.confirm.setStyleSheet(f"color:{pal.warning.name()}; font: 11px 'Segoe UI';")
        self.master.apply(pal)

    def _ok(self) -> None:
        pw = self.master.text()
        if self.creating and len(pw) < 4:
            self.err.setText("Master password must be at least 4 characters.")
            shake(self)
            return
        if not pw:
            self.err.setText("Enter your master password.")
            shake(self)
            return
        self.password = pw
        self.accept()

    def fail(self, msg: str) -> None:
        self.err.setText(msg)
        shake(self)

    def _ask_reset(self) -> None:
        self.confirm.setText(
            "This permanently deletes the encrypted vault file. There is no undo. Click Erase everything to confirm."
        )
        self.confirm.show()
        self.wipe.show()


class ExportDialog(QDialog):
    """Choose encrypted .bin, readable JSON, or CSV."""

    def __init__(self, pal: Palette, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Export")
        self.setMinimumWidth(420)
        self.choice = "bin"
        self.pal = pal
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 22, 22, 22)
        t = QLabel("Export vault")
        t.setStyleSheet(f"color:{pal.text.name()}; font: 800 16px 'Segoe UI';")
        b = QLabel(
            "Encrypted backup stays unreadable without the master password. "
            "JSON and CSV are plain text — anyone with the file can read every password."
        )
        b.setWordWrap(True)
        b.setStyleSheet(f"color:{pal.secondary.name()}; font: 12px 'Segoe UI';")
        lay.addWidget(t)
        lay.addWidget(b)
        self.btns = []
        for key, label in (
            ("bin", "Encrypted KEYGEN backup  (.bin)"),
            ("csv", "Browser CSV — Chrome / Edge / Firefox  (.csv)"),
            ("json", "JSON for KEYGEN — not encrypted  (.json)"),
            ("txt", "Readable text  (.txt)"),
            ("md", "Markdown  (.md)"),
        ):
            btn = PillButton(label)
            btn.setMinimumWidth(360)
            btn.pal = pal
            btn.clicked.connect(lambda key=key: self._pick(key))
            lay.addWidget(btn)
            self.btns.append((key, btn))
        cancel = PillButton("Cancel")
        cancel.pal = pal
        cancel.clicked.connect(self.reject)
        lay.addWidget(cancel)
        self.setStyleSheet(f"QDialog {{ background:{pal.panel.name()}; }}")
        self._paint_choice()

    def _pick(self, key: str) -> None:
        self.choice = key
        self._paint_choice()
        self.accept()

    def _paint_choice(self) -> None:
        for key, btn in self.btns:
            btn.selected = key == self.choice
            btn.update()


class ConfirmDialog(QDialog):
    def __init__(self, pal: Palette, title: str, body: str, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(360)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 22, 22, 22)
        t = QLabel(title)
        t.setStyleSheet(f"color:{pal.text.name()}; font: 700 16px 'Segoe UI';")
        b = QLabel(body)
        b.setWordWrap(True)
        b.setStyleSheet(f"color:{pal.secondary.name()}; font: 12px 'Segoe UI';")
        lay.addWidget(t)
        lay.addWidget(b)
        row = QHBoxLayout()
        no = PillButton("Cancel")
        yes = PillButton("Delete", "delete", primary=True)
        no.pal = yes.pal = pal
        no.clicked.connect(self.reject)
        yes.clicked.connect(self.accept)
        row.addStretch()
        row.addWidget(no)
        row.addWidget(yes)
        lay.addLayout(row)
        self.setStyleSheet(f"QDialog {{ background:{pal.panel.name()}; }}")
