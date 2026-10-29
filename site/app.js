"use strict";

const DAYS = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
const SHORT = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
const PRIZES = [["G8", "Giải 8"], ["G7", "Giải 7"], ["G6", "Giải 6"], ["G5", "Giải 5"], ["G4", "Giải 4"],
  ["G3", "Giải 3"], ["G2", "Giải 2"], ["G1", "Giải 1"], ["DB", "Đặc biệt"]];
const STRATS = [["hot", "Số nóng"], ["gan", "Lô gan"], ["random", "Ngẫu nhiên"]];
const app = document.getElementById("app");
const tip = document.getElementById("tip");
let summary = null;
const cache = {};

const pad = (n) => String(n).padStart(2, "0");
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (x, d = 1) => (100 * x).toFixed(d).replace(".", ",") + "%";
const num = (x) => x.toLocaleString("vi-VN");
const pyToJs = (w) => (w + 1) % 7; // Python: 0 = thứ 2; JS: 0 = chủ nhật

function todayVN() {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh" }).format(new Date());
}
function dow(iso) { return new Date(iso + "T00:00:00Z").getUTCDay(); }
function fmtDate(iso, withDay = true) {
  const [y, m, d] = iso.split("-");
  return (withDay ? DAYS[dow(iso)] + " " : "") + `${d}/${m}/${y}`;
}

async function getJSON(url) {
  if (!cache[url]) cache[url] = fetch(url, { cache: "no-cache" }).then((r) => {
    if (!r.ok) throw new Error(r.status + " " + url);
    return r.json();
  });
  return cache[url];
}

const chips = (arr, actual, cls = "") =>
  `<span class="chips">${arr.map((n) => `<span class="chip ${cls} ${n === actual ? "hit" : ""}">${pad(n)}</span>`).join("")}</span>`;

function bars(hits, tested, k) {
  const exp = k / 100;
  const max = Math.max(exp, ...STRATS.map(([s]) => hits[s] / tested)) * 1.25;
  const rows = STRATS.map(([s, name]) => {
    const r = hits[s] / tested;
    return `<div class="bar" title="${name}: trúng ${num(hits[s])}/${num(tested)} kỳ">
      <span class="name">${name}</span>
      <span class="track"><span class="fill" style="width:${(100 * r) / max}%"></span>
        <span class="ref" style="left:${(100 * exp) / max}%"></span></span>
      <span class="val">${pct(r)}</span></div>`;
  }).join("");
  return `<div class="bars">${rows}</div>
    <div class="ref-label">Vạch đứt = ${k}% (chọn bừa ${k} số / 100)</div>`;
}

function card(s) {
  const sg = s.suggest;
  const when = s.next ? (s.next === todayVN() ? "Hôm nay" : fmtDate(s.next)) : "Tạm ngừng";
  return `<article class="card">
    <div class="card-head"><h3>${esc(s.name)}</h3><span class="when">Kỳ tới: ${when}</span></div>
    <div class="last">Kỳ trước (${fmtDate(s.last, false)}): G8 <b>${esc(s.last_g8)}</b> · ĐB <b>${esc(s.last_db || "—")}</b></div>
    <div class="row"><span class="lbl">G8 số nóng</span>${chips(sg.hot)}</div>
    <div class="row"><span class="lbl">G8 lô gan</span>${chips(sg.gan)}</div>
    <div class="row"><span class="lbl">G8 ngẫu nhiên</span>${chips(sg.random)}</div>
    <div class="row"><span class="lbl">Đặc biệt</span><span class="chips">
      ${sg.db_digits ? `<span class="chip big" title="Chữ số về nhiều nhất ở từng vị trí">${sg.db_digits}</span>` : ""}
      ${sg.db_random ? `<span class="chip big" title="Số ngẫu nhiên">${sg.db_random}</span>` : ""}</span></div>
    <div class="card-foot"><span class="muted">Số nóng từng trúng ${pct(s.hits.hot / s.tested)} / ${num(s.tested)} kỳ</span>
      <a href="#/dai/${s.slug}">Chi tiết →</a></div>
  </article>`;
}

