"""Tạo dữ liệu JSON cho trang web từ data/*.csv -> site/data/

Với mỗi đài: thống kê giải 8 + ĐB, bộ số tham khảo cho kỳ tới, và backtest
walk-forward (gợi ý của từng kỳ trong quá khứ chỉ dùng dữ liệu trước kỳ đó).
"""
import csv, glob, json, math, os, random, sys, datetime as dt
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "site", "data")
VN = dt.timezone(dt.timedelta(hours=7))
K = 6        # số lượng số gợi ý mỗi nhóm
WARM = 100   # số kỳ khởi động trước khi tính backtest


def chi2_p(counts, n_cat):
    n = sum(counts)
    e = n / n_cat
    x = sum((c - e) ** 2 / e for c in counts)
    k = n_cat - 1
    z = ((x / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    return round(0.5 * math.erfc(z / math.sqrt(2)), 3)


def pick_hot(freq, last):
    return sorted(range(100), key=lambda n: (-freq[n], -last.get(n, -1)))[:K]


def pick_gan(last):
    return sorted(range(100), key=lambda n: (last.get(n, -1), n))[:K]


def pick_random(slug, date):
    return sorted(random.Random(f"{slug}|{date}").sample(range(100), K))


def db_random(slug, date):
    return "%06d" % random.Random(f"db|{slug}|{date}").randrange(10 ** 6)


def next_draw(last_date, weekdays, today):
    d = max(last_date + dt.timedelta(1), today)
    for _ in range(14):
        if d.weekday() in weekdays:
            return d
        d += dt.timedelta(1)
    return None


def station(slug, name, rows, today):
    g8 = [int(r["G8"]) for r in rows]
    dates = [r["date"] for r in rows]
    last_date = dt.date.fromisoformat(dates[-1])
    recent = [dt.date.fromisoformat(d) for d in dates if (last_date - dt.date.fromisoformat(d)).days < 365]
    wd_count = Counter(d.weekday() for d in recent)
    weekdays = sorted(w for w, c in wd_count.items() if c >= 10)
    active = (today - last_date).days <= 21
    nxt = next_draw(last_date, weekdays, today) if active else None

    # Walk-forward: gợi ý cho kỳ i chỉ dựa trên g8[:i]
    freq, last = Counter(), {}
    hits = {"hot": 0, "gan": 0, "random": 0}
    history = []
    for i, v in enumerate(g8):
        if i >= WARM:
            s = {"hot": pick_hot(freq, last), "gan": pick_gan(last), "random": pick_random(slug, dates[i])}
            for k in hits:
                hits[k] += v in s[k]
            history.append({"date": dates[i], "actual": v, **s})
        freq[v] += 1
        last[v] = i
    n = len(g8)
    gap_now = [n - 1 - last[x] if x in last else n for x in range(100)]
    maxgap = [0] * 100
    prev = {}
    for i, v in enumerate(g8):
        if v in prev:
            maxgap[v] = max(maxgap[v], i - prev[v] - 1)
        prev[v] = i
    for x in range(100):
        maxgap[x] = max(maxgap[x], gap_now[x])

    db = [r["DB"] for r in rows if r["DB"]]
    d6 = [x for x in db if len(x) == 6]
    pos = [[sum(1 for x in d6 if x[p] == str(dg)) for dg in range(10)] for p in range(6)]
    tail = Counter(int(x[-2:]) for x in db)
    tested = len(history)

    detail = {
        "slug": slug, "name": name, "count": n, "first": dates[0], "last": dates[-1],
        "weekdays": weekdays, "next": nxt.isoformat() if nxt else None,
        "latest": rows[-10:][::-1],
        "g8": {"freq": [freq[x] for x in range(100)], "gap": gap_now, "maxgap": maxgap,
               "p": chi2_p([freq[x] for x in range(100)], 100)},
        "db": {"count": len(db), "count6": len(d6), "pos": pos,
               "pos_p": [chi2_p(c, 10) for c in pos] if d6 else [],
               "tail_top": [[x, c] for x, c in tail.most_common(10)]},
        "suggest": {
            "for": nxt.isoformat() if nxt else None,
            "hot": pick_hot(freq, last), "gan": pick_gan(last),
            "random": pick_random(slug, nxt.isoformat()) if nxt else [],
            "db_digits": "".join(str(max(range(10), key=lambda dg: c[dg])) for c in pos) if d6 else None,
            "db_random": db_random(slug, nxt.isoformat()) if nxt else None,
        },
        "track": {"tested": tested, "expected": K / 100, "hits": hits, "recent": history[-12:][::-1]},
    }
    summary = {"slug": slug, "name": name, "count": n, "first": dates[0], "last": dates[-1],
               "weekdays": weekdays, "next": detail["next"], "active": active,
               "last_g8": rows[-1]["G8"], "last_db": rows[-1]["DB"],
               "suggest": detail["suggest"], "tested": tested, "hits": hits}
    return summary, detail


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    meta = json.load(open(os.path.join(DATA, "stations.json"), encoding="utf-8"))
    now = dt.datetime.now(VN)
    os.makedirs(os.path.join(OUT, "st"), exist_ok=True)
    stations = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.csv"))):
        slug = os.path.basename(f)[:-4]
        rows = list(csv.DictReader(open(f, encoding="utf-8")))
        if len(rows) < WARM + 10:
            continue
        s, d = station(slug, meta.get(slug, {}).get("name", slug), rows, now.date())
        stations.append(s)
        json.dump(d, open(os.path.join(OUT, "st", f"{slug}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    tot = {k: sum(s["hits"][k] for s in stations) for k in ("hot", "gan", "random")}
    tested = sum(s["tested"] for s in stations)
    summary = {"updated": now.isoformat(timespec="minutes"), "k": K, "tested": tested, "hits": tot,
               "draws": sum(s["count"] for s in stations), "stations": stations}
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    if not tested:
        print("Chưa đủ dữ liệu để backtest"); return
    print(f"{len(stations)} đài, {summary['draws']} kỳ; backtest {tested} kỳ:",
          {k: f"{100 * v / tested:.2f}%" for k, v in tot.items()}, f"(kỳ vọng {K}%)")


if __name__ == "__main__":
    main()
