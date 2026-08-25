# -*- mode: python ; coding: utf-8 -*-
"""Slim KEYGEN bundle: Qt Widgets + cryptography only."""
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).parent

# Heavy / unused Qt + stdlib. Visuals stay native QPainter — no extra modules.
EXCLUDES = [
    "tkinter", "turtle", "unittest", "pydoc", "doctest", "lib2to3",
    "xmlrpc", "http.server", "wsgiref", "idlelib", "turtledemo",
    "PySide6.QtWebEngine", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets", "PySide6.QtWebChannel", "PySide6.QtWebSockets",
    "PySide6.QtWebView", "PySide6.QtQuick", "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets", "PySide6.QtQml",
    "PySide6.QtQmlModels", "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtBluetooth", "PySide6.QtNfc",
    "PySide6.QtPositioning", "PySide6.QtLocation", "PySide6.QtSensors",
    "PySide6.QtSerialPort", "PySide6.QtSerialBus", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtGraphs", "PySide6.QtRemoteObjects", "PySide6.QtScxml",
    "PySide6.QtTextToSpeech", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtUiTools", "PySide6.QtHttpServer", "PySide6.QtDBus",
    "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets", "PySide6.QtSvg",
    "PySide6.QtSvgWidgets", "PySide6.QtXml", "PySide6.QtNetworkAuth",
    "matplotlib", "numpy", "PIL", "cv2", "pandas", "scipy",
]

DROP_SUBSTR = (
    "Qt6WebEngine", "Qt6Quick", "Qt6Qml", "Qt6Multimedia", "Qt6Pdf",
    "Qt6Sql", "Qt6Bluetooth", "Qt6Nfc", "Qt6Positioning", "Qt6Location",
    "Qt6Sensors", "Qt6Serial", "Qt63D", "Qt6Charts", "Qt6DataVisualization",
    "Qt6RemoteObjects", "Qt6Scxml", "Qt6TextToSpeech", "Qt6Designer",
    "Qt6Help", "Qt6Svg", "Qt6Xml", "Qt6OpenGL", "Qt6VirtualKeyboard",
    "Qt6WebChannel", "Qt6WebSockets", "Qt6WebView", "Qt6HttpServer",
    "Qt6NetworkAuth", "translations/", "qml/",
    "generic/qtuiotouchplugin",
)


def _keep(path: str) -> bool:
    p = path.replace("\\", "/")
    return not any(s in p for s in DROP_SUBSTR)


a = Analysis(
    [str(root / "project.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "packaging" / "app.ico"), "packaging"),
        (str(root / "packaging" / "keygen-icon.png"), "packaging"),
    ],
    hiddenimports=["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets"],
    hookspath=[],
    hooksconfig={
        "gi": {"module-versions": {}},
    },
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)
a.binaries = [b for b in a.binaries if _keep(str(b[1]))]
a.datas = [d for d in a.datas if _keep(str(d[1]))]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="KEYGEN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(root / "packaging" / "app.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="KEYGEN",
)