function renderHome(day) {
  const today = todayVN();
  if (day == null) day = dow(today);
  const list = summary.stations
    .filter((s) => s.active && s.weekdays.map(pyToJs).includes(day))
    .sort((a, b) => a.name.localeCompare(b.name, "vi"));
  const t = summary.tested, h = summary.hits;
  app.innerHTML = `
    <h1>${day === dow(today) ? "Hôm nay, " + fmtDate(today) : DAYS[day]}</h1>
    <p class="sub">Số tham khảo giải 8 và giải đặc biệt cho kỳ quay tới của từng đài.</p>
    <div class="notice">Kết quả xổ số là <b>ngẫu nhiên</b>. Khi thử lại trên <b>${num(t)}</b> kỳ của
      ${summary.stations.length} đài, bộ ${summary.k} số "nóng" trúng giải 8 <b>${pct(h.hot / t)}</b>, lô gan
      <b>${pct(h.gan / t)}</b>, chọn ngẫu nhiên <b>${pct(h.random / t)}</b> — đều quanh mức may rủi
      <b>${summary.k}%</b>. Không có cách chọn nào tốt hơn. Đặc biệt: 1/1.000.000 cho mọi số.</div>
    <nav class="days" aria-label="Chọn ngày">${SHORT.map((d, i) =>
      `<button type="button" data-day="${i}" aria-pressed="${i === day}">${d}${i === dow(today) ? " · hôm nay" : ""}</button>`).join("")}</nav>
    <div class="grid">${list.map(card).join("") || '<p class="muted">Không có đài nào quay ngày này.</p>'}</div>
    <h2>Tỉ lệ trúng giải 8 thực tế (toàn bộ đài)</h2>
    <p class="sub">Mỗi kỳ trong quá khứ, chọn ${summary.k} số chỉ dựa trên dữ liệu trước kỳ đó, rồi đối chiếu kết quả thật.</p>
    <div class="card">${bars(h, t, summary.k)}</div>
    <h2>Tất cả các đài</h2>
    <div class="card scroll"><table>
      <thead><tr><th>Đài</th><th>Ngày quay</th><th>Số kỳ</th><th>Từ</th><th>Kỳ gần nhất</th></tr></thead>
      <tbody>${[...summary.stations].sort((a, b) => a.name.localeCompare(b.name, "vi")).map((s) =>
        `<tr><td><a href="#/dai/${s.slug}">${esc(s.name)}</a></td>
        <td>${s.active ? s.weekdays.map((w) => SHORT[pyToJs(w)]).join(", ") : "Tạm ngừng"}</td>
        <td>${num(s.count)}</td><td>${fmtDate(s.first, false)}</td><td>${fmtDate(s.last, false)}</td></tr>`).join("")}
      </tbody></table></div>`;
  app.querySelectorAll(".days button").forEach((b) =>
    b.addEventListener("click", () => { location.hash = "#/ngay/" + b.dataset.day; }));
}

function darkMode() {
  const t = document.documentElement.dataset.theme;
  return t === "dark" || (t !== "light" && matchMedia("(prefers-color-scheme: dark)").matches);
}
// Thang 7 bậc một màu xanh. Ở chế độ tối thang đảo chiều sáng, nên màu chữ cũng đổi theo.
function shade(v, max) {
  const i = Math.min(6, Math.floor((v / (max || 1)) * 7));
  const light = darkMode() ? i >= 4 : i < 4;
  return { bg: `var(--s${i + 1}00)`, fg: light ? "#0b0b0b" : "#ffffff" };
}

function heatmap(freq, gap, count) {
  const max = Math.max(...freq);
  let html = `<div class="heat" role="grid" aria-label="Tần suất giải 8 theo số"><span></span>`;
  for (let c = 0; c < 10; c++) html += `<span class="ax">${c}</span>`;
  for (let r = 0; r < 10; r++) {
    html += `<span class="ax">${r}</span>`;
    for (let c = 0; c < 10; c++) {
      const n = r * 10 + c;
      const { bg, fg } = shade(freq[n], max);
      html += `<button class="cell" style="background:${bg};color:${fg}"
        data-tip="<b>${pad(n)}</b>: về ${freq[n]} lần (${pct(freq[n] / count, 2)})<br>Chưa về ${gap[n]} kỳ"
        aria-label="${pad(n)}: ${freq[n]} lần">${pad(n)}</button>`;
    }
  }
  html += `</div><div class="scale"><span>Ít</span>${["--s100", "--s200", "--s300", "--s400", "--s500", "--s600", "--s700"]
    .map((s) => `<span class="sw" style="background:var(${s})"></span>`).join("")}<span>Nhiều (tối đa ${max} lần)</span></div>`;
  return html;
}

