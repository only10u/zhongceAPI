/**
 * 首页：全站摘要 + 即时试探测
 * 排行页：轮询 /api/dashboard 重绘表体
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

  function setText(id, t) {
    const el = document.getElementById(id);
    if (el) el.textContent = t;
  }

  function fmtTime(iso) {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch {
      return iso;
    }
  }

  // —— 首页：home-stats
  function initHomeBroadcast() {
    const root = document.getElementById("home-page-root");
    if (!root) return;
    const poll = () => {
      fetch("/api/home-stats")
        .then((r) => r.json())
        .then((d) => {
          setText("home-stat-enabled", String(d.relays_enabled ?? 0));
          setText("home-stat-samples", String(d.probe_samples_in_window ?? 0));
          if (d.window_hours != null) setText("home-stat-window", String(d.window_hours));
          setText("home-stat-time", fmtTime(d.updated_at));
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
        .catch(() => {});
    };
    poll();
    setInterval(poll, 10000);
  }

  // —— 首页：试探测
  function initHomeProbe() {
    const f = document.getElementById("form-try-probe");
    const out = document.getElementById("probe-result");
    if (!f || !out) return;
    f.addEventListener("submit", (e) => {
      e.preventDefault();
      out.hidden = false;
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
            (j.ok ? "请求成功" : "请求未成功") +
            " · " +
            parts.join(" · ") +
            "</p>" +
            (j.error ? "<p class=\"err\">" + j.error + "</p>" : "") +
            "<div class=\"probe-chips\">" +
            chips +
            "</div>";
        })
        .catch((err) => {
          out.className = "probe-result err";
          out.textContent = String(err);
        });
    });
  }

  function el(tag, cls, text) {
    const x = document.createElement(tag);
    if (cls) x.className = cls;
    if (text != null) x.textContent = text;
    return x;
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

  // inclusion 表单
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
    initRankPoll();
    initInclusion();
  }
})();
