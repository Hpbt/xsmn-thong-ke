"""Tải kết quả xổ số Miền Nam theo ngày từ minhngoc.net.vn -> data/<đài>.csv

Mỗi trang https://www.minhngoc.net.vn/ket-qua-xo-so/mien-nam/DD-MM-YYYY.html chứa
kết quả mọi đài quay hôm đó (có dữ liệu từ 01/01/2008).

Dùng:
  python scrape.py                     # cập nhật: từ 7 ngày trước kỳ mới nhất đã có tới hôm nay
  python scrape.py --since 2008-01-01  # tải toàn bộ lịch sử (chậm, ~1 giờ)
"""
import argparse, csv, glob, json, os, re, sys, time, datetime as dt
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PRIZES = ["G8", "G7", "G6", "G5", "G4", "G3", "G2", "G1", "DB"]
CLASSES = ["giai8", "giai7", "giai6", "giai5", "giai4", "giai3", "giai2", "giai1", "giaidb"]
VN = dt.timezone(dt.timedelta(hours=7))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DELAY = 0.5  # giây nghỉ giữa các lần tải của mỗi luồng, để không bị chặn


def fetch(d):
    url = f"https://www.minhngoc.net.vn/ket-qua-xo-so/mien-nam/{d:%d-%m-%Y}.html"
    for attempt in range(5):
        time.sleep(DELAY)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "vi"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            wait = 60 if e.code in (403, 418, 429) else 3 * (attempt + 1)
            print(f"  HTTP {e.code} {url} — chờ {wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception:
            time.sleep(3 * (attempt + 1))
    print("  lỗi tải", url, file=sys.stderr)
    return None


def parse(d, html):
    """-> list[(slug, tên đài, row)] của ngày d; [] nếu không có kỳ quay."""
    if not html:
        return []
    i = html.find('<div class="box_kqxs">')
    if i < 0:
        return []
    j = html.find('<div class="box_kqxs">', i + 10)
    box = html[i : j if j > 0 else len(html)]
    m = re.search(r'class="title">.*?mien-nam/(\d\d-\d\d-\d{4})\.html', box, re.S)
    if not m or m.group(1) != f"{d:%d-%m-%Y}":  # trang tự chuyển sang ngày khác khi không có kỳ quay
        return []
    out = []
    for col in box.split('class="rightcl"')[1:]:
        st = re.search(r'class="tinh">\s*<a href="/xo-so-mien-nam/([a-z0-9-]+)\.html"[^>]*>([^<]+)</a>', col)
        if not st:
            continue
        row = {"date": d.isoformat()}
        for key, cls in zip(PRIZES, CLASSES):
            mm = re.search(r'<td class="%s">(.*?)</td>' % cls, col, re.S)
            row[key] = " ".join(re.findall(r"<div>\s*(\d+)\s*</div>", mm.group(1))) if mm else ""
        if re.fullmatch(r"\d\d", row["G8"]) and row["G1"]:
            out.append((st.group(1), st.group(2).strip(), row))
    return out


def load():
    data = {}
    for f in glob.glob(os.path.join(DATA, "*.csv")):
        slug = os.path.basename(f)[:-4]
        data[slug] = {r["date"]: r for r in csv.DictReader(open(f, encoding="utf-8"))}
    return data


def save(data, meta):
    for slug, rows in data.items():
        with open(os.path.join(DATA, f"{slug}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date"] + PRIZES, lineterminator="\n")
            w.writeheader()
            w.writerows(rows[k] for k in sorted(rows))
    with open(os.path.join(DATA, "stations.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(dict(sorted(meta.items())), f, ensure_ascii=False, indent=1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="YYYY-MM-DD")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    data = load()
    meta_path = os.path.join(DATA, "stations.json")
    meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
    today = dt.datetime.now(VN).date()
    if a.since:
        start = dt.date.fromisoformat(a.since)
    else:
        latest = max((max(v) for v in data.values() if v), default="2008-01-01")
        start = dt.date.fromisoformat(latest) - dt.timedelta(days=7)
    days = [start + dt.timedelta(n) for n in range((today - start).days + 1)]
    print(f"Tải {len(days)} ngày: {days[0]} → {days[-1]}", flush=True)
    added = 0
    for attempt in range(2):  # lượt 2: thử lại các ngày trống (lỗi mạng, trang chưa đủ dữ liệu)
        empty = []
        with ThreadPoolExecutor(a.workers) as ex:
            for n, (d, res) in enumerate(zip(days, ex.map(lambda d: parse(d, fetch(d)), days)), 1):
                if not res:
                    empty.append(d)
                for slug, name, row in res:
                    meta[slug] = {"name": name}
                    if data.setdefault(slug, {}).get(row["date"]) != row:
                        added += 1
                    data[slug][row["date"]] = row
                if n % 250 == 0:
                    save(data, meta)
                    print(f"  {n}/{len(days)} ({d})", flush=True)
        days = empty
    save(data, meta)
    print(f"Ngày không có kết quả: {len(days)}")
    print(f"{added} kỳ mới/cập nhật; {len(data)} đài; tổng {sum(map(len, data.values()))} kỳ")


if __name__ == "__main__":
    main()
