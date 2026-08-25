"""KEYGEN main window — native PySide6."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QPropertyAnimation, QSettings, QThread, Qt, Signal
from PySide6.QtGui import QAction, QFont, QGuiApplication, QIcon, QKeySequence, QPainter
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.animations import fade_widget, later, tween
from app.dialogs import ConfirmDialog, CredentialDialog, ExportDialog, UnlockDialog
from app.icons import brand_pixmap, paint_icon
from app.theme import DARK, LIGHT, Palette, strength_color
from app.widgets import (
    BrandMark,
    Chip,
    CompactToggle,
    IconButton,
    LengthSlider,
    NavItem,
    PillButton,
    Segmented,
    StrengthBar,
    StyledLine,
    ToastHost,
)
from core.generator import GeneratorError, count_classes, generate_password, generate_pin, fortify_password
from core.passphrase import SEPARATORS, generate_passphrase
from core.strength import analyze_generated, observed_entropy, pool_size
from core.vault import CATEGORIES, Vault, VaultError


class UnlockWorker(QThread):
    ok = Signal()
    fail = Signal(str)

    def __init__(self, vault: Vault, password: str, create: bool) -> None:
        super().__init__()
        self.vault = vault
        self.password = password
        self.create = create

    def run(self) -> None:
        try:
            if self.create:
                self.vault.create_new(self.password)
            else:
                self.vault.unlock(self.password)
            self.ok.emit()
        except VaultError as exc:
            self.fail.emit(str(exc))


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings("KEYGEN", "KEYGEN")
        theme_name = self.settings.value("theme", "dark")
        self.pal: Palette = LIGHT if theme_name == "light" else DARK
        self.mode = self.settings.value("mode", "password")
        self.length = int(self.settings.value("length", 16))
        self.words = int(self.settings.value("words", 5))
        self.pin_len = int(self.settings.value("pin_len", 6))
        self.sep = self.settings.value("sep", "-")
        self.flags = {
            "uppercase": self.settings.value("uppercase", True, bool),
            "lowercase": self.settings.value("lowercase", True, bool),
            "digits": self.settings.value("digits", True, bool),
            "symbols": self.settings.value("symbols", True, bool),
            "exclude": self.settings.value("exclude", False, bool),
        }
        self.vault = Vault()
        self.current_value = ""
        self._worker: UnlockWorker | None = None
        self.vault_filter = "All"

        self.setWindowTitle("KEYGEN")
        self.setMinimumSize(980, 650)
        self.resize(1180, 760)
        self._center()
        self.setWindowIcon(QIcon(brand_pixmap(64)))

        self._build()
        self.apply_theme()
        self.generate()

        for seq, slot in (
            ("Ctrl+G", self.generate),
            ("Ctrl+S", self.save_current),
            ("Ctrl+C", self.copy_current),
        ):
            act = QAction(self)
            act.setShortcut(QKeySequence(seq))
            act.triggered.connect(slot)
            self.addAction(act)

    def _center(self) -> None:
        scr = QGuiApplication.primaryScreen()
        if scr:
            g = scr.availableGeometry()
            self.move(g.center().x() - self.width() // 2, g.center().y() - self.height() // 2)

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(16, 28, 16, 16)
        sl.setSpacing(6)

        brand = QVBoxLayout()
        brand.setSpacing(10)
        brand.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.brand_mark = BrandMark(56)
        brand.addWidget(self.brand_mark, 0, Qt.AlignmentFlag.AlignHCenter)
        self.brand_title = QLabel("KEYGEN")
        self.brand_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.brand_sub = QLabel("Offline Security Suite")
        self.brand_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        brand.addWidget(self.brand_title)
        brand.addWidget(self.brand_sub)
        sl.addLayout(brand)
        sl.addSpacing(26)

        self.nav_gen = NavItem("sparkles", "Generator")
        self.nav_vault = NavItem("vault", "Vault")
        self.nav_gen.active = True
        self.nav_gen.clicked.connect(lambda: self.show_page(0))
        self.nav_vault.clicked.connect(lambda: self.show_page(1))
        sl.addWidget(self.nav_gen)
        sl.addWidget(self.nav_vault)
        sl.addStretch()

        self.status_dot = QLabel("  Offline  ·  Private")
        sl.addWidget(self.status_dot)

        theme_row = QHBoxLayout()
        self.theme_btn = IconButton("sun", "Toggle theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.shortcut_hint = QLabel("Ctrl+G  generate")
        theme_row.addWidget(self.theme_btn)
        theme_row.addWidget(self.shortcut_hint)
        sl.addLayout(theme_row)

        self.stack = QStackedWidget()
        self.gen_page = self._generator_page()
        self.vault_page = self._vault_page()
        self.stack.addWidget(self.gen_page)
        self.stack.addWidget(self.vault_page)

        root.addWidget(self.sidebar)
        root.addWidget(self.stack, 1)

        self.toasts = ToastHost(self)
        self.toasts.raise_()

    def _generator_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(36, 26, 36, 20)
        lay.setSpacing(14)

        self.h_title = QLabel("PASSWORD GENERATOR")
        self.h_sub = QLabel("Create cryptographically strong passwords.")
        lay.addWidget(self.h_title)
        lay.addWidget(self.h_sub)

        self.seg = Segmented(
            [
                ("password", "Password", "lock"),
                ("passphrase", "Passphrase", "book"),
                ("pin", "PIN", "hash"),
            ]
        )
        self.seg.current = self.mode if self.mode in ("password", "passphrase", "pin") else "password"
        self.seg.changed.connect(self._set_mode)
        lay.addWidget(self.seg)

        self.card = QFrame()
        self.card.setObjectName("card")
        cl = QVBoxLayout(self.card)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(12)

        self.card_label = QLabel("GENERATED CREDENTIAL")
        cl.addWidget(self.card_label)

        self.pwd_label = QLabel("")
        self.pwd_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.pwd_label.setWordWrap(True)
        self.pwd_label.setMinimumHeight(76)
        cl.addWidget(self.pwd_label)
        self.sbar = StrengthBar()
        self.sbar.setFixedHeight(8)
        cl.addWidget(self.sbar)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        self.chip_u = Chip("0", "Upper")
        self.chip_l = Chip("0", "Lower")
        self.chip_d = Chip("0", "Digits")
        self.chip_s = Chip("0", "Symbols")
        for c in (self.chip_u, self.chip_l, self.chip_d, self.chip_s):
            chips.addWidget(c)
        chips.addSpacing(16)
        stats = QVBoxLayout()
        stats.setSpacing(2)
        self.level_lbl = QLabel("—")
        self.bits_lbl = QLabel("—")
        self.crack_lbl = QLabel("—")
        self.crack_lbl.setWordWrap(True)
        stats.addWidget(self.level_lbl)
        stats.addWidget(self.bits_lbl)
        stats.addWidget(self.crack_lbl)
        chips.addLayout(stats, 1)
        cl.addLayout(chips)

        actions = QHBoxLayout()
        self.btn_gen = PillButton("Generate", "refresh", primary=True)
        self.btn_copy = PillButton("Copy Password", "copy")
        self.btn_save = PillButton("Save to Vault", "save")
        self.btn_gen.setMinimumWidth(220)
        self.btn_gen.clicked.connect(self.generate)
        self.btn_copy.clicked.connect(self.copy_current)
        self.btn_save.clicked.connect(self.save_current)
        actions.addWidget(self.btn_gen, 2)
        actions.addWidget(self.btn_copy, 1)
        actions.addWidget(self.btn_save, 1)
        cl.addLayout(actions)
        lay.addWidget(self.card)

        self.err_lbl = QLabel("")
        lay.addWidget(self.err_lbl)

        self.pw_box = QFrame()
        self.pw_box.setObjectName("box")
        pwl = QVBoxLayout(self.pw_box)
        pwl.setContentsMargins(20, 16, 20, 16)
        pwl.setSpacing(14)
        row = QHBoxLayout()
        self.len_title = QLabel("PASSWORD LENGTH")
        self.len_num = QLabel(str(self.length))
        row.addWidget(self.len_title)
        row.addSpacing(12)
        row.addWidget(self.len_num)
        row.addStretch()
        pwl.addLayout(row)
        self.slider = LengthSlider(4, 64, self.length)
        self.slider.changed.connect(self._len_changed)
        pwl.addWidget(self.slider)
        self.t_up = CompactToggle("Uppercase", self.flags["uppercase"])
        self.t_lo = CompactToggle("Lowercase", self.flags["lowercase"])
        self.t_di = CompactToggle("Numbers", self.flags["digits"])
        self.t_sy = CompactToggle("Symbols", self.flags["symbols"])
        self.t_ex = CompactToggle("Exclude Ambiguous", self.flags["exclude"])
        for t, key in (
            (self.t_up, "uppercase"),
            (self.t_lo, "lowercase"),
            (self.t_di, "digits"),
            (self.t_sy, "symbols"),
            (self.t_ex, "exclude"),
        ):
            t.changed.connect(lambda v, k=key: self._flag(k, v))
        grid = QHBoxLayout()
        grid.setSpacing(24)
        col_a = QVBoxLayout()
        col_b = QVBoxLayout()
        col_a.setSpacing(8)
        col_b.setSpacing(8)
        col_a.addWidget(self.t_up)
        col_a.addWidget(self.t_lo)
        col_a.addWidget(self.t_ex)
        col_b.addWidget(self.t_di)
        col_b.addWidget(self.t_sy)
        col_b.addStretch()
        grid.addLayout(col_a)
        grid.addLayout(col_b)
        grid.addStretch()
        pwl.addLayout(grid)
        self.preset_btns: list[PillButton] = []
        lay.addWidget(self.pw_box)

        self.pp_box = QFrame()
        self.pp_box.setObjectName("box")
        ppl = QVBoxLayout(self.pp_box)
        ppl.setContentsMargins(18, 14, 18, 14)
        r2 = QHBoxLayout()
        self.pp_title = QLabel("WORD COUNT")
        self.pp_num = QLabel(str(self.words))
        r2.addWidget(self.pp_title)
        r2.addStretch()
        r2.addWidget(self.pp_num)
        ppl.addLayout(r2)
        self.wslider = LengthSlider(3, 12, self.words)
        self.wslider.ticks = (3, 4, 5, 6, 8, 10, 12)
        self.wslider.changed.connect(self._words_changed)
        ppl.addWidget(self.wslider)
        sep_row = QHBoxLayout()
        self.sep_lbl = QLabel("SEPARATOR")
        sep_row.addWidget(self.sep_lbl)
        self.sep_btns = []
        for s in SEPARATORS:
            label = "space" if s == " " else s
            b = PillButton(label)
            b.setFixedSize(72, 32)
            b.clicked.connect(lambda s=s: self._set_sep(s))
            sep_row.addWidget(b)
            self.sep_btns.append((s, b))
        sep_row.addStretch()
        ppl.addLayout(sep_row)
        lay.addWidget(self.pp_box)

        self.pin_box = QFrame()
        self.pin_box.setObjectName("box")
        pil = QHBoxLayout(self.pin_box)
        pil.setContentsMargins(18, 14, 18, 14)
        self.pin_title = QLabel("PIN LENGTH")
        pil.addWidget(self.pin_title)
        self.pin_btns = []
        for n in (4, 6, 8, 10, 12):
            b = PillButton(str(n))
            b.setFixedSize(64, 36)
            b.setMinimumWidth(64)
            b.clicked.connect(lambda n=n: self._set_pin(n))
            pil.addWidget(b)
            self.pin_btns.append((n, b))
        pil.addStretch()
        lay.addWidget(self.pin_box)

        self.fort = QFrame()
        self.fort.setObjectName("box")
        fl = QVBoxLayout(self.fort)
        fl.setContentsMargins(18, 12, 18, 12)
        headf = QHBoxLayout()
        titlesf = QVBoxLayout()
        self.fort_title = QLabel("FORTIFIER")
        self.fort_sub = QLabel("Add extra randomness with generated characters.")
        titlesf.addWidget(self.fort_title)
        titlesf.addWidget(self.fort_sub)
        headf.addLayout(titlesf, 1)
        self.btn_fort_toggle = PillButton("Open", "lightning")
        self.btn_fort_toggle.setFixedWidth(100)
        self.btn_fort_toggle.clicked.connect(self._toggle_fort)
        headf.addWidget(self.btn_fort_toggle)
        fl.addLayout(headf)
        self.fort_body = QWidget()
        fb = QHBoxLayout(self.fort_body)
        fb.setContentsMargins(0, 8, 0, 0)
        self.fort_in = StyledLine()
        self.fort_in.setPlaceholderText("Type a weak password to fortify...")
        self.btn_fort = PillButton("Fortify", "lightning", primary=True)
        self.btn_fort.setFixedWidth(140)
        self.btn_fort.clicked.connect(self.do_fortify)
        fb.addWidget(self.fort_in, 1)
        fb.addWidget(self.btn_fort)
        fl.addWidget(self.fort_body)
        self.fort_out = QLabel("")
        self.fort_out.setWordWrap(True)
        fl.addWidget(self.fort_out)
        self.fort_body.hide()
        self.fort_out.hide()
        lay.addWidget(self.fort)
        lay.addStretch()
        self._sync_mode_ui()
        return page

    def _vault_page(self) -> QWidget:
        page = QWidget()
        vl = QVBoxLayout(page)
        vl.setContentsMargins(36, 28, 36, 24)
        ht = QHBoxLayout()
        titles = QVBoxLayout()
        self.v_title = QLabel("ENCRYPTED VAULT")
        self.v_sub = QLabel("Local encrypted storage. Locked items stay unreadable until you act.")
        titles.addWidget(self.v_title)
        titles.addWidget(self.v_sub)
        ht.addLayout(titles, 1)
        self.btn_add = PillButton("Add Password", "plus", primary=True)
        self.btn_lock = PillButton("Lock Now", "lock")
        self.btn_exp = PillButton("Export", "upload")
        self.btn_imp = PillButton("Import", "download")
        self.btn_reset = PillButton("Reset", "warning")
        self.btn_add.clicked.connect(lambda: self._guarded(lambda: self._edit_cred(None)))
        self.btn_lock.clicked.connect(self.lock_vault)
        self.btn_exp.clicked.connect(lambda: self._guarded(self.export_backup))
        self.btn_imp.clicked.connect(self.import_backup)
        self.btn_reset.clicked.connect(self._reset_vault_flow)
        for b in (self.btn_add, self.btn_lock, self.btn_exp, self.btn_imp, self.btn_reset):
            ht.addWidget(b, 0, Qt.AlignmentFlag.AlignTop)
        vl.addLayout(ht)

        self.search = StyledLine()
        self.search.setPlaceholderText("Search credentials…")
        self.search.textChanged.connect(self._on_search)
        self.search.installEventFilter(self)
        vl.addWidget(self.search)

        cats = QHBoxLayout()
        self.cat_btns = []
        for name in ("All",) + CATEGORIES:
            b = PillButton(name)
            b.setFixedHeight(32)
            b.clicked.connect(lambda name=name: self._set_cat(name))
            cats.addWidget(b)
            self.cat_btns.append((name, b))
        cats.addStretch()
        vl.addLayout(cats)

        self.list_host = QVBoxLayout()
        self.list_host.setSpacing(8)
        holder = QWidget()
        holder.setLayout(self.list_host)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(holder)
        self.scroll = scroll
        vl.addWidget(scroll, 1)
        self.empty_lbl = QLabel("No credentials yet. Generate one and save it, or click Add Password.")
        self.empty_lbl.setWordWrap(True)
        vl.addWidget(self.empty_lbl)

        # unused leftovers kept as no-ops for theme apply
        self.lock_title = QLabel("")
        self.lock_body = QLabel("")
        self.lock_err = QLabel("")
        self.master = StyledLine()
        self.master.hide()
        self.btn_unlock = PillButton("Unlock", "unlock", primary=True)
        self.btn_unlock.hide()
        return page

    # ------------------------------------------------------------------ theme
    def apply_theme(self) -> None:
        pal = self.pal
        self.setStyleSheet(
            f"""
            MainWindow, QStackedWidget, QStackedWidget > QWidget {{
                background: {pal.bg.name()};
                color: {pal.text.name()};
            }}
            QLabel {{
                background: transparent;
                color: {pal.text.name()};
                border: none;
            }}
            QScrollArea, QScrollArea > QWidget > QWidget {{
                background: transparent;
                border: none;
            }}
            """
        )
        self.setAutoFillBackground(True)
        pal_bg = self.palette()
        pal_bg.setColor(self.backgroundRole(), pal.bg)
        self.setPalette(pal_bg)
        self.sidebar.setStyleSheet(
            f"QFrame {{ background:{pal.sidebar.name()}; border: none; border-right:1px solid {pal.border.name()}; }}"
        )
        self.brand_title.setText(f'<span style="color:{pal.accent.name()}">KEY</span><span style="color:{pal.text.name()}">GEN</span>')
        self.brand_title.setStyleSheet("font: 800 20px 'Segoe UI'; letter-spacing:2px;")
        self.brand_sub.setStyleSheet(f"color:{pal.muted.name()}; font: 10px 'Segoe UI';")
        self.status_dot.setStyleSheet(f"color:{pal.success.name()}; font: 600 11px 'Segoe UI';")
        self.shortcut_hint.setStyleSheet(f"color:{pal.muted.name()}; font: 10px 'Segoe UI';")
        self.h_title.setStyleSheet(f"color:{pal.text.name()}; font: 800 26px 'Segoe UI'; letter-spacing:0.5px;")
        self.h_sub.setStyleSheet(f"color:{pal.secondary.name()}; font: 12px 'Segoe UI';")
        self.card.setStyleSheet(
            f"QFrame#card {{ background:{pal.elevated.name()}; border:1px solid {pal.border.name()}; border-radius:20px; }}"
        )
        self.card_label.setStyleSheet(f"color:{pal.muted.name()}; font: 700 10px 'Segoe UI'; letter-spacing:1.4px;")
        mf = QFont("Cascadia Mono")
        if not mf.exactMatch():
            mf = QFont("Consolas")
        mf.setPointSize(28)
        mf.setWeight(QFont.Weight.Medium)
        self.pwd_label.setFont(mf)
        self.pwd_label.setStyleSheet(f"color:{pal.text.name()};")
        self.bits_lbl.setStyleSheet(f"color:{pal.secondary.name()}; font: 600 12px 'Segoe UI';")
        self.crack_lbl.setStyleSheet(f"color:{pal.accent.name()}; font: 600 14px 'Segoe UI';")
        for box in (self.pw_box, self.pp_box, self.pin_box, self.fort):
            box.setStyleSheet(
                f"QFrame#box {{ background:{pal.panel.name()}; border:1px solid {pal.border.name()}; border-radius:16px; }}"
            )
        self.len_title.setStyleSheet(f"color:{pal.muted.name()}; font: 700 10px 'Segoe UI'; letter-spacing:1px;")
        self.len_num.setStyleSheet(f"color:{pal.accent.name()}; font: 800 22px 'Segoe UI';")
        self.pp_title.setStyleSheet(self.len_title.styleSheet())
        self.pp_num.setStyleSheet(self.len_num.styleSheet())
        self.pin_title.setStyleSheet(self.len_title.styleSheet())
        self.sep_lbl.setStyleSheet(self.len_title.styleSheet())
        self.fort_title.setStyleSheet(f"color:{pal.text.name()}; font: 700 13px 'Segoe UI';")
        self.fort_sub.setStyleSheet(f"color:{pal.secondary.name()}; font: 11px 'Segoe UI';")
        self.fort_out.setStyleSheet(f"color:{pal.text.name()}; font: 12px 'Cascadia Mono','Consolas';")
        self.v_title.setStyleSheet(self.h_title.styleSheet())
        self.v_sub.setStyleSheet(self.h_sub.styleSheet())
        self.lock_title.setStyleSheet(f"color:{pal.text.name()}; font: 800 20px 'Segoe UI';")
        self.lock_body.setStyleSheet(f"color:{pal.secondary.name()}; font: 12px 'Segoe UI';")
        self.lock_err.setStyleSheet(f"color:{pal.error.name()}; font: 11px 'Segoe UI';")
        self.empty_lbl.setStyleSheet(f"color:{pal.muted.name()}; font: 12px 'Segoe UI';")
        self.err_lbl.setStyleSheet(f"color:{pal.error.name()}; font: 11px 'Segoe UI';")

        widgets = [
            self.nav_gen, self.nav_vault, self.theme_btn, self.seg,
            self.btn_gen, self.btn_copy, self.btn_save, self.slider, self.sbar,
            self.chip_u, self.chip_l, self.chip_d, self.chip_s,
            self.t_up, self.t_lo, self.t_di, self.t_sy, self.t_ex,
            self.wslider, self.btn_fort, self.btn_fort_toggle, self.btn_add, self.btn_lock, self.btn_exp, self.btn_imp,
            self.btn_reset, self.btn_unlock,
        ]
        widgets += self.preset_btns
        widgets += [b for _, b in self.sep_btns]
        widgets += [b for _, b in self.pin_btns]
        widgets += [b for _, b in self.cat_btns]
        for w in widgets:
            w.pal = pal
            w.update()
        self.fort_in.apply(pal)
        self.master.apply(pal)
        self.search.apply(pal)
        self.theme_btn.name = "sun" if self.pal.name == "dark" else "moon"
        self.theme_btn.update()
        self._refresh_strength_colors()
        self._refresh_choice_buttons()
        self.update()

    def toggle_theme(self) -> None:
        self.pal = LIGHT if self.pal.name == "dark" else DARK
        self.settings.setValue("theme", self.pal.name)
        self.apply_theme()
        self.refresh_vault_list()

    def show_page(self, i: int) -> None:
        self.stack.setCurrentIndex(i)
        self.nav_gen.active = i == 0
        self.nav_vault.active = i == 1
        self.nav_gen.update()
        self.nav_vault.update()
        if i == 1:
            self.refresh_vault_list()

    # ------------------------------------------------------------------ generate
    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        self.settings.setValue("mode", mode)
        self._sync_mode_ui()
        titles = {
            "password": ("PASSWORD GENERATOR", "Create cryptographically strong passwords."),
            "passphrase": ("PASSPHRASE GENERATOR", "Memorable phrases from a 512-word dictionary — 9 bits per word."),
            "pin": ("PIN GENERATOR", "Numeric PINs from a CSPRNG. Not for high-value accounts."),
        }
        self.h_title.setText(titles[mode][0])
        self.h_sub.setText(titles[mode][1])
        self.generate()

    def _sync_mode_ui(self) -> None:
        self.pw_box.setVisible(self.mode == "password")
        self.pp_box.setVisible(self.mode == "passphrase")
        self.pin_box.setVisible(self.mode == "pin")
        self.fort.setVisible(self.mode == "password")

    def _flag(self, key: str, val: bool) -> None:
        self.flags[key] = val
        self.settings.setValue(key, val)

    def _len_changed(self, v: int) -> None:
        self.length = v
        self.len_num.setText(str(v))
        self.settings.setValue("length", v)

    def _set_len(self, n: int) -> None:
        self.slider.set_value(n)
        self._len_changed(n)

    def _words_changed(self, v: int) -> None:
        self.words = v
        self.pp_num.setText(str(v))
        self.settings.setValue("words", v)

    def _set_sep(self, s: str) -> None:
        self.sep = s
        self.settings.setValue("sep", s)
        self._refresh_choice_buttons()
        self.generate()

    def _refresh_choice_buttons(self) -> None:
        for key, b in self.sep_btns:
            b.selected = key == self.sep
            b.update()
        for n, b in self.pin_btns:
            b.selected = n == self.pin_len
            b.update()

    def _set_pin(self, n: int) -> None:
        self.pin_len = n
        self.settings.setValue("pin_len", n)
        self._refresh_choice_buttons()
        self.generate()

    def generate(self) -> None:
        self.err_lbl.setText("")
        try:
            if self.mode == "password":
                val = generate_password(
                    self.length,
                    self.flags["uppercase"],
                    self.flags["lowercase"],
                    self.flags["digits"],
                    self.flags["symbols"],
                    self.flags["exclude"],
                )
                pool = pool_size(
                    self.flags["uppercase"],
                    self.flags["lowercase"],
                    self.flags["digits"],
                    self.flags["symbols"],
                    self.flags["exclude"],
                )
                info = analyze_generated(val, mode="password", length=len(val), pool=pool)
            elif self.mode == "passphrase":
                val = generate_passphrase(self.words, self.sep)
                info = analyze_generated(val, mode="passphrase", words=self.words)
            else:
                val = generate_pin(self.pin_len)
                info = analyze_generated(val, mode="pin")
        except (GeneratorError, ValueError) as exc:
            self.err_lbl.setText(str(exc))
            return
        self.current_value = val
        self.pwd_label.setText(val)
        self.level_lbl.setText(info["level"])
        self.bits_lbl.setText(f"{info['bits']} bits  ·  estimate")
        self.crack_lbl.setText(info["crack"])
        self.sbar.level = info["level"]
        self.sbar.bits = info["bits"]
        self.sbar.update()
        c = count_classes(val)
        self.chip_u.count = str(c["upper"])
        self.chip_l.count = str(c["lower"])
        self.chip_d.count = str(c["digits"])
        self.chip_s.count = str(c["symbols"])
        for ch in (self.chip_u, self.chip_l, self.chip_d, self.chip_s):
            ch.update()
        self._refresh_strength_colors()
        # spin generate icon
        self.btn_gen.set_rot(0)
        tween(self.btn_gen, b"rotation", 0.0, 360.0, 360)

    def _refresh_strength_colors(self) -> None:
        col = strength_color(self.sbar.level, self.pal)
        self.level_lbl.setStyleSheet(
            f"color:{col.name()}; font: 800 18px 'Segoe UI'; letter-spacing:1px;"
        )
        self.crack_lbl.setStyleSheet(
            f"color:{self.pal.accent.name()}; font: 600 14px 'Segoe UI';"
        )

    def copy_current(self) -> None:
        if not self.current_value:
            return
        QGuiApplication.clipboard().setText(self.current_value)
        self.btn_copy.success = True
        old = self.btn_copy.text
        old_icon = self.btn_copy.icon
        self.btn_copy.text = "Copied!"
        self.btn_copy.icon = "check"
        self.btn_copy.update()
        self.toasts.show_toast("Password copied!", self.pal)

        def revert():
            self.btn_copy.success = False
            self.btn_copy.text = old
            self.btn_copy.icon = old_icon
            self.btn_copy.update()

        later(1500, revert)

    def save_current(self) -> None:
        if not self.current_value:
            return
        if not self._ensure_unlocked():
            return
        dlg = CredentialDialog(self.pal, seed=self.current_value, parent=self)
        if dlg.exec() and dlg.result_cred:
            try:
                self.vault.add(dlg.result_cred)
                self.toasts.show_toast("Password saved to vault!", self.pal)
                self.refresh_vault_list()
            except VaultError as exc:
                self.toasts.show_toast(str(exc), self.pal)

    def do_fortify(self) -> None:
        src = self.fort_in.text()
        try:
            out = fortify_password(src)
        except GeneratorError as exc:
            self.fort_out.setText(str(exc))
            return
        self.current_value = out
        self.pwd_label.setText(out)
        bits = observed_entropy(out)
        from core.strength import classify, crack_time_label

        info = {"bits": round(bits, 1), "level": classify(bits), "crack": crack_time_label(bits, out)}
        self.level_lbl.setText(info["level"])
        self.bits_lbl.setText(f"{info['bits']} bits  ·  estimate")
        self.crack_lbl.setText(info["crack"])
        self.sbar.level, self.sbar.bits = info["level"], info["bits"]
        self.sbar.update()
        self._refresh_strength_colors()
        self.fort_out.setText(f"Fortified (estimate): {out}")
        self.toasts.show_toast("Password fortified successfully.", self.pal)


    # ------------------------------------------------------------------ vault
    def _toggle_fort(self) -> None:
        vis = self.fort_body.isHidden()
        self.fort_body.setVisible(vis)
        self.fort_out.setVisible(vis and bool(self.fort_out.text()))
        self.btn_fort_toggle.text = "Hide" if vis else "Open"
        self.btn_fort_toggle.update()

    def _guarded(self, fn, silent: bool = False) -> None:
        if self.vault.unlocked:
            fn()
            return
        if silent:
            return
        if self._ensure_unlocked():
            fn()

    def _ensure_unlocked(self) -> bool:
        if self.vault.unlocked:
            return True
        dlg = UnlockDialog(self.pal, creating=not self.vault.exists, parent=self)
        dlg.reset_requested.connect(lambda: (dlg.reject(), self._wipe_confirmed()))
        if not dlg.exec():
            return False
        create = not self.vault.exists
        try:
            if create:
                self.vault.create_new(dlg.password)
            else:
                self.vault.unlock(dlg.password)
        except VaultError as exc:
            self.toasts.show_toast(str(exc), self.pal)
            return False
        self.refresh_vault_list()
        self.toasts.show_toast("Vault created." if create else "Vault unlocked.", self.pal)
        return True

    def _reset_vault_flow(self) -> None:
        dlg = UnlockDialog(self.pal, creating=False, parent=self)
        dlg.reset_requested.connect(lambda: (dlg.reject(), self._wipe_confirmed()))
        dlg.exec()

    def _wipe_confirmed(self) -> None:
        confirm = ConfirmDialog(
            self.pal,
            "Erase the vault?",
            "Every stored credential will be destroyed. This cannot be undone.",
            parent=self,
        )
        if not confirm.exec():
            return
        self.vault.wipe()
        self.refresh_vault_list()
        self.toasts.show_toast("Vault reset. All data erased.", self.pal)

    def unlock_vault(self) -> None:
        self._ensure_unlocked()

    def lock_vault(self) -> None:
        if not self.vault.unlocked:
            return
        self.vault.lock()
        self.refresh_vault_list()
        self.toasts.show_toast("Vault locked.", self.pal)

    def _set_cat(self, name: str) -> None:
        if not self.vault.unlocked and not self._ensure_unlocked():
            return
        self.vault_filter = name
        self.refresh_vault_list()

    def refresh_vault_list(self) -> None:
        while self.list_host.count():
            item = self.list_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.vault.unlocked:
            self.empty_lbl.setVisible(False)
            for _ in range(4):
                self.list_host.addWidget(self._ghost_row())
            self.list_host.addStretch()
            return
        rows = self.vault.search(self.search.text(), self.vault_filter)
        self.empty_lbl.setVisible(len(rows) == 0)
        for cred in rows:
            self.list_host.addWidget(self._cred_row(cred))
        self.list_host.addStretch()

    def _ghost_row(self) -> QWidget:
        pal = self.pal
        row = QFrame()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet(
            f"QFrame {{ background:{pal.elevated.name()}; border:1px solid {pal.border.name()}; border-radius:14px; }}"
        )
        h = QHBoxLayout(row)
        h.setContentsMargins(14, 14, 14, 14)
        col = QVBoxLayout()
        name = QLabel("████████    ••••••")
        name.setStyleSheet(
            f"color:{pal.muted.name()}; font: 700 13px 'Segoe UI'; letter-spacing:3px; background:transparent; border:none;"
        )
        meta = QLabel("••••••••••••    ••••    ••••••••")
        meta.setStyleSheet(f"color:{pal.border.name()}; font: 11px 'Segoe UI'; background:transparent; border:none;")
        col.addWidget(name)
        col.addWidget(meta)
        h.addLayout(col, 1)
        secret = QLabel("••••••••••••")
        secret.setStyleSheet(f"color:{pal.muted.name()}; font: 12px Consolas; background:transparent; border:none;")
        h.addWidget(secret)
        row.mousePressEvent = lambda e: self._ghost_clicked()  # type: ignore[method-assign]
        return row

    def _ghost_clicked(self) -> None:
        if self._ensure_unlocked():
            self.refresh_vault_list()

    def _on_search(self, _text: str) -> None:
        if self.vault.unlocked:
            self.refresh_vault_list()

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent

        if obj is getattr(self, "search", None) and event.type() == QEvent.Type.MouseButtonPress:
            if not self.vault.unlocked:
                self._ensure_unlocked()
                return True
        return super().eventFilter(obj, event)

    def _cred_row(self, cred) -> QWidget:
        pal = self.pal
        row = QFrame()
        row.setStyleSheet(
            f"QFrame {{ background:{pal.elevated.name()}; border:1px solid {pal.border.name()}; border-radius:14px; }}"
        )
        h = QHBoxLayout(row)
        h.setContentsMargins(14, 10, 10, 10)
        col = QVBoxLayout()
        name = QLabel(cred.service)
        name.setStyleSheet(f"color:{pal.text.name()}; font: 700 13px 'Segoe UI'; background:transparent; border:none;")
        meta = QLabel(f"{cred.website or '—'}  ·  {cred.category}  ·  {cred.username or 'no user'}")
        meta.setStyleSheet(f"color:{pal.muted.name()}; font: 11px 'Segoe UI'; background:transparent; border:none;")
        col.addWidget(name)
        col.addWidget(meta)
        h.addLayout(col, 1)
        secret = QLabel("••••••••")
        secret.setStyleSheet(
            f"color:{pal.secondary.name()}; font: 12px 'Cascadia Mono','Consolas'; background:transparent; border:none;"
        )
        h.addWidget(secret)
        shown = {"v": False}

        def toggle():
            shown["v"] = not shown["v"]
            secret.setText(cred.password if shown["v"] else "••••••••")
            eye.name = "eye-off" if shown["v"] else "eye"
            eye.update()

        eye = IconButton("eye", "Show / hide")
        copy = IconButton("copy", "Copy")
        edit = IconButton("edit", "Edit")
        delete = IconButton("delete", "Delete")
        for b in (eye, copy, edit, delete):
            b.pal = pal
        eye.clicked.connect(toggle)
        copy.clicked.connect(lambda: self._copy_text(cred.password))
        edit.clicked.connect(lambda c=cred: self._edit_cred(c))
        delete.clicked.connect(lambda c=cred: self._del_cred(c))
        for b in (eye, copy, edit, delete):
            h.addWidget(b)
        return row

    def _copy_text(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)
        self.toasts.show_toast("Password copied!", self.pal)

    def _edit_cred(self, cred) -> None:
        if not self._ensure_unlocked():
            return
        dlg = CredentialDialog(self.pal, existing=cred, parent=self)
        if dlg.exec() and dlg.result_cred:
            try:
                if cred is None:
                    self.vault.add(dlg.result_cred)
                else:
                    self.vault.update(dlg.result_cred)
                self.refresh_vault_list()
            except VaultError as exc:
                self.toasts.show_toast(str(exc), self.pal)

    def _del_cred(self, cred) -> None:
        dlg = ConfirmDialog(self.pal, "Delete credential?", f"Remove “{cred.service}” from the vault.", parent=self)
        if dlg.exec():
            self.vault.delete(cred.id)
            self.refresh_vault_list()

    def export_backup(self) -> None:
        if not self._ensure_unlocked():
            return
        if not self.vault.exists and not self.vault.entries:
            self.toasts.show_toast("Nothing to export.", self.pal)
            return
        chooser = ExportDialog(self.pal, parent=self)
        if not chooser.exec():
            return
        kind = chooser.choice
        filters = {
            "bin": ("keygen-backup.bin", "KEYGEN encrypted (*.bin)"),
            "csv": ("keygen-chrome.csv", "Browser CSV (*.csv)"),
            "json": ("keygen-export.json", "JSON (*.json)"),
            "txt": ("keygen-export.txt", "Text (*.txt)"),
            "md": ("keygen-export.md", "Markdown (*.md)"),
        }
        default, filt = filters[kind]
        path, _ = QFileDialog.getSaveFileName(self, "Export", default, filt)
        if not path:
            return
        dest = Path(path)
        ext = {"bin": ".bin", "csv": ".csv", "json": ".json", "txt": ".txt", "md": ".md"}[kind]
        if dest.suffix.lower() != ext:
            dest = dest.with_suffix(ext)
        try:
            if kind == "bin":
                self.vault.export_backup(dest)
                msg = "Encrypted backup saved. Open it only in KEYGEN → Import."
            elif kind == "csv":
                n = self.vault.export_browser_csv(dest)
                msg = f"Browser CSV ({n}). Chrome: Password Manager → Settings → Import."
            elif kind == "json":
                n = self.vault.export_json(dest)
                msg = f"JSON ({n}) — not encrypted. Re-import in KEYGEN."
            elif kind == "txt":
                n = self.vault.export_txt(dest)
                msg = f"Text file ({n}) — readable, not encrypted."
            else:
                n = self.vault.export_markdown(dest)
                msg = f"Markdown ({n}) — readable, not encrypted."
            self.toasts.show_toast(msg, self.pal)
        except Exception as exc:
            self.toasts.show_toast(str(exc), self.pal)

    def import_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import backup", "", "KEYGEN backup (*.bin);;All files (*)")
        if not path:
            return
        dlg = UnlockDialog(self.pal, creating=False, parent=self)
        dlg.title.setText("Import backup")
        dlg.body.setText("Enter the master password that encrypted this backup file.")
        if not dlg.exec():
            return
        try:
            self.vault.import_backup(Path(path), dlg.password)
            self.refresh_vault_list()
            self.toasts.show_toast("Backup imported.", self.pal)
        except VaultError as exc:
            self.toasts.show_toast(str(exc), self.pal)

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self.toasts.setGeometry(0, 0, self.width(), self.height())

    def keyPressEvent(self, e) -> None:
        if e.key() == Qt.Key.Key_Escape:
            for w in self.findChildren(CredentialDialog):
                w.reject()
            for w in self.findChildren(UnlockDialog):
                w.reject()
        super().keyPressEvent(e)
