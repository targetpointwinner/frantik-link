#!/usr/bin/env python3
"""
Обновление отзывов-сторис.
Положи новые картинки-отзывы (JPG/PNG, вертикальные 9:16) в папку-источник
и запусти:  python3 sync-reviews.py "/путь/к/папке/Отзывы"

Скрипт сожмёт их в WebP (assets/reviews/NN.webp) и перепишет reviews.json,
который читает сайт. Порядок — по имени файла.
"""
import os, sys, glob, json
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/Отзывы frantik.by")
OUT = os.path.join(ROOT, "assets", "reviews")

def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.webp")):
        os.remove(f)
    files = sorted(glob.glob(os.path.join(SRC, "*.[Jj][Pp][Gg]")) +
                   glob.glob(os.path.join(SRC, "*.[Jj][Pp][Ee][Gg]")) +
                   glob.glob(os.path.join(SRC, "*.[Pp][Nn][Gg]")))
    items = []
    for i, f in enumerate(files, 1):
        im = Image.open(f).convert("RGB")
        im.thumbnail((1200, 1200), Image.LANCZOS)
        name = f"{i:02d}.webp"
        im.save(os.path.join(OUT, name), "WEBP", quality=82, method=5)
        items.append({"src": f"assets/reviews/{name}", "w": im.width, "h": im.height})
    json.dump({"items": items}, open(os.path.join(ROOT, "reviews.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✓ отзывов: {len(items)}")

if __name__ == "__main__":
    main()
