// 복붙 코드블록에 복사 버튼 자동 부착. file:// 환경도 지원(execCommand 폴백).
(function () {
  function flash(btn, msg) {
    var prev = "복사";
    btn.textContent = msg;
    setTimeout(function () { btn.textContent = prev; }, 1200);
  }
  function copyText(text, btn) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(
        function () { flash(btn, "복사됨 ✓"); },
        function () { legacy(text, btn); }
      );
    } else {
      legacy(text, btn);
    }
  }
  function legacy(text, btn) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      flash(btn, "복사됨 ✓");
    } catch (e) {
      flash(btn, "실패");
    }
    document.body.removeChild(ta);
  }
  document.querySelectorAll("pre").forEach(function (pre) {
    var wrap = document.createElement("div");
    wrap.className = "pre-wrap";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.textContent = "복사";
    btn.addEventListener("click", function () {
      var code = pre.querySelector("code");
      copyText(code ? code.innerText : pre.innerText, btn);
    });
    wrap.appendChild(btn);
  });
})();