async function renderStation(slug) {
  const d = await getJSON(`data/st/${slug}.json`);
  const sg = d.suggest, tr = d.track;
  const exp = d.count / 100;
  const ganTop = d.g8.gap.map((g, n) => [n, g]).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const freqTop = d.g8.freq.map((f, n) => [n, f]).sort((a, b) => b[1] - a[1]).slice(0, 10);
  app.innerHTML = `
    <p><a href="#/">← Tất cả đài</a></p>
    <h1>Xổ số ${esc(d.name)}</h1>
    <p class="sub">${num(d.count)} kỳ từ ${fmtDate(d.first, false)} đến ${fmtDate(d.last, false)} ·
      Quay ${d.weekdays.map((w) => DAYS[pyToJs(w)].toLowerCase()).join(", ")} hằng tuần</p>

    <div class="two">
      <section class="card">
        <div class="card-head"><h3>Kết quả</h3>
          <select id="pick" aria-label="Chọn kỳ">${d.latest.map((r, i) =>
            `<option value="${i}">${fmtDate(r.date)}</option>`).join("")}</select></div>
        <div id="result"></div>
      </section>
      <section class="card">
        <div class="card-head"><h3>Số tham khảo</h3><span class="when">${sg.for ? "Kỳ " + fmtDate(sg.for) : "Đài tạm ngừng"}</span></div>
        <div class="row"><span class="lbl">G8 số nóng</span>${chips(sg.hot)}</div>
        <div class="row"><span class="lbl">G8 lô gan</span>${chips(sg.gan)}</div>
        <div class="row"><span class="lbl">G8 ngẫu nhiên</span>${chips(sg.random)}</div>
        <div class="row"><span class="lbl">Đặc biệt</span><span class="chips">
          ${sg.db_digits ? `<span class="chip big">${sg.db_digits}</span>` : ""}
          ${sg.db_random ? `<span class="chip big">${sg.db_random}</span>` : ""}</span></div>
        <p class="muted" style="font-size:13px;margin:10px 0 0">Số nóng: về nhiều nhất từ trước tới nay. Lô gan: lâu chưa về nhất.
          Ngẫu nhiên: rút thăm. ĐB: chữ số hay về nhất ở từng vị trí, và một số rút thăm.
          Mỗi bộ ${summary.k} số có ${summary.k}% cơ hội trúng giải 8 — như nhau.</p>
      </section>
    </div>

    <h2>Gợi ý đã trúng bao nhiêu?</h2>
    <p class="sub">Thử lại trên ${num(tr.tested)} kỳ của đài này, mỗi kỳ chỉ dùng dữ liệu trước đó.</p>
    <div class="card">${bars(tr.hits, tr.tested, summary.k)}</div>
    <div class="card scroll" style="margin-top:12px"><table>
      <thead><tr><th>Kỳ</th><th>G8 về</th><th>Số nóng</th><th>Lô gan</th><th>Ngẫu nhiên</th></tr></thead>
      <tbody>${tr.recent.map((r) => `<tr><td>${fmtDate(r.date, false)}</td><td><b>${pad(r.actual)}</b></td>
        <td>${chips(r.hot, r.actual)}</td><td>${chips(r.gan, r.actual)}</td><td>${chips(r.random, r.actual)}</td></tr>`).join("")}</tbody>
    </table></div>

    <h2>Tần suất giải 8 (00–99)</h2>
    <p class="sub">Hàng = chữ số đầu, cột = chữ số đuôi. Trung bình mỗi số về ${exp.toFixed(1).replace(".", ",")} lần.
      Kiểm định phân bố đều: p = ${String(d.g8.p).replace(".", ",")} ${d.g8.p > 0.05 ? "— chênh lệch chỉ là may rủi." : "— hơi lệch, nhưng cần xem cùng kết quả thử lại ở trên."}</p>
    <div class="two">
      <div class="card">${heatmap(d.g8.freq, d.g8.gap, d.count)}</div>
      <div class="card scroll"><table>
        <thead><tr><th>Về nhiều nhất</th><th>Lần</th><th>Lô gan</th><th>Chưa về</th><th>Kỷ lục</th></tr></thead>
        <tbody>${freqTop.map(([n, f], i) => `<tr><td><b>${pad(n)}</b></td><td>${f}</td>
          <td><b>${pad(ganTop[i][0])}</b></td><td>${ganTop[i][1]} kỳ</td><td>${d.g8.maxgap[ganTop[i][0]]} kỳ</td></tr>`).join("")}</tbody>
      </table></div>
    </div>

    <h2>Giải đặc biệt</h2>
    <p class="sub">${num(d.db.count6)} kỳ có số 6 chữ số. Số lần mỗi chữ số xuất hiện ở từng vị trí.</p>
    <div class="two">
      <div class="card scroll"><table>
        <thead><tr><th>Vị trí</th>${[...Array(10).keys()].map((i) => `<th>${i}</th>`).join("")}<th>p</th></tr></thead>
        <tbody>${d.db.pos.map((row, p) => `<tr><td>${p + 1}</td>${row.map((v, dg) => {
          const s = shade(v - Math.min(...row), Math.max(...row) - Math.min(...row));
          return `<td><span class="cell" style="background:${s.bg};color:${s.fg};aspect-ratio:auto;padding:2px 4px"
            data-tip="Vị trí ${p + 1}, chữ số ${dg}: ${v} lần">${v}</span></td>`;
        }).join("")}<td>${String(d.db.pos_p[p]).replace(".", ",")}</td></tr>`).join("")}</tbody>
      </table></div>
      <div class="card"><h3 style="margin-bottom:8px">2 số cuối ĐB về nhiều nhất</h3>
        <span class="chips">${d.db.tail_top.map(([n, c]) => `<span class="chip" title="${c} lần">${pad(n)} · ${c}</span>`).join("")}</span>
      </div>
    </div>`;
  const pick = document.getElementById("pick");
  const show = () => {
    const r = d.latest[pick.value];
    document.getElementById("result").innerHTML = `<table class="result"><tbody>${PRIZES.map(([k, name]) =>
      `<tr class="${k.toLowerCase()}"><td>${name}</td><td>${esc(r[k] || "—").split(" ").join(" &nbsp; ")}</td></tr>`).join("")}</tbody></table>`;
  };
  pick.addEventListener("change", show);
  show();
}

