(function () {
  const I18N = {
    zh: {
      brand: "中测",
      subtitle: "中转站 API 检测平台",
      nav_home: "首页",
      nav_rank: "中转站排行",
      nav_yiyuan: "一元模型",
      nav_inclusion: "申请收录",
      nav_workspace: "工作台",
      nav_logout: "退出",
      nav_login: "登录",
      foot_copy: "中测",
      home_eyebrow: "中转站 API 检测平台",
      home_brand_title: "中测",
      home_tagline: "识别中转站接口真伪 · 多模型分榜 · 持续探测",
      home_cta: "进入中转站排行",
      home_cta2: "申请收录",
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
      col_price: "1人民币=x Token",
      col_online: "在线率",
      col_dilu: "掺水率",
      col_lat: "延迟 (ms)",
      col_run: "运行状态",
      col_in_usd: "输入/$",
      col_out_usd: "输出/$",
      col_cny_token: "1人民币=X TOKEN",
      col_base: "Base",
      pricing_cols_hint:
        "与全站、首页一致：表头为「输入/$」「输出/$」「1人民币=X TOKEN」（后台维护）。掺水：人工登记优先，否则为当前模型线目录探测摘要（非对话掺水鉴定）。",
      sort_label: "排行",
      sort_default: "综合",
      sort_price_desc: "价格从高到低",
      sort_price_asc: "价格从低到高",
      sort_perf_desc: "性能从高到低",
      sort_perf_asc: "性能从低到高",
      col_window_ok: "窗口成功率",
      col_avg_lat: "均延迟 (ms)",
      rank_h1: "中转站排行",
      rank_recommend: "推荐",
      rank_legacy_h: "总榜（/v1/models 全通道）",
      rank_note:
        "在线率来自窗口内 GET /v1/models 子串命中。表头「输入/$」「输出/$」为登记单价口径；「1人民币=X TOKEN」为充值折算。掺水率：后台登记优先；未登记时按本模型线目录探测在线率生成提示（非对话质检）。",
      rank_live_ribbon: "排行数据与服务器同步中",
      home_live_ribbon: "全站数据实时刷新中",
      stat_enabled: "已启用站点",
      stat_samples: "窗口内探测次数",
      stat_enabled_tip:
        "当前在库中勾选了「启用探测」的中转站数量；这些站会参与全站定时探测任务。",
      stat_samples_tip:
        "当前统计时间窗口内写入数据库的「目录探测」样本总条数（全库累计）。与「已启用站点」无固定倍数：取决于轮询间隔、失败重试以及曾收录后又禁用的站点留存记录。",
      stat_window: "统计窗口",
      detector_h2: "在线检测",
      detector_hint:
        "输入 OpenAI 兼容根地址，Key 仅本次经服务器转发、不作持久保存。",
      detector_hint_en:
        "Base URL and optional key; key not stored, rate-limited.",
      detector_api: "API 根地址",
      detector_api_label: "API 接口地址",
      detector_key: "API Key",
      detector_key_label: "API Key",
      detector_path: "检测路径",
      detector_models_hint: "返回体中对目标模型的子串匹配：",
      detector_go: "开始检测",
      detector_sec_cfg: "接口配置",
      detector_hist: "中转站排行",
      detector_hint2: "向网关请求 GET /v1/models。先选主评线。",
      target_model_lbl: "目标模型",
      detector_privacy: "不保存你的 Key 与业务对话。建议测试专用 Key。",
      tab_legacy: "总榜",
      home_broadcast_h2: "全站监测摘要",
      home_broadcast_p: "与排行同一统计窗口，每 10 秒拉取。",
      home_detect_rank_h2: "主评线检测排名",
      home_detect_rank_sub: "24 小时窗 · Opus 4.7（与日榜一致）",
      home_detect_rank_link: "完整排行",
      detector_hint2_en: "GET /v1/models once. Pick model line. Key not stored.",
      detector_privacy_en: "Key not stored. Use test keys.",
      home_live_ribbon_en: "Live",
      inc_h2: "中转站收录申请",
      inc_hint2:
        "在此提交，字段习惯可参考禾维。审核通过后由管理员配置探测。",
      inc_hint2_en: "Listing request, similar to Hvoy. Admin reviews.",
      inc_hint_short: "需登记站点信息、测试账户约定与申报模型线；完整表单与进度查询请前往收录专页。",
      inc_hint_short_en: "Use the dedicated inclusion page for the full form and status lookup.",
      inc_go_full: "填写收录申请",
      inc_status_btn: "查看申请状态",
      inc_notice_p1: "中测为公开技术探测索引：收录与基础探测不收费，意在提供可复现的网关健康度参考，中立第三方视角。",
      inc_notice_p2: "全站数据由程序按固定路径定时请求、自动汇总；收录后如需对话级用量抽检，将使用单独配置的探测 Key（非人工登录你的账户）。",
      inc_notice_p3: "请提供可探测的测试账户信息（由管理员在后台录入），账户内需保留不少于 ¥100 可用额度，供目录与抽样请求消耗；测试额度仅用于技术探测，不作任何非探测用途。",
      inc_notice_p4: "测试站密码要求（与常见安全基线一致）：长度 > 8；含英文大写与小写、数字与特殊字符，避免与正式主账号同口令。",
      inc_notice_p5: "资料齐全时，一般在 1–2 个工作日内完成审核与上线探测；高峰期可能顺延，以站内状态为准。",
      inc_sec_site: "站点信息",
      inc_site_name: "站点名称",
      inc_site_url: "站点 URL",
      inc_founded: "成立时间",
      inc_signup: "注册 URL",
      inc_sec_contact: "联系信息",
      inc_person: "联系人",
      inc_sec_other: "其他",
      inc_suggest_group: "建议分组",
      inc_sec_models: "支持的模型（申报）",
      inc_models_hint: "勾选贵站实际可提供的线路，便于审核侧对照目录；与中测探测目标线对齐。",
      inc_status_h1: "申请状态",
      inc_back_form: "返回申请表",
      inc_status_lead: "提交成功后页面会显示申请编号；也可在此输入编号查询当前进度。",
      inc_q_id: "申请编号",
      inc_q_btn: "查询",
      inc_q_site: "站点",
      inc_q_status: "状态",
      inc_q_time: "提交时间",
      inc_name: "站点名称",
      inc_url: "站点 URL (Base)",
      inc_contact: "联系方式",
      inc_remark: "备注",
      inc_submit: "提交申请",
      inc_sec_probe: "探测账户",
      inc_probe_hint:
        "用于收录后自动目录/抽检的测试账号。密码须含大小写、数字、特殊符号且长于 8 位（与贵站常见安全基线一致）。",
      inc_probe_login: "探测用账户",
      inc_probe_pw: "探测用密码",
      ws_h2: "个人工作台",
      ws_p1: "以下为与全站相同数据源的实时摘要（每 10 秒更新）。可前往排行或首页使用在线检测。",
      ad_pw_h: "修改当前账号密码",
      ad_boot: "首启创建管理员",
      f_old: "原密码",
      f_new: "新密码",
      f_save: "保存新密码",
      matrix_h2: "下列为本库已收录站点",
      viz_title: "本检测 · 多线模型",
      viz_lat: "近 12 次本机检测延迟",
      register_title: "注册",
      login_h2: "登录",
      login_hint: "",
      f_user: "用户名",
      f_pass: "密码",
      f_submit: "登录",
      reg_h3: "注册",
      reg_btn: "注册",
      rep_h1: "在线检测报告",
      rep_h2: "检测结果",
      btn_share: "分享报告",
      m_lat: "延迟 (ms)",
      m_tokps: "Tokens/秒",
      m_tin: "输入 Tokens",
      m_tout: "输出 Tokens",
      m_tcr: "缓存读 Tokens",
      m_tcw: "缓存写 Tokens",
      m_na: "不适用",
      m_knote: "目录与对话实连；无 Key 时仅目录。",
      m_knote_en: "With API key, chat usage is probed. Without key, models only.",
      rep_rank_link: "查看全站排行",
      rep_by: "中测 / OpenAI-compatible 目录探测",
      probe_banner_sub: "试探测不保存你的 Key 与业务对话。为保障账户安全，建议优先使用测试专用 Key。我们重视你的隐私，可在合规场景下放心使用。",
      probe_banner_sub_en: "Probes do not store your key or chat content. Prefer a test-only key. We care about your privacy and security.",
      cost_h2: "成本计算",
      cost_sec: "实付单价试算",
      cost_link_formula: "公式与拆解",
      cost_hint:
        "填写该站的官方美金单价、倍率、充值活动，试算实付约多少元人民币/百万 Token。与「一元模型」页同一公式。",
      cost_hint_en:
        "Enter USD/M, multiplier, top-up deal; estimate CNY per million tokens. Same formula as the ¥/token page.",
      cost_p_usd: "官方美金单价（$/百万 Token）",
      cost_mult: "站长倍率",
      cost_rmb: "充值人民币（元）",
      cost_credit: "充值所得额度",
      cost_privacy: "仅在本机浏览器内计算，数据不上传。",
      cost_privacy_en: "Computed in your browser only; nothing is uploaded.",
      cost_btn: "计算",
      nav_presence_lbl: "在线",
      nav_presence_tip: "约 2 分钟内有活动视为在线；同实例内存统计（多机不合并）。",
      ad_traffic_h2: "日访问量（PV，UTC）",
      ad_traffic_p: "主站各可见页面「GET 成功」计一次（不含 /api、/static 等）。部署多实例时各库独立累加。",
      auth_reg_title: "创建账户",
      auth_reg_sub: "注册以开始使用中测",
      auth_login_lead: "使用已有账号登录",
      auth_pw_hint: "至少 6 个字符",
      auth_foot: "未注册可切换到「注册」创建普通账号",
      auth_copyright: "© 中测",
      auth_aria_close: "关闭",
    },
    en: {
      brand: "Zhongce",
      subtitle: "Relay API Health Board",
      nav_home: "Home",
      nav_rank: "Rankings",
      nav_yiyuan: "¥/Token",
      nav_inclusion: "List a relay",
      nav_workspace: "Workspace",
      nav_logout: "Logout",
      nav_login: "Login",
      foot_copy: "Zhongce",
      home_eyebrow: "Relay API verification platform",
      home_brand_title: "Zhongce",
      home_tagline: "Spot fake relays · per-model tables · always-on probes",
      home_cta: "Open rankings",
      home_cta2: "Request listing",
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
      col_price: "1 CNY = x Tokens",
      col_online: "Online %",
      col_dilu: "Dilution",
      col_lat: "Latency (ms)",
      col_run: "Status",
      col_in_usd: "Input /$",
      col_out_usd: "Output /$",
      col_cny_token: "1 CNY = X TOKEN",
      col_base: "Base",
      pricing_cols_hint:
        "Same headers site-wide: Input /$, Output /$, 1 CNY = X TOKEN (admin). Dilution: manual first, else a per-model-line catalog-probe hint (not chat dilution QA).",
      sort_label: "Sort",
      sort_default: "Default",
      sort_price_desc: "Price high → low",
      sort_price_asc: "Price low → high",
      sort_perf_desc: "Perf high → low",
      sort_perf_asc: "Perf low → high",
      col_window_ok: "Window success",
      col_avg_lat: "Avg (ms)",
      rank_h1: "Relay leaderboards",
      rank_recommend: "Featured",
      rank_legacy_h: "Aggregate (all /v1/models)",
      rank_note:
        "Online rate uses /v1/models substring hits in the window. Columns Input /$, Output /$ and CNY/token are as registered. Dilution: admin text/percent first; if empty, a short probe-based hint for this model line (not chat-level dilution QA).",
      rank_live_ribbon: "Leaderboard sync",
      rank_live_ribbon_en: "Syncing",
      home_live_ribbon: "Live refresh",
      home_live_ribbon_en: "polled",
      stat_enabled: "Enabled relays",
      stat_samples: "Probes in window",
      stat_enabled_tip:
        "How many relays are marked enabled for scheduled probing.",
      stat_samples_tip:
        "Total ProbeSample rows written in the window (all relays). Not a fixed multiple of enabled relays—depends on poll interval, retries, and history from relays later disabled.",
      stat_window: "Window",
      detector_h2: "Live check",
      detector_hint:
        "Base URL; optional key used only for this request, not stored.",
      detector_hint_en: "Base URL; key not stored, rate-limited.",
      detector_api: "Base URL",
      detector_api_label: "API interface URL",
      detector_key: "API Key",
      detector_key_label: "API Key",
      detector_path: "Path",
      detector_models_hint: "Substring model hits:",
      detector_go: "Run check",
      detector_sec_cfg: "Endpoint",
      detector_hist: "Rankings",
      detector_hint2: "GET /v1/models. Pick a line. Key not stored.",
      target_model_lbl: "Model",
      detector_privacy: "Keys not stored. Use test keys.",
      tab_legacy: "Aggregate",
      home_broadcast_h2: "Site snapshot",
      home_broadcast_p: "Same window as rank; polled every 10s.",
      home_detect_rank_h2: "Primary line rankings",
      home_detect_rank_sub: "24h · Opus 4.7 (same as daily board)",
      home_detect_rank_link: "Full leaderboard",
      inc_h2: "List your relay",
      inc_hint2: "Fields similar to Hvoy. Admin will enable probes.",
      inc_hint2_en: "Hvoy-style request.",
      inc_hint_short: "Use the full inclusion page for site details, test-account terms, declared model lines, and status lookup.",
      inc_hint_short_en: "Full form and status are on the inclusion page.",
      inc_go_full: "Open inclusion form",
      inc_status_btn: "Application status",
      inc_notice_p1: "Zhongce is a public technical index: basic listing and probes are free, for reproducible gateway health signals from a neutral third-party view.",
      inc_notice_p2: "Site-wide stats are collected automatically on a schedule; if chat-level usage sampling is needed after listing, a dedicated probe key is configured—not a human logging into your account.",
      inc_notice_p3: "Provide a test account for operators to enter in the admin panel, with at least ¥100 usable balance for directory and sampling traffic. Credits are strictly for technical probing.",
      inc_notice_p4: "Test-account password baseline: length > 8; include uppercase & lowercase Latin letters, digits, and a symbol; avoid reusing your production password.",
      inc_notice_p5: "When information is complete, review is typically within 1–2 business days; may slip at peak times—follow status in-app.",
      inc_sec_site: "Site",
      inc_site_name: "Site name",
      inc_site_url: "Site URL",
      inc_founded: "Founded date",
      inc_signup: "Sign-up URL",
      inc_sec_contact: "Contact",
      inc_person: "Contact person",
      inc_sec_other: "Other",
      inc_suggest_group: "Suggested group",
      inc_sec_models: "Supported models (declared)",
      inc_models_hint: "Check lines you actually offer so reviewers can compare with your catalog.",
      inc_status_h1: "Application status",
      inc_back_form: "Back to form",
      inc_status_lead: "After submit you get an application ID; enter it here to check progress.",
      inc_q_id: "Application ID",
      inc_q_btn: "Lookup",
      inc_q_site: "Site",
      inc_q_status: "Status",
      inc_q_time: "Submitted at",
      inc_name: "Name",
      inc_url: "Base URL",
      inc_contact: "Contact",
      inc_remark: "Notes",
      inc_submit: "Submit",
      inc_sec_probe: "Probe account",
      inc_probe_hint:
        "Test credentials for scheduled directory/chat sampling after listing. Password policy: mixed case, digit, symbol, length > 8.",
      inc_probe_login: "Probe login",
      inc_probe_pw: "Probe password",
      ws_h2: "Workspace",
      ws_p1: "Snapshot below refreshes every 10s. Use rank or home live check.",
      ad_pw_h: "Change your password",
      ad_boot: "Bootstrap first admin",
      f_old: "Current password",
      f_new: "New password",
      f_save: "Update",
      register_title: "Register",
      matrix_h2: "Relays in this library",
      viz_title: "This check · model lines",
      viz_lat: "Last 12 one-off latencies (browser only)",
      login_h2: "Sign in",
      login_hint: "",
      f_user: "Username",
      f_pass: "Password",
      f_submit: "Sign in",
      reg_h3: "Register",
      reg_btn: "Register",
      rep_h1: "Probe report",
      rep_h2: "Results",
      btn_share: "Share report",
      m_lat: "Latency (ms)",
      m_tokps: "Tokens/s",
      m_tin: "Input tokens",
      m_tout: "Output tokens",
      m_tcr: "Cache read",
      m_tcw: "Cache write",
      m_na: "N/A",
      m_knote: "Models + optional chat usage with API key. Deep checks not on this page.",
      m_knote_en: "With API key, one chat completion and usage. Without key, models only.",
      rep_rank_link: "Open full rankings",
      rep_by: "Zhongce · OpenAI-compatible models list probe",
      probe_banner_sub: "Probes do not store your key or chat content. Prefer a test-only key. We care about your privacy and security.",
      probe_banner_sub_en: "Probes do not store your key or chat content. Prefer a test-only key.",
      cost_h2: "Cost estimate",
      cost_sec: "CNY / M token estimate",
      cost_link_formula: "Formula",
      cost_hint:
        "Enter USD per million, multiplier, and your top-up. Estimates CNY per million output tokens. Same as the ¥/token page.",
      cost_hint_en:
        "Same as above. Numbers stay in your browser.",
      cost_p_usd: "Official USD / M tokens",
      cost_mult: "Provider multiplier",
      cost_rmb: "Top-up CNY (¥)",
      cost_credit: "Credit received from top-up",
      cost_privacy: "Computed in-browser only; nothing is uploaded.",
      cost_privacy_en: "In-browser only.",
      cost_btn: "Calculate",
      nav_presence_lbl: "Live",
      nav_presence_tip: "Activity within ~2 min counts as online. In-process count (not merged across workers).",
      ad_traffic_h2: "Daily page views (UTC)",
      ad_traffic_p: "One count per successful HTML GET (excludes /api, /static). Each app instance has its own counter.",
      auth_reg_title: "Create account",
      auth_reg_sub: "Register to use Zhongce",
      auth_login_lead: "Sign in with an existing account",
      auth_pw_hint: "At least 6 characters",
      auth_foot: "Use the Register tab to create a normal account.",
      auth_copyright: "© Zhongce",
      auth_aria_close: "Close",
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
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const k = el.getAttribute("data-i18n-title");
      if (k && t[k]) el.setAttribute("title", t[k]);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const k = el.getAttribute("data-i18n-aria");
      if (k && t[k]) el.setAttribute("aria-label", t[k]);
    });
    const sel = document.getElementById("lang");
    if (sel) sel.value = lang;
    localStorage.setItem("zhongce_lang", lang);
  }

  document.addEventListener("zhongce-refresh-i18n", function () {
    applyLang(localStorage.getItem("zhongce_lang") || "zh");
  });

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

  const strip = document.getElementById("kuma-appstrip");
  const stripDot = document.getElementById("kuma-app-health");
  const stripLine = document.getElementById("kuma-app-line");
  function kumaAppStrip() {
    if (!strip) return;
    fetch("/health")
      .then((r) => r.json())
      .then((d) => {
        strip.hidden = false;
        if (stripLine) stripLine.textContent = d.status === "ok" ? "中测 API 正常" : "—";
        if (stripDot) stripDot.className = d.status === "ok" ? "kuma-strip-dot kuma-up" : "kuma-strip-dot kuma-down";
      })
      .catch(() => {
        strip.hidden = false;
        if (stripLine) stripLine.textContent = "API 不可达";
        if (stripDot) stripDot.className = "kuma-strip-dot kuma-down";
      });
  }
  kumaAppStrip();
  setInterval(kumaAppStrip, 120000);

  (function initAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (!modal) return;
    const sLogin = document.getElementById("auth-surface-login");
    const sReg = document.getElementById("auth-surface-reg");
    const tIn = document.getElementById("auth-tab-in");
    const tUp = document.getElementById("auth-tab-up");
    const msg = document.getElementById("auth-modal-msg");
    const nav = document.getElementById("nav-auth-open");
    const backdrop = modal.querySelector("[data-auth-close]");
    const xBtn = document.getElementById("auth-modal-x");
    const fLogin = document.getElementById("f-auth-login");
    const fReg = document.getElementById("f-auth-reg");

    function getNext() {
      try {
        return new URLSearchParams(location.search).get("next") || "/workspace";
      } catch (e) {
        return "/workspace";
      }
    }

    function setMode(reg) {
      if (!sLogin || !sReg) return;
      sLogin.hidden = reg;
      sReg.hidden = !reg;
      if (tIn) tIn.classList.toggle("is-on", !reg);
      if (tUp) tUp.classList.toggle("is-on", reg);
      if (msg) msg.textContent = "";
    }

    function openAuth(mode) {
      setMode(mode === "register");
      modal.hidden = false;
      document.body.classList.add("auth-modal-open");
      if (getComputedStyle(document.body).overflow === "auto" || getComputedStyle(document.body).overflow === "visible") {
        document.body.style.overflow = "hidden";
      }
    }

    function closeAuth() {
      modal.hidden = true;
      document.body.classList.remove("auth-modal-open");
      document.body.style.overflow = "";
    }

    if (tIn) tIn.addEventListener("click", () => setMode(false));
    if (tUp) tUp.addEventListener("click", () => setMode(true));
    if (backdrop) backdrop.addEventListener("click", closeAuth);
    if (xBtn) xBtn.addEventListener("click", closeAuth);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !modal.hidden) closeAuth();
    });
    if (nav) {
      nav.addEventListener("click", (e) => {
        e.preventDefault();
        openAuth("login");
      });
    }
    if (fLogin) {
      fLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!msg) return;
        const fd = new FormData(fLogin);
        const r = await fetch("/api/auth/login", { method: "POST", body: fd, credentials: "same-origin" });
        if (r.ok) {
          location.href = getNext();
          return;
        }
        msg.textContent = (await r.json().catch(() => ({}))).detail || String(r.status);
      });
    }
    if (fReg) {
      fReg.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!msg) return;
        const fd = new FormData(fReg);
        const r = await fetch("/api/auth/register", { method: "POST", body: fd, credentials: "same-origin" });
        if (r.ok) {
          location.href = getNext();
          return;
        }
        msg.textContent = (await r.json().catch(() => ({}))).detail || String(r.status);
      });
    }
    if (document.getElementById("auth-page-only")) {
      const q = new URLSearchParams(location.search);
      if (q.get("mode") === "register") openAuth("register");
      else openAuth("login");
    }
  })();

  function newVisitorId() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return "v" + crypto.randomUUID().replace(/-/g, "");
    }
    return "v" + String(Date.now()) + "x" + String(Math.random()).slice(2, 12);
  }

  function initPresencePill() {
    const nEl = document.getElementById("presence-count");
    if (!nEl) return;
    var key = "zhongce_vid";
    var vid = null;
    try {
      vid = localStorage.getItem(key);
    } catch (e) {
      vid = null;
    }
    if (!vid || String(vid).length < 8) {
      vid = newVisitorId();
      try {
        localStorage.setItem(key, vid);
      } catch (e) {}
    }
    function setCount(n) {
      if (n == null || n === "") nEl.textContent = "—";
      else nEl.textContent = String(n);
    }
    function ping() {
      fetch("/api/presence/heartbeat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ visitor_id: vid }),
        credentials: "same-origin",
      })
        .then((r) => r.json().then((j) => ({ ok: r.ok, j })))
        .then(({ ok, j }) => {
          if (ok && j.online != null) setCount(j.online);
          else setCount(null);
        })
        .catch(function () {
          setCount(null);
        });
    }
    fetch("/api/presence", { credentials: "same-origin" })
      .then((r) => r.json())
      .then((j) => {
        if (j.online != null) setCount(j.online);
      })
      .catch(function () {});
    ping();
    setInterval(ping, 30000);
  }

  initPresencePill();
})();
