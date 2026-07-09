#!/usr/bin/env python3
"""
Синхронизация школьной коллекции frantik.by с публичной папки Яндекс.Диска.

Папка на Я.Диске:  Школа 2026-2027 год / {Для девочек, Для мальчиков}
Фото лежат в .heic — браузеры его не показывают, поэтому берём готовые
JPEG-превью Яндекса и переупаковываем в лёгкий WebP в catalog/{girls,boys}/.
Результат описывается в catalog.json, который читает index.html.

Запуск:
    python3 sync.py               # докачать новое (идемпотентно)
    python3 sync.py --force       # перекачать всё заново
    LIMIT=4 python3 sync.py       # тест на 4 фото в каждой категории
"""
import os, io, sys, json, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

PUBLIC_KEY = "https://disk.yandex.ru/d/u7Tb05aUevhcqA"
ROOT = os.path.dirname(os.path.abspath(__file__))
# соответствие «папка на Я.Диске» -> «категория на сайте»
CATS = {"/Для девочек": "girls", "/Для мальчиков": "boys"}

MAX_SIDE = 1000          # длинная сторона WebP
QUALITY  = 76            # качество WebP
WORKERS  = 8             # параллельные загрузки
# порядок предпочтения размеров превью Яндекса
SIZE_PREF = ["XXXL", "XXL", "XL", "L", "M", "DEFAULT"]

API = "https://cloud-api.yandex.net/v1/disk/public/resources"
FORCE = "--force" in sys.argv
LIMIT = int(os.environ.get("LIMIT", "0"))


def api(path=None, limit=200, offset=0):
    q = {"public_key": PUBLIC_KEY, "limit": limit, "offset": offset,
         "sort": "name", "preview_crop": "false"}
    if path:
        q["path"] = path
    url = API + "?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))


def list_images(path):
    """Все файлы-картинки в папке, с пагинацией, отсортированные по имени."""
    out, off = [], 0
    while True:
        d = api(path, limit=200, offset=off)
        emb = d.get("_embedded", {})
        items = emb.get("items", [])
        for i in items:
            if i.get("type") == "file" and (i.get("media_type") == "image"
                                            or i.get("mime_type", "").startswith("image")):
                out.append(i)
        total = emb.get("total", 0)
        off += 200
        if off >= total or not items:
            break
    out.sort(key=lambda i: i["name"])
    return out


def pick_url(item):
    sizes = {s["name"]: s["url"] for s in item.get("sizes", [])}
    for name in SIZE_PREF:
        if name in sizes:
            return sizes[name]
    return item.get("preview") or item.get("file")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "frantik-sync/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))


def process(item, cat, idx):
    name = f"{idx:04d}.webp"
    dst = os.path.join(ROOT, "catalog", cat, name)
    rel = f"catalog/{cat}/{name}"
    if os.path.exists(dst) and not FORCE:
        try:
            with Image.open(dst) as im:
                return {"src": rel, "w": im.width, "h": im.height}
        except Exception:
            pass  # битый — перекачаем
    data = fetch(pick_url(item))
    im = Image.open(io.BytesIO(data))
    im = im.convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    im.save(dst, "WEBP", quality=QUALITY, method=5)
    return {"src": rel, "w": im.width, "h": im.height}


def main():
    manifest = {"updated": time.strftime("%d.%m.%Y"), "collection": "Школа 2026/2027"}
    for path, cat in CATS.items():
        os.makedirs(os.path.join(ROOT, "catalog", cat), exist_ok=True)
        print(f"\n=== {path}  ->  {cat} ===")
        items = list_images(path)
        if LIMIT:
            items = items[:LIMIT]
        print(f"  фото: {len(items)}")
        results = [None] * len(items)
        done = 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(process, it, cat, i): i for i, it in enumerate(items)}
            for f in as_completed(futs):
                i = futs[f]
                try:
                    results[i] = f.result()
                except Exception as e:
                    print(f"  ! {items[i]['name']}: {e}")
                done += 1
                if done % 25 == 0 or done == len(items):
                    print(f"  {done}/{len(items)}")
        manifest[cat] = [r for r in results if r]
    with open(os.path.join(ROOT, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f"\n✓ catalog.json: girls={len(manifest.get('girls',[]))} "
          f"boys={len(manifest.get('boys',[]))}")


if __name__ == "__main__":
    main()
