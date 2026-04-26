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
      home_h1: "中测 · 海外节点中转站 API 检测与排名",
      home_lead: "多家中转网关可用性、延迟与按模型线号展示。",
      home_cta: "进入中转站排行",
      col_rank: "排名",
      col_site: "站点",
      col_group: "站点分组",
      col_price: "价格",
      col_online: "在线率",
      col_dilu: "掺水率",
      col_lat: "延迟 (ms)",
      col_run: "运行状态",
      rank_note: "在线率由 /v1/models 是否列出对应模型名判定；掺水率需更深度检测。",
      inc_h2: "申请收录",
      inc_hint: "提交后由管理员审核。",
      inc_submit: "提交",
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
      home_h1: "Zhongce — Relay API checks & rankings",
      home_lead: "Availability, latency, and per-model presence from the models catalog.",
      home_cta: "Open rankings",
      col_rank: "Rank",
      col_site: "Site",
      col_group: "Group",
      col_price: "Price",
      col_online: "Online %",
      col_dilu: "Dilution",
      col_lat: "Latency",
      col_run: "Status",
      rank_note: "Online rate uses substring match in /v1/models; dilution needs deeper checks.",
      inc_h2: "Apply for listing",
      inc_hint: "Pending admin review.",
      inc_submit: "Submit",
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
