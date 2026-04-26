/**
 * 首页：全站摘要 + 试探测 + Uptime 风格条 + 矩阵 + Chart
 * 排行页：轮询 dashboard
 */
(function () {
  const MODEL_SLUGS = [
    "opus-47",
    "opus-46",
    "sonnet-46",
    "gpt-5-5",
    "gpt-5-4",
    "gemini-3-1",
  ];
  const LS_LAT = "zhongce_probe_lat_v1";
  const chartState = { bar: null, doughnut: null, line: null };

  function setText(id, t) {
    const el = document.getElementById(id);
    if (el) el.textContent = t;
  }

  function fmtTime(iso) {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  }

  function buildUptimeBarHost() {
    const host = document.getElementById("kuma-uptime-bars");
    if (!host || host.children.length) return;
    for (var i = 0; i < 12; i++) {
      var b = document.createElement("span");
      b.className = "kuma-uptime-seg";
      b.setAttribute("data-i", String(i));
      host.appendChild(b);
    }
  }

  var barTick = 0;
  function tickUptimeBar(ok) {
    buildUptimeBarHost();
    const host = document.getElementById("kuma-uptime-bars");
    if (!host) return;
    var segs = host.querySelectorAll(".kuma-uptime-seg");
    if (!segs.length) return;
    segs[barTick % 12].className =
      "kuma-uptime-seg " + (ok ? "seg-ok" : "seg-bad");
    barTick++;
  }

  function el(tag, cls, text) {
    const x = document.createElement(tag);
    if (cls) x.className = cls;
    if (text != null) x.textContent = text;
    return x;
  }

  function initMatrix() {
    const tb = document.getElementById("matrix-tbody");
    const th = document.getElementById("matrix-thead");
    if (!tb || !th) return;
    var poll = function () {
      fetch("/api/relay-matrix")
        .then(function (r) {
          return r.json();
        })
        .then(function (d) {
          setText("matrix-updated", fmtTime(d.updated_at));
          th.textContent = "";
          tb.textContent = "";
          const htr = el("tr");
          htr.appendChild(el("th", "th-site", "站点"));
          (d.models_meta || []).forEach(function (m) {
            var short = m.name_zh || m.slug;
            if (short.length > 7) short = short.slice(0, 6) + "…";
            htr.appendChild(el("th", "th-matrix", short));
          });
          htr.appendChild(el("th", "th-base", "Base"));
          th.appendChild(htr);
          const rows = d.rows || [];
          if (!rows.length) {
            var tr0 = el("tr");
            var td0 = el("td", "muted", "暂无已收录站点，请用 seed 或管理接口添加");
            td0.colSpan = (d.models_meta || []).length + 2;
            tr0.appendChild(td0);
            tb.appendChild(tr0);
            return;
          }
          rows.forEach(function (row) {
            var tr = el("tr", "row-flash");
            tr.appendChild(el("td", "td-mat-name", row.name));
            (d.models_meta || []).forEach(function (m) {
              var cell = row.by_slug && row.by_slug[m.slug];
              var txt = "—";
              if (cell && cell.samples) {
                txt =
                  typeof cell.online_rate_pct === "number"
                    ? cell.online_rate_pct + "%"
                    : String(cell.status || "—");
              } else if (cell && cell.status) {
                txt = cell.status;
              }
              tr.appendChild(el("td", "td-mat " + (cell && cell.status_class ? cell.status_class : ""), txt));
            });
            var tdb = el("td", "url");
            tdb.appendChild(el("small", null, row.base_url));
            tr.appendChild(tdb);
            tb.appendChild(tr);
          });
        })
        .catch(function () {});
    };
    poll();
    setInterval(poll, 15000);
  }

  // —— 首页：home-stats
  function initHomeBroadcast() {
    const root = document.getElementById("home-page-root");
    if (!root) return;
    const poll = function () {
      fetch("/api/home-stats")
        .then((r) => r.json())
        .then((d) => {
          setText("home-stat-enabled", String(d.relays_enabled ?? 0));
          setText("home-stat-samples", String(d.probe_samples_in_window ?? 0));
          if (d.window_hours != null) setText("home-stat-window", String(d.window_hours));
          setText("home-stat-time", fmtTime(d.updated_at));
          tickUptimeBar(true);
          const leg = d.legacy_top || [];
          const tb = document.getElementById("home-live-tbody");
          if (tb) {
            tb.textContent = "";
            if (leg.length === 0) {
              const tr = document.createElement("tr");
              tr.innerHTML = '<td colspan="4" class="muted">—</td>';
              tb.appendChild(tr);
            } else {
              leg.slice(0, 8).forEach((x) => {
                const tr = document.createElement("tr");
                tr.className = "row-flash";
                const ok = x.samples_in_window
                  ? (Math.round(x.success_rate * 1000) / 10).toFixed(1) + "%"
                  : "—";
                const lat =
                  x.avg_latency_ms != null ? String(x.avg_latency_ms) : "—";
                tr.innerHTML =
                  "<td class=\"td-rank\"><span class=\"rank-pill\">#" +
                  x.rank +
                  "</span></td>" +
                  '<td class="td-name"></td><td class="td-metric">' +
                  ok +
                  '</td><td class="td-metric td-lat">' +
                  lat +
                  "</td>";
                tr.querySelector(".td-name").textContent = x.name || "—";
                tb.appendChild(tr);
              });
            }
          }
        })
        .catch(function () {
          tickUptimeBar(false);
        });
    };
    buildUptimeBarHost();
    poll();
    setInterval(poll, 10000);
  }

  function pushLat(lat) {
    if (lat == null || isNaN(lat)) return;
    try {
      var arr = JSON.parse(sessionStorage.getItem(LS_LAT) || "[]");
      if (!Array.isArray(arr)) arr = [];
      arr.push(Number(lat));
      while (arr.length > 12) arr.shift();
      sessionStorage.setItem(LS_LAT, JSON.stringify(arr));
      return arr;
    } catch (e) {
      return [Number(lat)];
    }
  }

  function renderProbeCharts(j) {
    if (typeof Chart === "undefined") return;
    const svc = j.service_status || {};
    const det = svc.model_detail || [];
    const labels = det.map(function (m) { return m.name_zh || m.slug; });
    const present = det.map(function (m) { return m.present ? 1 : 0; });
    const elBar = document.getElementById("chart-models-h");
    const elD = document.getElementById("chart-hit-d");
    const elL = document.getElementById("chart-lat-line");
    if (!elBar || !elD || !elL) return;
    if (chartState.bar) {
      chartState.bar.destroy();
      chartState.doughnut.destroy();
      if (chartState.line) chartState.line.destroy();
    }
    const dark = document.getElementById("html-root").getAttribute("data-theme") === "dark";
    const fg = dark ? "#e4e4e7" : "#18181b";
    const grid = dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)";

    chartState.bar = new Chart(elBar, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "匹配",
            data: present,
            backgroundColor: present.map(function (p) { return p ? "rgba(52, 211, 153, 0.8)" : "rgba(113, 113, 122, 0.5)"; }),
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { x: { min: 0, max: 1, grid: { color: grid }, ticks: { color: fg } }, y: { grid: { display: false }, ticks: { color: fg, font: { size: 10 } } } },
      },
    });
    const hits = svc.model_hits != null ? svc.model_hits : 0;
    const tot = svc.model_tracked != null ? svc.model_tracked : 6;
    chartState.doughnut = new Chart(elD, {
      type: "doughnut",
      data: {
        labels: ["命中", "未命中"],
        datasets: [
          {
            data: [hits, Math.max(0, tot - hits)],
            backgroundColor: ["#34d399", "#52525b"],
          },
        ],
      },
      options: { plugins: { legend: { labels: { color: fg } } } },
    });
    const hist = pushLat(j.latency_ms);
    chartState.line = new Chart(elL, {
      type: "line",
      data: {
        labels: (hist || []).map(function (_x, i) { return String(i + 1); }),
        datasets: [
          {
            label: "ms",
            data: hist || [j.latency_ms],
            borderColor: "#a78bfa",
            backgroundColor: "rgba(167, 139, 250, 0.1)",
            fill: true,
            tension: 0.2,
          },
        ],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { x: { grid: { color: grid }, ticks: { color: fg } }, y: { grid: { color: grid }, ticks: { color: fg } } },
      },
    });
  }

  // —— 首页：试探测
  function initHomeProbe() {
    const f = document.getElementById("form-try-probe");
    const out = document.getElementById("probe-result");
    const pill = document.getElementById("probe-kuma-pill");
    const pv = document.getElementById("probe-viz");
    if (!f || !out) return;
    f.addEventListener("submit", (e) => {
      e.preventDefault();
      out.hidden = false;
      if (pv) pv.hidden = true;
      if (pill) pill.hidden = true;
      out.textContent = "…";
      out.className = "probe-result loading";
      const fd = new FormData(f);
      fetch("/api/try-probe", { method: "POST", body: fd })
        .then((r) => r.json().then((j) => ({ ok: r.ok, j })))
        .then(({ ok, j }) => {
          out.className = "probe-result";
          if (!ok) {
            out.textContent = j.detail || JSON.stringify(j);
            return;
          }
          const svc = j.service_status || {};
          if (pill) {
            pill.hidden = false;
            setText("probe-svc-emoji", svc.status_emoji || "—");
            setText("probe-svc-time", fmtTime(j.checked_at));
            var line = "状态 " + (svc.status || "—");
            if (j.http_status != null) line += " · HTTP " + j.http_status;
            if (j.latency_ms != null) line += " · " + j.latency_ms + " ms";
            if (svc.model_hits != null) line += " · 六线 " + svc.model_hits + "/" + (svc.model_tracked || 6);
            setText("probe-svc-line", line);
            pill.className = "probe-kuma-pill kuma-" + (svc.status || "down");
          }
          const ms = j.model_matches || {};
          const parts = [];
          parts.push("HTTP " + (j.http_status != null ? j.http_status : "—"));
          parts.push("延迟 " + (j.latency_ms != null ? j.latency_ms + " ms" : "—"));
          const labels = {
            "opus-47": "Opus 4.7",
            "opus-46": "Opus 4.6",
            "sonnet-46": "Sonnet 4.6",
            "gpt-5-5": "GPT 5.5",
            "gpt-5-4": "GPT 5.4",
            "gemini-3-1": "Gemini 3.1 Pro",
          };
          const chips = Object.keys(labels)
            .map((slug) => {
              const hit = ms[slug] ? "hit" : "miss";
              return (
                '<span class="probe-chip ' +
                hit +
                '"><span class="n">' +
                labels[slug] +
                "</span> " +
                (ms[slug] ? "✓" : "×") +
                "</span>"
              );
            })
            .join(" ");
          out.innerHTML =
            "<p><strong>结果</strong>：" +
            (j.ok ? "请求已返回" : "请求未成功") +
            " · " +
            parts.join(" · ") +
            "</p>" +
            (j.error ? "<p class=\"err\">" + j.error + "</p>" : "") +
            "<div class=\"probe-chips\">" +
            chips +
            "</div>";
          if (pv) {
            pv.hidden = false;
            requestAnimationFrame(function () {
              renderProbeCharts(j);
            });
          }
        })
        .catch((err) => {
          out.className = "probe-result err";
          out.textContent = String(err);
        });
    });
  }

  function renderModelRows(tbody, rows) {
    tbody.textContent = "";
    if (!rows || rows.length === 0) {
      const tr = el("tr");
      tr.appendChild(
        (function () {
          const td = el("td", "muted", "暂无数据");
          td.colSpan = 9;
          return td;
        })()
      );
      tbody.appendChild(tr);
      return;
    }
    rows.forEach((row) => {
      const tr = el("tr", "row-flash");
      tr.appendChild(
        (function () {
          const td = el("td", "td-rank");
          const s = el("span", "rank-pill", "#" + row.rank);
          td.appendChild(s);
          return td;
        })()
      );
      const tdN = el("td", "td-name", row.name);
      tr.appendChild(tdN);
      tr.appendChild(el("td", null, row.group || "—"));
      tr.appendChild(el("td", "td-price", String(row.price || "—")));
      const online =
        row.samples && typeof row.online_rate_pct === "number"
          ? row.online_rate_pct + "%"
          : "—";
      tr.appendChild(el("td", "td-metric", online));
      tr.appendChild(el("td", "td-metric td-dilu", String(row.dilution || "—")));
      const lat = row.avg_latency_ms != null ? String(row.avg_latency_ms) : "—";
      tr.appendChild(el("td", "td-metric td-lat", lat));
      const tdSt = el("td");
      const b = el("span", "run-badge " + (row.status_class || "st-muted"), row.status);
      tdSt.appendChild(b);
      tr.appendChild(tdSt);
      const tdU = el("td", "url");
      const sm = el("small", null, row.base_url);
      tdU.appendChild(sm);
      tr.appendChild(tdU);
      tbody.appendChild(tr);
    });
  }

  function renderLegacyRows(tbody, rows) {
    tbody.textContent = "";
    if (!rows || rows.length === 0) return;
    rows.forEach((x) => {
      const tr = el("tr", "row-flash");
      tr.appendChild(
        (function () {
          const td = el("td", "td-rank");
          td.appendChild(el("span", "rank-pill", "#" + x.rank));
          return td;
        })()
      );
      tr.appendChild(el("td", "td-name", x.name));
      const rate =
        x.samples_in_window && x.success_rate != null
          ? (Math.round(x.success_rate * 1000) / 10).toFixed(1) + "%"
          : "—";
      tr.appendChild(el("td", "td-metric", rate));
      const lat = x.avg_latency_ms != null ? String(x.avg_latency_ms) : "—";
      tr.appendChild(el("td", "td-metric td-lat", lat));
      const tdu = el("td", "url");
      tdu.appendChild(el("small", null, x.base_url));
      tr.appendChild(tdu);
      tbody.appendChild(tr);
    });
  }

  function initRankPoll() {
    const root = document.getElementById("rank-page-root");
    if (!root) return;
    const w = root.getAttribute("data-window-hours") || "24";
    const sec = parseInt(root.getAttribute("data-poll-sec") || "8", 10) * 1000;
    const poll = () => {
      fetch("/api/dashboard?window_hours=" + encodeURIComponent(w))
        .then((r) => r.json())
        .then((d) => {
          setText("rank-stat-updated", fmtTime(d.updated_at));
          const meta = d.models_meta;
          (meta && meta.length ? meta : MODEL_SLUGS.map((s) => ({ slug: s }))).forEach(
            (m) => {
              const slug = m.slug;
              const tb = document.getElementById("tb-model-" + slug);
              if (tb) renderModelRows(tb, d.by_model && d.by_model[slug]);
            }
          );
          const tbleg = document.getElementById("tb-legacy");
          if (tbleg) renderLegacyRows(tbleg, d.legacy);
        })
        .catch(() => {});
    };
    poll();
    setInterval(poll, sec);
  }

  function initInclusion() {
    const f = document.getElementById("f-inc");
    if (!f) return;
    f.addEventListener("submit", async (e) => {
      e.preventDefault();
      const imsg = document.getElementById("imsg");
      const r = await fetch("/api/inclusion", {
        method: "POST",
        body: new FormData(f),
      });
      if (r.ok) {
        if (imsg) imsg.textContent = "已提交，ID " + (await r.json()).id;
        f.reset();
      } else if (imsg) imsg.textContent = await r.text();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", go);
  } else {
    go();
  }

  function go() {
    initHomeBroadcast();
    initHomeProbe();
    initMatrix();
    initRankPoll();
    initInclusion();
  }
})();
