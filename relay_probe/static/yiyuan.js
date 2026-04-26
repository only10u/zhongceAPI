/**
 * 一元模型页：实付 元/百万Token 计算器
 */
(function () {
  function fmt(n) {
    if (n == null || !isFinite(n)) return "—";
    if (Math.abs(n) >= 100) return n.toFixed(2);
    if (Math.abs(n) >= 1) return n.toFixed(3);
    return n.toFixed(4);
  }

  function calc() {
    var pUsd = parseFloat(document.getElementById("yiyuan-p-usd").value);
    var mult = parseFloat(document.getElementById("yiyuan-mult").value);
    var rmb = parseFloat(document.getElementById("yiyuan-rmb").value);
    var credit = parseFloat(document.getElementById("yiyuan-credit").value);

    var elP = document.getElementById("yiyuan-v-purchase");
    var elC = document.getElementById("yiyuan-v-consume");
    var elF = document.getElementById("yiyuan-v-final");
    if (!elP || !elC || !elF) return;

    if (!(rmb > 0) || !(credit > 0)) {
      elP.textContent = "—";
      elC.textContent = "—";
      elF.textContent = "—";
      return;
    }

    var purchasePerYuan = credit / rmb;
    elP.textContent = fmt(purchasePerYuan) + " 额度/元";

    if (!(pUsd >= 0) || !(mult >= 0)) {
      elC.textContent = "—";
      elF.textContent = "—";
      return;
    }

    var consumePerM = pUsd * mult;
    elC.textContent = fmt(consumePerM) + "（与「官方标价×倍率」同口径的额度/百万）";

    var finalYuan = consumePerM / purchasePerYuan;
    elF.textContent = fmt(finalYuan);
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
