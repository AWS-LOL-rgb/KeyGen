"""Write a multi-size Windows .ico Inno Setup accepts."""
from __future__ import annotations
from pathlib import Path

def main() -> None:
    from PIL import Image
    root = Path(__file__).resolve().parents[1]
    png = root / "packaging" / "keygen-icon.png"
    ico = root / "packaging" / "app.ico"
    if not png.exists():
        raise SystemExit(f"missing {png}")
    im = Image.open(png).convert("RGBA")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    im.save(ico, format="ICO", sizes=sizes)
    print(f"wrote {ico} ({ico.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