// Tooltip dùng chung cho ô bản đồ nhiệt
document.addEventListener("pointerover", (e) => {
  const el = e.target.closest("[data-tip]");
  if (!el) { tip.hidden = true; return; }
  tip.innerHTML = el.dataset.tip;
  tip.hidden = false;
  const r = el.getBoundingClientRect();
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + "px";
  tip.style.top = (r.top - h - 8 < 8 ? r.bottom + 8 : r.top - h - 8) + "px";
});
document.addEventListener("focusin", (e) => { if (e.target.dataset && e.target.dataset.tip) e.target.dispatchEvent(new Event("pointerover", { bubbles: true })); });
addEventListener("scroll", () => { tip.hidden = true; }, { passive: true });

async function route() {
  tip.hidden = true;
  try {
    if (!summary) {
      summary = await getJSON("data/summary.json");
      const u = new Date(summary.updated);
      document.getElementById("updated").textContent = "Cập nhật " +
        u.toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh", dateStyle: "short", timeStyle: "short" });
    }
    const m = location.hash.match(/^#\/(dai|ngay)\/([\w-]+)/);
    if (m && m[1] === "dai") await renderStation(m[2]);
    else renderHome(m ? Number(m[2]) % 7 : null);
    scrollTo(0, 0);
  } catch (err) {
    app.innerHTML = `<p class="muted">Không tải được dữ liệu (${esc(err.message)}).</p>`;
  }
}
addEventListener("hashchange", route);
route();
