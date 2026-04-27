/**
 * 一元模型页：1 元可购买多少 Token（由实付 ¥/百万 Token 换算）
 */
(function () {
  function fmt(n) {
    if (n == null || !isFinite(n)) return "—";
    if (Math.abs(n) >= 100) return n.toFixed(2);
    if (Math.abs(n) >= 1) return n.toFixed(3);
    return n.toFixed(4);
  }

  /** 正整数枚数，千分位 */
  function fmtTokens(n) {
    if (n == null || !isFinite(n) || n <= 0) return "—";
    return Math.round(n).toLocaleString("zh-CN");
  }

  function readNum(id) {
    var el = document.getElementById(id);
    if (!el) return NaN;
    var v = el.value;
    if (v === "" || v == null) return NaN;
    return parseFloat(v);
  }

  function setSpan(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function calc() {
    var pUsd = readNum("yiyuan-p-usd");
    var mult = readNum("yiyuan-mult");
    var rmb = readNum("yiyuan-rmb");
    var credit = readNum("yiyuan-credit");

    if (!(rmb > 0) || !(credit > 0)) {
      setSpan("yiyuan-v-purchase", "—");
      setSpan("yiyuan-v-consume", "—");
      setSpan("yiyuan-v-tokens", "—");
      setSpan("yiyuan-v-yuan-per-m", "—");
      return;
    }

    var purchasePerYuan = credit / rmb;
    setSpan("yiyuan-v-purchase", fmt(purchasePerYuan) + " 额度/元");

    if (!(pUsd >= 0) || !(mult >= 0)) {
      setSpan("yiyuan-v-consume", "—");
      setSpan("yiyuan-v-tokens", "—");
      setSpan("yiyuan-v-yuan-per-m", "—");
      return;
    }

    var consumePerM = pUsd * mult;
    setSpan(
      "yiyuan-v-consume",
      fmt(consumePerM) + "（与「官方标价×倍率」同口径的额度/百万）"
    );

    var finalYuanPerM = consumePerM / purchasePerYuan;
    var tokensPerOneYuan =
      finalYuanPerM > 0 ? 1e6 / finalYuanPerM : NaN;
    setSpan("yiyuan-v-tokens", fmtTokens(tokensPerOneYuan));
    setSpan("yiyuan-v-yuan-per-m", fmt(finalYuanPerM));
  }

  function bind() {
    var btn = document.getElementById("yiyuan-calc-btn");
    if (btn) btn.addEventListener("click", calc);
    ["yiyuan-p-usd", "yiyuan-mult", "yiyuan-rmb", "yiyuan-credit"].forEach(
      function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener("change", calc);
        el.addEventListener("input", calc);
      }
    );
    calc();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();
