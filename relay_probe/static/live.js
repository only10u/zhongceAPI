/**
 * 首页：全站摘要 + 试探测 + Uptime 风格条 + 矩阵 + Chart
 * 排行页：轮询 dashboard
 */
(function () {
  const MODEL_SLUGS = ["opus-47", "opus-46", "sonnet-46"];
  const LS_LAT = "zhongce_probe_lat_v1";
  const chartState = { bar: null, doughnut: null, line: null };
  var lastProbeSnapshot = null;

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
          htr.appendChild(el("th", "th-site", "名称"));
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
            const td0 = el("td", "td-mat-name");
            if (row.base_url) {
              var axm = document.createElement("a");
              axm.className = "site-link";
              axm.href = row.base_url;
              axm.target = "_blank";
              axm.rel = "noopener noreferrer";
              axm.textContent = row.name;
              td0.appendChild(axm);
            } else {
              td0.textContent = row.name;
            }
            tr.appendChild(td0);
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
                  '</span></td><td class="td-name"></td><td class="td-metric">' +
                  ok +
                  '</td><td class="td-metric td-lat">' +
                  lat +
                  "</td>";
                var tdn = tr.querySelector(".td-name");
                if (x.base_url) {
                  var an = document.createElement("a");
                  an.className = "site-link";
                  an.href = x.base_url;
                  an.target = "_blank";
                  an.rel = "noopener noreferrer";
                  an.textContent = x.name || "—";
                  tdn.appendChild(an);
                } else {
                  tdn.textContent = x.name || "—";
                }
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
    var selslug = (svc && svc.selected_slug) || "opus-47";
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
            backgroundColor: det.map(function (m, i) {
              var p = present[i];
              var isSel = m.slug === selslug;
              if (isSel) return p ? "#34d399" : "rgba(251, 191, 36, 0.85)";
              return p ? "rgba(52, 211, 153, 0.55)" : "rgba(113, 113, 122, 0.45)";
            }),
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
    const tot = svc.model_tracked != null ? svc.model_tracked : 3;
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

  function isZhRoot() {
    const r = document.getElementById("html-root");
    return (r && r.getAttribute("lang") || "").toLowerCase().startsWith("zh");
  }

  function metricNaLabel() {
    return isZhRoot() ? "不适用" : "N/A";
  }

  function renderHomeProbeReport(j) {
    const dump = document.getElementById("probe-report-dump");
    if (!dump) return;
    dump.hidden = false;
    const ru = j.report_ui || {};
    const p = Math.max(0, Math.min(100, parseInt(String(ru.score_percent), 10) || 0));
    const ring = document.getElementById("home-score-ring");
    if (ring) ring.style.setProperty("--p", String(p));
    setText("home-score-pct", p + "%");
    setText("home-score-hl-zh", ru.headline_zh || "—");
    const hel = document.getElementById("home-score-hl-en");
    if (hel) hel.textContent = ru.headline_en || "—";
    setText("m-v-lat", j.latency_ms != null ? String(j.latency_ms) : "—");
    const na = metricNaLabel();
    const ch = j.chat_usage || {};
    const up = ch.usage_parsed === true;
    const fmtInt = (n) => (n == null || Number.isNaN(n) ? na : String(Math.trunc(n)));
    const tps = document.getElementById("m-v-tps");
    const tIn = document.getElementById("m-v-tin");
    const tOut = document.getElementById("m-v-tout");
    const tCr = document.getElementById("m-v-tcr");
    const tCw = document.getElementById("m-v-tcw");
    if (tps) tps.textContent = up && ch.tokens_per_sec != null ? String(ch.tokens_per_sec) : na;
    if (tIn) tIn.textContent = up ? fmtInt(ch.prompt_tokens) : na;
    if (tOut) tOut.textContent = up ? fmtInt(ch.completion_tokens) : na;
    if (tCr) tCr.textContent = up ? fmtInt(ch.cache_read) : na;
    if (tCw) tCw.textContent = up ? fmtInt(ch.cache_write) : na;
    [tps, tIn, tOut, tCr, tCw].forEach((el) => {
      if (el) el.classList.toggle("pm-tok-na", !up);
    });
    const nZh = document.getElementById("probe-metric-note-zh");
    const nEn = document.getElementById("probe-metric-note-en");
    if (nZh && nEn) {
      if (ch.skipped) {
        nZh.textContent = "未填写 API Key，仅发起 GET /v1/models，不拉对话 Token 用量。填写 Key 后会额外 POST 一次 /v1/chat/completions 解析 usage。";
        nEn.textContent = "No API key: only GET /v1/models. Add a key to also POST /v1/chat/completions and read usage.";
      } else if (up) {
        nZh.textContent =
          "已使用所选主评线的 model id 实连 " +
          (ch.model_id_used || "") +
          " 并解析返回中的 usage。延迟 (ms) 为目录请求；对话为独立一次请求。深度项本页未检。";
        nEn.textContent = "Token figures come from one non-streaming chat completion. Latency is the models list request. Deep checks not on this page.";
      } else {
        nZh.textContent = "未解析到有效 Token 数据：" + (ch.error || "失败") + "。可确认 model id 在网关中可用。目录延迟仍见左栏。";
        nEn.textContent = "No usage parsed: " + (ch.error || "failed");
      }
    }
    const cl = document.getElementById("home-probe-checklist");
    if (cl) {
      cl.textContent = "";
      (ru.checklist || []).forEach(function (row) {
        const li = el("li", "ck ck-" + (row.state || "skip"));
        var ico = "—";
        if (row.state === "pass") ico = "✓";
        else if (row.state === "warn") ico = "△";
        else if (row.state === "fail") ico = "✗";
        li.appendChild(el("span", "ck-ico", ico));
        const tw = el("div", "ck-twrap");
        tw.appendChild(el("span", "ck-t i18n-zh", row.text_zh || ""));
        tw.appendChild(el("span", "ck-t i18n-en", row.text_en || ""));
        li.appendChild(tw);
        cl.appendChild(li);
      });
    }
    lastProbeSnapshot = j;
  }

  function initProbeShare() {
    const b = document.getElementById("btn-probe-share");
    if (!b || b.getAttribute("data-wired") === "1") return;
    b.setAttribute("data-wired", "1");
    b.addEventListener("click", function () {
      const toast = document.getElementById("probe-share-toast");
      if (!lastProbeSnapshot) {
        if (toast) {
          toast.textContent = isZhRoot() ? "请先完成一次检测" : "Run a probe first";
          toast.hidden = false;
        }
        return;
      }
      if (toast) toast.hidden = true;
      fetch("/api/probe-reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version: 1, data: lastProbeSnapshot }),
        credentials: "same-origin",
      })
        .then((r) => r.json().then((j) => ({ ok: r.ok, j })))
        .then(function ({ ok, j }) {
          if (ok && j.url) {
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(j.url);
            } else {
              const ta = document.createElement("textarea");
              ta.value = j.url;
              document.body.appendChild(ta);
              ta.select();
              try {
                document.execCommand("copy");
              } catch (ex) {}
              document.body.removeChild(ta);
            }
            if (toast) {
              toast.textContent = (isZhRoot() ? "已复制报告链接： " : "Copied: ") + j.url;
              toast.hidden = false;
            }
          } else if (toast) {
            toast.textContent = (j && j.detail) || String(j) || "error";
            toast.hidden = false;
          }
        })
        .catch(function (e) {
          if (toast) {
            toast.textContent = String(e);
            toast.hidden = false;
          }
        });
    });
  }

  // —— 首页：试探测
  function initHomeProbe() {
    const f = document.getElementById("form-try-probe");
    const out = document.getElementById("probe-result");
    const dump = document.getElementById("probe-report-dump");
    const pill = document.getElementById("probe-kuma-pill");
    const pv = document.getElementById("probe-viz");
    if (!f || !out) return;
    f.addEventListener("submit", (e) => {
      e.preventDefault();
      if (dump) dump.hidden = true;
      const tst = document.getElementById("probe-share-toast");
      if (tst) {
        tst.hidden = true;
        tst.textContent = "";
      }
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
            if (dump) dump.hidden = true;
            out.textContent = j.detail || JSON.stringify(j);
            return;
          }
          out.hidden = true;
          out.textContent = "";
          const svc = j.service_status || {};
          if (pill) {
            pill.hidden = false;
            setText("probe-svc-emoji", svc.status_emoji || "—");
            setText("probe-svc-time", fmtTime(j.checked_at));
            var line = "状态 " + (svc.status || "—");
            if (j.http_status != null) line += " · HTTP " + j.http_status;
            if (j.latency_ms != null) line += " · " + j.latency_ms + " ms";
            if (svc.model_hits != null) line += " · 三线 " + svc.model_hits + "/" + (svc.model_tracked || 3);
            setText("probe-svc-line", line);
            pill.className = "probe-kuma-pill kuma-" + (svc.status || "down");
          }
          renderHomeProbeReport(j);
          if (pv) {
            pv.hidden = false;
            requestAnimationFrame(function () {
              renderProbeCharts(j);
            });
          }
        })
        .catch((err) => {
          if (dump) dump.hidden = true;
          out.hidden = false;
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
          td.colSpan = 8;
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
      const tdN = el("td", "td-name");
      if (row.base_url) {
        const a = document.createElement("a");
        a.className = "site-link";
        a.href = row.base_url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = row.name;
        tdN.appendChild(a);
      } else {
        tdN.textContent = row.name;
      }
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
      const tdU = el("td", "td-uptime");
      const g = el("div", "uptime-grid");
      g.setAttribute("role", "img");
      const tip = (row.status || "—") + (row.samples && row.online_rate_pct != null ? " · " + row.online_rate_pct + "%" : "");
      g.setAttribute("title", tip);
      g.setAttribute("aria-label", tip);
      const keys = row.uptime_block_keys || [];
      for (var i = 0; i < 12; i++) {
        const k = keys[i] || "pad";
        g.appendChild(el("span", "uptime-sq sq-" + k));
      }
      tdU.appendChild(g);
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
      const tdn = el("td", "td-name");
      if (x.base_url) {
        const ax = document.createElement("a");
        ax.className = "site-link";
        ax.href = x.base_url;
        ax.target = "_blank";
        ax.rel = "noopener noreferrer";
        ax.textContent = x.name;
        tdn.appendChild(ax);
      } else tdn.textContent = x.name;
      tr.appendChild(tdn);
      const rate =
        x.samples_in_window && x.success_rate != null
          ? (Math.round(x.success_rate * 1000) / 10).toFixed(1) + "%"
          : "—";
      tr.appendChild(el("td", "td-metric", rate));
      const lat = x.avg_latency_ms != null ? String(x.avg_latency_ms) : "—";
      tr.appendChild(el("td", "td-metric td-lat", lat));
      const tdu = el("td", "url");
      if (x.base_url) {
        const bx = document.createElement("a");
        bx.className = "site-link";
        bx.href = x.base_url;
        bx.target = "_blank";
        bx.rel = "noopener noreferrer";
        bx.appendChild(el("small", null, x.base_url));
        tdu.appendChild(bx);
      }
      tr.appendChild(tdu);
      tbody.appendChild(tr);
    });
  }

  const RANK_BUNDLE_KEYS = ["day", "week", "month"];

  function initRankPoll() {
    const root = document.getElementById("rank-page-root");
    if (!root) return;
    if (!root.getAttribute("data-bundles")) {
      return;
    }
    const sec = parseInt(root.getAttribute("data-poll-sec") || "8", 10) * 1000;
    const poll = () => {
      fetch("/api/rank-bundles")
        .then((r) => r.json())
        .then((d) => {
          setText("rank-stat-updated", fmtTime(d.updated_at));
          RANK_BUNDLE_KEYS.forEach((pk) => {
            const b = d[pk];
            if (!b) return;
            const meta = b.models_meta;
            (meta && meta.length
              ? meta
              : MODEL_SLUGS.map((s) => ({ slug: s }))
            ).forEach((m) => {
              const tb = document.getElementById("tb-" + pk + "-model-" + m.slug);
              if (tb) renderModelRows(tb, b.by_model && b.by_model[m.slug]);
            });
            const tbleg = document.getElementById("tb-legacy-" + pk);
            if (tbleg) renderLegacyRows(tbleg, b.legacy);
          });
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

  function initHvoyCards() {
    const box = document.getElementById("model-cards-hvoy");
    const hint = document.getElementById("probe-hvoy-hint");
    if (!box) return;
    const cards = box.querySelectorAll(".model-card-hvoy");
    function updateHint() {
      if (!hint) return;
      const r = box.querySelector('input[name="model_slug"]:checked');
      if (!r) return;
      const lab = r.closest("label");
      const n = lab && lab.querySelector(".model-card-t");
      const c = lab && lab.querySelector(".model-card-id");
      var ntxt = n ? n.textContent : "";
      var ctx = c ? c.textContent : "";
      var lang = document.getElementById("html-root") && document.getElementById("html-root").getAttribute("lang");
      if (lang === "en") {
        hint.textContent = "Primary line: " + ntxt + " · match " + ctx + " in /v1/models";
      } else {
        hint.textContent = "主评 " + ntxt + "：在 /v1/models 返回中匹配 " + ctx + "。";
      }
    }
    box.addEventListener("change", function () {
      cards.forEach(function (c) {
        c.classList.toggle("is-checked", c.querySelector("input").checked);
      });
      updateHint();
    });
    cards.forEach(function (c) {
      c.classList.toggle("is-checked", c.querySelector("input").checked);
    });
    updateHint();
  }

  function _applyRankHash() {
    var h = (location.hash || "").replace(/^#/, "");
    if (h && /^m-/.test(h) && !/^m-(day|week|month)-/.test(h)) {
      h = "m-day-" + h.slice(2);
      try {
        history.replaceState(null, "", "#" + h);
      } catch (ex) {}
    }
    var m = h.match(/^m-(day|week|month)-(.+)$/);
    if (!m) return;
    var period = m[1];
    var slug = m[2];
    var nav = document.querySelector(
      '.rank-model-tabs[data-period="' + period + '"]'
    );
    if (!nav) return;
    var btn = nav.querySelector('.rank-tab[data-slug="' + slug + '"]');
    if (!btn) return;
    nav.querySelectorAll(".rank-tab").forEach(function (b) {
      b.classList.remove("is-active");
    });
    btn.classList.add("is-active");
    var p = document.getElementById("period-" + period);
    if (p) {
      p.querySelectorAll(".model-block.tabbed").forEach(function (sec) {
        sec.classList.toggle(
          "model-block--hidden",
          sec.getAttribute("data-slug") !== slug
        );
      });
    }
  }

  function initRankTabs() {
    document.querySelectorAll(".rank-model-tabs[data-period]").forEach(function (nav) {
      nav.addEventListener("click", function (e) {
        var btn = e.target && e.target.closest && e.target.closest(".rank-tab[data-slug]");
        if (!btn) return;
        e.preventDefault();
        var slug = btn.getAttribute("data-slug");
        var period = nav.getAttribute("data-period");
        if (!period) return;
        nav.querySelectorAll(".rank-tab").forEach(function (b) {
          b.classList.remove("is-active");
        });
        btn.classList.add("is-active");
        var p = document.getElementById("period-" + period);
        if (p) {
          p.querySelectorAll(".model-block.tabbed").forEach(function (sec) {
            sec.classList.toggle(
              "model-block--hidden",
              sec.getAttribute("data-slug") !== slug
            );
          });
        }
        try {
          history.replaceState(null, "", "#m-" + period + "-" + slug);
        } catch (ex) {}
      });
    });
    _applyRankHash();
    window.addEventListener("hashchange", _applyRankHash);
  }

  function fmtCost(n) {
    if (n == null || !isFinite(n)) return "—";
    if (Math.abs(n) >= 100) return n.toFixed(2);
    if (Math.abs(n) >= 1) return n.toFixed(3);
    return n.toFixed(4);
  }

  function doHomeCostCalc() {
    var pUsd = parseFloat(
      (document.getElementById("home-cost-p-usd") || {}).value
    );
    var mult = parseFloat((document.getElementById("home-cost-mult") || {}).value);
    var rmb = parseFloat((document.getElementById("home-cost-rmb") || {}).value);
    var credit = parseFloat(
      (document.getElementById("home-cost-credit") || {}).value
    );
    function setz(id, t) {
      var el = document.getElementById(id);
      if (el) el.textContent = t;
    }
    if (!(rmb > 0) || !(credit > 0)) {
      setz("home-cost-v-purchase-zh", "—");
      setz("home-cost-v-purchase-en", "—");
      setz("home-cost-v-consume-zh", "—");
      setz("home-cost-v-consume-en", "—");
      setz("home-cost-v-final-zh", "—");
      setz("home-cost-v-final-en", "—");
      return;
    }
    var purchasePerYuan = credit / rmb;
    setz(
      "home-cost-v-purchase-zh",
      fmtCost(purchasePerYuan) + " 额度/元"
    );
    setz(
      "home-cost-v-purchase-en",
      fmtCost(purchasePerYuan) + " credits / CNY"
    );
    if (!(pUsd >= 0) || !(mult >= 0)) {
      setz("home-cost-v-consume-zh", "—");
      setz("home-cost-v-consume-en", "—");
      setz("home-cost-v-final-zh", "—");
      setz("home-cost-v-final-en", "—");
      return;
    }
    var consumePerM = pUsd * mult;
    setz(
      "home-cost-v-consume-zh",
      fmtCost(consumePerM) + "（官方标价×倍率 同口径）"
    );
    setz(
      "home-cost-v-consume-en",
      fmtCost(consumePerM) + " (USD/M × mult)"
    );
    var finalYuan = consumePerM / purchasePerYuan;
    setz("home-cost-v-final-zh", fmtCost(finalYuan));
    setz("home-cost-v-final-en", fmtCost(finalYuan));
  }

  function initHomeCostCalc() {
    var btn = document.getElementById("home-cost-btn");
    if (!btn) return;
    ["home-cost-p-usd", "home-cost-mult", "home-cost-rmb", "home-cost-credit"].forEach(
      function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener("change", doHomeCostCalc);
        el.addEventListener("input", doHomeCostCalc);
      }
    );
    btn.addEventListener("click", doHomeCostCalc);
    var lang = document.getElementById("lang");
    if (lang) {
      lang.addEventListener("change", function () {
        doHomeCostCalc();
      });
    }
    doHomeCostCalc();
  }

  function go() {
    initHomeBroadcast();
    initHvoyCards();
    initHomeProbe();
    initProbeShare();
    initHomeCostCalc();
    initMatrix();
    initRankTabs();
    initRankPoll();
    initInclusion();
  }
})();
