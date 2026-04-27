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

  function calc() {
    var pUsd = parseFloat(document.getElementById("yiyuan-p-usd").value);
    var mult = parseFloat(document.getElementById("yiyuan-mult").value);
    var rmb = parseFloat(document.getElementById("yiyuan-rmb").value);
    var credit = parseFloat(document.getElementById("yiyuan-credit").value);

    var elP = document.getElementById("yiyuan-v-purchase");
    var elC = document.getElementById("yiyuan-v-consume");
    var elT = document.getElementById("yiyuan-v-tokens");
    var elRef = document.getElementById("yiyuan-v-yuan-per-m");
    if (!elP || !elC || !elT || !elRef) return;

    if (!(rmb > 0) || !(credit > 0)) {
      elP.textContent = "—";
      elC.textContent = "—";
      elT.textContent = "—";
      elRef.textContent = "—";
      return;
    }

    var purchasePerYuan = credit / rmb;
    elP.textContent = fmt(purchasePerYuan) + " 额度/元";

    if (!(pUsd >= 0) || !(mult >= 0)) {
      elC.textContent = "—";
      elT.textContent = "—";
      elRef.textContent = "—";
      return;
    }

    var consumePerM = pUsd * mult;
    elC.textContent = fmt(consumePerM) + "（与「官方标价×倍率」同口径的额度/百万）";

    var finalYuanPerM = consumePerM / purchasePerYuan;
    var tokensPerOneYuan =
      finalYuanPerM > 0 ? 1e6 / finalYuanPerM : NaN;
    elT.textContent = fmtTokens(tokensPerOneYuan);
    elRef.textContent = fmt(finalYuanPerM);
  }

  var btn = document.getElementById("yiyuan-calc-btn");
  if (btn) btn.addEventListener("click", calc);
  ["yiyuan-p-usd", "yiyuan-mult", "yiyuan-rmb", "yiyuan-credit"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener("change", calc);
      el.addEventListener("input", function () {
        if (id === "yiyuan-rmb" || id === "yiyuan-credit") return;
        calc();
      });
    }
  });
  calc();
})();
