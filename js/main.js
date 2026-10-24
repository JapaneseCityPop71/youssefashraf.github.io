/* Youssef Ashraf — site scripts (theme, reveal, petals, posts, cert copy) */
(function () {
  "use strict";

  /* ---------- theme ---------- */
  var root = document.documentElement;
  var themeBtn = document.getElementById("theme");
  var themeLabel = document.getElementById("themelabel");
  function applyTheme(t) {
    root.setAttribute("data-theme", t);
    if (themeLabel) themeLabel.textContent = t === "dark" ? "Light" : "Dark";
    try { localStorage.setItem("theme", t); } catch (e) {}
  }
  var saved = null;
  try { saved = localStorage.getItem("theme"); } catch (e) {}
  // default to dark (Byakuya) unless user already chose light
  applyTheme(saved === "light" ? "light" : "dark");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      applyTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
    });
  }

  /* ---------- scroll reveal ---------- */
  var reveal = document.querySelectorAll("[data-reveal]");
  if (reveal.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    reveal.forEach(function (el) { io.observe(el); });
  } else {
    reveal.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- sakura petals ---------- */
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduced) {
    var count = 14;
    var frag = document.createDocumentFragment();
    for (var i = 0; i < count; i++) {
      var p = document.createElement("span");
      p.className = "petal";
      var size = (6 + Math.random() * 12).toFixed(1);
      p.style.width = size + "px";
      p.style.height = size + "px";
      p.style.left = (Math.random() * 100).toFixed(2) + "%";
      p.style.setProperty("--drift", ((Math.random() * 120 - 60).toFixed(0)) + "px");
      p.style.setProperty("--spin", ((Math.random() * 520 - 260).toFixed(0)) + "deg");
      p.style.animationDuration = (9 + Math.random() * 14).toFixed(1) + "s";
      p.style.animationDelay = (-Math.random() * 20).toFixed(1) + "s";
      p.style.opacity = (0.25 + Math.random() * 0.4).toFixed(2);
      frag.appendChild(p);
    }
    document.body.appendChild(frag);
  }

  /* ---------- footer year ---------- */
  var yr = document.getElementById("yr");
  if (yr) yr.textContent = new Date().getFullYear();

  /* ---------- copy certificate id (index) ---------- */
  var copyBtn = document.getElementById("copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var idEl = document.getElementById("cid");
      if (!idEl) return;
      var done = function () { copyBtn.textContent = "Copied"; setTimeout(function () { copyBtn.textContent = "Copy ID"; }, 1800); };
      try { navigator.clipboard.writeText(idEl.textContent).then(done, function () {}); } catch (e) { done(); }
    });
  }

  /* ---------- writeups list (writeups.html) ---------- */
  var listEl = document.getElementById("list");
  if (listEl) {
    var MONTHS = { Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12 };
    function sortPosts(posts) {
      return posts.slice().sort(function (a, b) {
        function key(s) {
          var m = /^([A-Za-z]{3})\s+(\d{4})$/.exec(s || "");
          return m ? (parseInt(m[2], 10) * 12 + (MONTHS[m[1]] || 0)) : 0;
        }
        return key(b.date) - key(a.date);
      });
    }
    function render(posts) {
      listEl.innerHTML = "";
      if (!posts || !posts.length) {
        listEl.innerHTML = '<p class="lead">No write-ups yet. The first ones are on the way.</p>';
        return;
      }
      sortPosts(posts).forEach(function (p, idx) {
        var a = document.createElement("a");
        a.className = "post-card";
        a.href = p.url;
        a.setAttribute("data-reveal", "");
        a.style.transitionDelay = (idx * 60) + "ms";
        a.innerHTML =
          '<div class="post-top">' +
            '<span class="post-date">' + (p.date || "") + '</span>' +
            '<span class="post-tag">' + (p.tag || "Write-up") + '</span>' +
          '</div>' +
          '<h3>' + escapeHtml(p.title || "Untitled") + '</h3>' +
          '<p>' + escapeHtml(p.summary || "") + '</p>' +
          '<span class="read">Read write-up' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>' +
          '</span>';
        listEl.appendChild(a);
      });
      // reveal the cards we just injected
      var els = listEl.querySelectorAll("[data-reveal]");
      if ("IntersectionObserver" in window) {
        var io2 = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) { e.target.classList.add("in"); io2.unobserve(e.target); }
          });
        }, { threshold: 0.1 });
        els.forEach(function (el) { io2.observe(el); });
      } else {
        els.forEach(function (el) { el.classList.add("in"); });
      }
    }
    function escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
    }
    fetch("posts.json").then(function (r) { return r.ok ? r.json() : null; })
      .then(render)
      .catch(function () { render([]); });
  }
})();
