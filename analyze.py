"""Thống kê giải 8 + giải ĐB của một đài, kiểm định ngẫu nhiên, backtest các 'quy luật' phổ biến.

Dùng: python analyze.py [file.csv]   (mặc định: data/vinh-long.csv)
"""
import csv, math, os, random, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "vinh-long.csv")
rows = list(csv.DictReader(open(os.path.join(HERE, CSV), encoding="utf-8")))
g8 = [int(r["G8"]) for r in rows]
N = len(g8)


def chi2_sf(x, k):
    """P(X^2_k >= x) — xấp xỉ Wilson–Hilferty."""
    z = ((x / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    return 0.5 * math.erfc(z / math.sqrt(2))


def chi2_uniform(values, cats):
    c = Counter(values)
    e = len(values) / len(cats)
    x = sum((c[v] - e) ** 2 / e for v in cats)
    return x, chi2_sf(x, len(cats) - 1)


print(f"Số kỳ: {N}  ({rows[0]['date']} → {rows[-1]['date']})\n")

# 1. Tần suất
cnt = Counter(g8)
x, p = chi2_uniform(g8, range(100))
print("== 1. TẦN SUẤT 00–99 (kỳ vọng mỗi số %.1f lần)" % (N / 100))
top = cnt.most_common()
print("Về nhiều nhất:", ", ".join(f"{n:02d}({c})" for n, c in top[:10]))
print("Về ít nhất:   ", ", ".join(f"{n:02d}({cnt[n]})" for n in sorted(range(100), key=lambda n: cnt[n])[:10]))
print(f"Chi-square đều 100 số: X²={x:.1f}, df=99, p={p:.3f}")

# 2. Đầu / đuôi / chẵn lẻ / tổng
heads, tails = [v // 10 for v in g8], [v % 10 for v in g8]
for name, arr in (("Đầu", heads), ("Đuôi", tails)):
    c = Counter(arr)
    x, p = chi2_uniform(arr, range(10))
    print(f"\n== {name}: " + "  ".join(f"{d}:{c[d]}" for d in range(10)) + f"   (X²={x:.1f}, p={p:.3f})")
even = sum(1 for v in g8 if v % 2 == 0)
print(f"\nChẵn {even} / Lẻ {N - even}")
big = sum(1 for v in g8 if v >= 50)
print(f"Lớn (50–99) {big} / Nhỏ (00–49) {N - big}")
sums = Counter((v // 10 + v % 10) % 10 for v in g8)
x, p = chi2_uniform([(v // 10 + v % 10) % 10 for v in g8], range(10))
print("Tổng (chạm, mod 10): " + "  ".join(f"{d}:{sums[d]}" for d in range(10)) + f"   (p={p:.3f})")

# 3. Theo từng giai đoạn
print("\n== 3. TOP 5 THEO TỪNG GIAI ĐOẠN (xem 'số nóng' có giữ được không)")
for a in range(0, N, 260):
    seg = g8[a : a + 260]
    print(f"  {rows[a]['date'][:4]}–{rows[min(a + 259, N - 1)]['date'][:4]}: " + ", ".join(f"{n:02d}({c})" for n, c in Counter(seg).most_common(5)))

# 4. Lô gan
last = {}
gaps_all = []
maxgap = Counter()
for i, v in enumerate(g8):
    if v in last:
        gaps_all.append(i - last[v])
        maxgap[v] = max(maxgap[v], i - last[v])
    last[v] = i
cur = {n: (N - 1 - last[n]) if n in last else N for n in range(100)}
print("\n== 4. LÔ GAN (số kỳ chưa về tính đến kỳ gần nhất)")
print("Gan lâu nhất hiện tại:", ", ".join(f"{n:02d}({g})" for n, g in sorted(cur.items(), key=lambda t: -t[1])[:10]))
print("Kỷ lục gan:", ", ".join(f"{n:02d}({g})" for n, g in maxgap.most_common(5)))
print(f"Khoảng cách TB giữa 2 lần về: {sum(gaps_all) / len(gaps_all):.1f} kỳ (lý thuyết 100)")

# 5. Độc lập giữa các kỳ
print("\n== 5. KỲ TRƯỚC CÓ ẢNH HƯỞNG KỲ SAU KHÔNG?")
rep = sum(1 for a, b in zip(g8, g8[1:]) if a == b)
print(f"G8 lặp lại y hệt kỳ trước: {rep} lần / {N - 1} (kỳ vọng {(N - 1) / 100:.1f})")
# bảng chuyển đầu->đầu
obs = Counter(zip(heads, heads[1:]))
rh, ch = Counter(heads[:-1]), Counter(heads[1:])
x = sum((obs[(i, j)] - rh[i] * ch[j] / (N - 1)) ** 2 / (rh[i] * ch[j] / (N - 1)) for i in range(10) for j in range(10))
print(f"Chuyển đầu→đầu (độc lập?): X²={x:.1f}, df=81, p={chi2_sf(x, 81):.3f}")
mean = sum(g8) / N
var = sum((v - mean) ** 2 for v in g8) / N
for lag in (1, 2, 4, 52):
    r = sum((g8[i] - mean) * (g8[i + lag] - mean) for i in range(N - lag)) / (N - lag) / var
    print(f"  Tự tương quan lag {lag:>2}: r={r:+.3f}  (ngưỡng ý nghĩa ±{2 / math.sqrt(N):.3f})")
# G8 có nằm trong lô tô (2 số cuối 18 giải) kỳ trước không — "bạc nhớ"
def loto(r):
    return {int(x[-2:]) for k in ("G8", "G7", "G6", "G5", "G4", "G3", "G2", "G1", "DB") for x in r[k].split()}
hit = sum(1 for a, b in zip(rows, rows[1:]) if int(b["G8"]) in loto(a))
exp = sum(len(loto(a)) / 100 for a in rows[:-1])
print(f"G8 trùng 1 lô tô của kỳ trước: {hit} lần (kỳ vọng ngẫu nhiên {exp:.0f})")

# 6. Backtest walk-forward: mỗi kỳ chọn K số theo 'quy luật', đếm trúng
K = 10
WARM = 200
def s_hot_all(h): c = Counter(h); return [n for n, _ in sorted(c.items(), key=lambda t: -t[1])][:K]
def s_hot_recent(h): c = Counter(h[-100:]); return sorted(range(100), key=lambda n: -c[n])[:K]
def s_cold_freq(h): c = Counter(h); return sorted(range(100), key=lambda n: c[n])[:K]
def s_gan(h):
    l = {v: i for i, v in enumerate(h)}
    return sorted(range(100), key=lambda n: l.get(n, -1))[:K]
def s_last(h): return [h[-1]] + [(h[-1] + d) % 100 for d in range(1, K)]
def s_mirror(h):  # đảo số + các số 'bóng'
    v = h[-1]; return list(dict.fromkeys([(v % 10) * 10 + v // 10] + [(v + 11 * d) % 100 for d in range(1, 20)]))[:K]
rng = random.Random(2026)
def s_random(h): return rng.sample(range(100), K)
strategies = {"Số nóng toàn bộ lịch sử": s_hot_all, "Số nóng 100 kỳ gần nhất": s_hot_recent,
              "Số lạnh (ít về nhất)": s_cold_freq, "Lô gan lâu nhất": s_gan,
              "Quanh số kỳ trước": s_last, "Đảo số / bóng kỳ trước": s_mirror, "Chọn ngẫu nhiên": s_random}
tests = N - WARM
print(f"\n== 6. BACKTEST {tests} kỳ (từ {rows[WARM]['date']}): mỗi kỳ chọn {K} số, trúng nếu G8 nằm trong đó")
print(f"   Kỳ vọng thuần may rủi: {K}% (≈{tests * K / 100:.0f} lần trúng, sai số ±{2 * math.sqrt(tests * .1 * .9):.0f})")
for name, f in strategies.items():
    h = sum(1 for i in range(WARM, N) if g8[i] in set(f(g8[:i])))
    print(f"   {name:<28} {h:>4} lần = {100 * h / tests:5.2f}%")

# 7. Thống kê 8 kỳ tiếp theo: xác suất
print("\n== 7. XÁC SUẤT CHO 8 KỲ TỚI (nếu mỗi kỳ là ngẫu nhiên đều)")
print(f"   Đoán đúng 1 số cụ thể ở 1 kỳ: 1%.  Đoán đúng cả 8 kỳ: 1/10^16.")
print(f"   1 số cụ thể về ít nhất 1 lần trong 8 kỳ: {100 * (1 - .99 ** 8):.1f}%")
print(f"   Bộ 10 số trúng ít nhất 1 lần trong 8 kỳ: {100 * (1 - .9 ** 8):.1f}%")

# 8. Giải đặc biệt
db = [r["DB"] for r in rows if r["DB"]]
d6 = [x for x in db if len(x) == 6]
print(f"\n== 8. GIẢI ĐẶC BIỆT: {len(db)} kỳ có số, {len(d6)} kỳ 6 chữ số")
best = ""
for p in range(6):
    c = Counter(x[p] for x in d6)
    x, pv = chi2_uniform([x[p] for x in d6], [str(i) for i in range(10)])
    best += c.most_common(1)[0][0]
    print(f"   Vị trí {p + 1}: " + " ".join(f"{i}:{c[str(i)]}" for i in range(10)) + f"   p={pv:.2f}")
t2 = [int(x[-2:]) for x in db]
x, pv = chi2_uniform(t2, range(100))
print("   2 số cuối nhiều nhất:", ", ".join(f"{n:02d}({c})" for n, c in Counter(t2).most_common(8)), f"  p={pv:.2f}")
print("   ĐB trùng nhau:", [x for x, c in Counter(d6).items() if c > 1])
print("   Ghép chữ số hay về nhất từng vị trí:", best)
print("   5 kỳ gần nhất:", ", ".join(f"{r['date']}={r['DB']}" for r in rows[-5:]))
