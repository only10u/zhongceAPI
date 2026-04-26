(function () {
  const I18N = {
    zh: {
      brand: "中测",
      subtitle: "中转站 API 检测平台",
      nav_home: "首页",
      nav_rank: "中转站排行",
      nav_inclusion: "中转站收录",
      nav_workspace: "工作台",
      nav_logout: "退出",
      nav_login: "登录",
      foot_copy: "中测",
      foot_tg: "Telegram: @only10u",
      home_eyebrow: "中转站 API 检测平台",
      home_brand_title: "中测",
      home_tagline: "识别中转站接口真伪 · 多模型分榜 · 持续探测",
      home_cta: "进入中转站排行",
      home_cta2: "申请收录",
      home_cta_api: "OpenAPI 文档",
      home_b1_t: "多模型分榜",
      home_b2_t: "可调时间窗口",
      home_b3_t: "开放 JSON / 自架",
      home_models_h: "目标模型 / 去排行",
      home_how_h: "我们测什么、不承诺什么",
      home_faq_h: "常见问题",
      chip_badge: "新",
      col_rank: "排名",
      col_site: "站点",
      col_site2: "名称",
      col_group: "站点分组",
      col_price: "价格",
      col_online: "在线率",
      col_dilu: "掺水率",
      col_lat: "延迟 (ms)",
      col_run: "运行状态",
      col_window_ok: "窗口成功率",
      col_avg_lat: "均延迟 (ms)",
      rank_h1: "中转站排行",
      rank_recommend: "推荐",
      rank_legacy_h: "总榜（/v1/models 全通道）",
      rank_note: "在线率由 /v1/models 是否列出对应模型名判定；掺水率需更深度检测。",
      rank_live_ribbon: "排行数据与服务器同步中",
      home_live_ribbon: "全站数据实时刷新中",
      stat_enabled: "已启用站点",
      stat_samples: "窗口内探测次数",
      stat_window: "统计窗口",
      detector_h2: "在线检测",
      detector_hint:
        "输入 OpenAI 兼容根地址，Key 仅本次经服务器转发、不作持久保存。",
      detector_hint_en:
        "Base URL and optional key; key not stored, rate-limited.",
      detector_api: "API 根地址",
      detector_key: "API Key",
      detector_path: "检测路径",
      detector_models_hint: "返回体中对目标模型的子串匹配：",
      detector_go: "开始检测",
      home_broadcast_h2: "全站监测摘要",
      home_broadcast_p: "与排行同一统计窗口，每 10 秒拉取。",
      home_live_ribbon_en: "Live",
      inc_h2: "中转站收录",
      inc_hint2:
        "在此提交，字段习惯可参考禾维。审核通过后由管理员配置探测。",
      inc_hint2_en: "Listing request, similar to Hvoy. Admin reviews.",
      inc_name: "站点名称",
      inc_url: "站点 URL (Base)",
      inc_contact: "联系方式",
      inc_remark: "备注",
      inc_submit: "提交申请",
      ws_h2: "个人工作台",
      ws_p1: "以下为与全站相同数据源的实时摘要（每 10 秒更新）。可前往排行或首页使用在线检测。",
      ad_pw_h: "修改当前账号密码",
      ad_boot: "首启创建管理员",
      f_old: "原密码",
      f_new: "新密码",
      f_save: "保存新密码",
      register_title: "注册",
      login_h2: "登录",
      login_hint: "",
      f_user: "用户名",
      f_pass: "密码",
      f_submit: "登录",
      reg_h3: "注册",
      reg_btn: "注册",
    },
    en: {
      brand: "Zhongce",
      subtitle: "Relay API Health Board",
      nav_home: "Home",
      nav_rank: "Rankings",
      nav_inclusion: "List a relay",
      nav_workspace: "Workspace",
      nav_logout: "Logout",
      nav_login: "Login",
      foot_copy: "Zhongce",
      foot_tg: "Telegram: @only10u",
      home_eyebrow: "Relay API verification platform",
      home_brand_title: "Zhongce",
      home_tagline: "Spot fake relays · per-model tables · always-on probes",
      home_cta: "Open rankings",
      home_cta2: "Request listing",
      home_cta_api: "OpenAPI docs",
      home_b1_t: "Per-model boards",
      home_b2_t: "Configurable window",
      home_b3_t: "JSON + self-host",
      home_models_h: "Tracked models",
      home_how_h: "What we test / what we do not claim",
      home_faq_h: "FAQ",
      chip_badge: "NEW",
      col_rank: "Rank",
      col_site: "Site",
      col_site2: "Name",
      col_group: "Group",
      col_price: "Price",
      col_online: "Online %",
      col_dilu: "Dilution",
      col_lat: "Latency (ms)",
      col_run: "Status",
      col_window_ok: "Window success",
      col_avg_lat: "Avg (ms)",
      rank_h1: "Relay leaderboards",
      rank_recommend: "Featured",
      rank_legacy_h: "Aggregate (all /v1/models)",
      rank_note: "Online rate uses substring match in /v1/models; dilution needs deeper checks.",
      rank_live_ribbon: "Leaderboard sync",
      rank_live_ribbon_en: "Syncing",
      home_live_ribbon: "Live refresh",
      home_live_ribbon_en: "polled",
      stat_enabled: "Enabled relays",
      stat_samples: "Probes in window",
      stat_window: "Window",
      detector_h2: "Live check",
      detector_hint:
        "Base URL; optional key used only for this request, not stored.",
      detector_hint_en: "Base URL; key not stored, rate-limited.",
      detector_api: "Base URL",
      detector_key: "API Key",
      detector_path: "Path",
      detector_models_hint: "Substring model hits:",
      detector_go: "Run check",
      home_broadcast_h2: "Site snapshot",
      home_broadcast_p: "Same window as rank; polled every 10s.",
      inc_h2: "List your relay",
      inc_hint2: "Fields similar to Hvoy. Admin will enable probes.",
      inc_hint2_en: "Hvoy-style request.",
      inc_name: "Name",
      inc_url: "Base URL",
      inc_contact: "Contact",
      inc_remark: "Notes",
      inc_submit: "Submit",
      ws_h2: "Workspace",
      ws_p1: "Snapshot below refreshes every 10s. Use rank or home live check.",
      ad_pw_h: "Change your password",
      ad_boot: "Bootstrap first admin",
      f_old: "Current password",
      f_new: "New password",
      f_save: "Update",
      register_title: "Register",
      login_h2: "Sign in",
      login_hint: "",
      f_user: "Username",
      f_pass: "Password",
      f_submit: "Sign in",
      reg_h3: "Register",
      reg_btn: "Register",
    },
  };

  function applyLang(lang) {
    const t = I18N[lang] || I18N.zh;
    const root = document.getElementById("html-root");
    if (root) root.setAttribute("lang", lang === "en" ? "en" : "zh-CN");
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const k = el.getAttribute("data-i18n");
      if (k && t[k]) el.textContent = t[k];
    });
    const sel = document.getElementById("lang");
    if (sel) sel.value = lang;
    localStorage.setItem("zhongce_lang", lang);
  }

  const themeKey = "zhongce_theme";
  function applyTheme(t) {
    const root = document.getElementById("html-root");
    if (root) root.setAttribute("data-theme", t);
    localStorage.setItem(themeKey, t);
  }

  const btnTheme = document.getElementById("btn-theme");
  if (btnTheme) {
    btnTheme.addEventListener("click", () => {
      const r = document.getElementById("html-root");
      const next = (r.getAttribute("data-theme") || "dark") === "dark" ? "light" : "dark";
      applyTheme(next);
    });
  }
  const savedT = localStorage.getItem(themeKey);
  if (savedT) applyTheme(savedT);
  const savedL = localStorage.getItem("zhongce_lang") || "zh";
  applyLang(savedL);
  const langSel = document.getElementById("lang");
  if (langSel) {
    langSel.addEventListener("change", () => applyLang(langSel.value));
  }

  const lo = document.getElementById("btn-logout");
  if (lo) {
    lo.addEventListener("click", async () => {
      await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
      location.href = "/";
    });
  }
})();
