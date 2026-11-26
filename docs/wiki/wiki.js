(function boot() {
  "use strict";
  if (!window.WIKI) {
    fetch("data.json").then(function (r) { return r.json(); }).then(function (d) { window.WIKI = d; boot(); })
      .catch(function () { document.getElementById("main").innerHTML = "<h1>資料載入失敗</h1><p>重新整理頁面再試一次。</p>"; });
    return;
  }
  var W = window.WIKI;
  // routes like "item/soul_essence" travel in the hash as "item--soul-essence" (letters, digits, hyphens only);
  // ids never contain "-", so the mapping is reversible. Old "#/item/soul_essence" links still work.
  function enc(r) { return r.replace(/\//g, "--").replace(/_/g, "-"); }
  function dec(h) { return h.charAt(0) === "/" ? h.slice(1) : h.replace(/--/g, "/").replace(/-/g, "_"); }
  function fixLinks(root) {
    [].forEach.call(root.querySelectorAll('a[href^="#/"]'), function (a) { a.setAttribute("href", "#" + enc(a.getAttribute("href").slice(2))); });
  }
  var main = document.getElementById("main");
  var nav = document.getElementById("nav");
  var q = document.getElementById("q");
  var results = document.getElementById("results");

  // ---------------------------------------------------------------- theme (per-viewer convenience only)
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  var saved = store("sift-theme");
  if (saved) document.documentElement.setAttribute("data-theme", saved);
  document.getElementById("theme").onclick = function () {
    var cur = document.documentElement.getAttribute("data-theme");
    if (!cur) cur = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    var next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    store("sift-theme", next);
  };

  // ---------------------------------------------------------------- nav
  nav.innerHTML = W.nav.map(function (n) {
    if (!n[1]) return '<div class="sep"></div>';
    return '<a href="#' + enc(n[1]) + '" data-r="' + n[1] + '">' + n[0] + "</a>";
  }).join("");

  // ---------------------------------------------------------------- router
  fixLinks(document);
  function route() {
    var r = dec(decodeURIComponent((location.hash || "#home").slice(1))) || "home";
    var anchor = null;
    var i = r.indexOf("@");
    if (i > 0) { anchor = r.slice(i + 1); r = r.slice(0, i); }
    var p = W.pages[r];
    if (!p) {
      main.innerHTML = '<h1>找不到頁面</h1><p>沒有「' + esc(r) + '」這一頁。可以用上方的搜尋找看看。</p>';
      document.title = "找不到頁面 - 隙浮 Wiki";
      return;
    }
    main.innerHTML = crumbs(r) + p[1];
    [].forEach.call(main.querySelectorAll(".rcp"), function (d) { d.outerHTML = recipe(W.recipes[+d.getAttribute("data-i")]); });
    fixLinks(main);
    document.title = p[0] + " - 隙浮 Wiki";
    [].forEach.call(nav.querySelectorAll("a"), function (a) {
      var dr = a.getAttribute("data-r");
      var sec = { item: "items", mob: "mobs", biome: "biomes", structure: "structures" }[r.split("/")[0]];
      a.classList.toggle("on", dr === r || dr === sec);
    });
    document.body.classList.remove("nav-open");
    if (anchor) { var el = document.getElementById(anchor); if (el) { el.scrollIntoView(); return; } }
    window.scrollTo(0, 0);
  }
  var KIND = { item: ["物品", "items"], mob: ["生物", "mobs"], biome: ["生態域", "biomes"], structure: ["建築與地形", "structures"], page: null };
  function crumbs(r) {
    var k = r.split("/")[0];
    if (!KIND[k]) return "";
    return '<div class="crumbs"><a href="#home">首頁</a> › <a href="#' + KIND[k][1] + '">' + KIND[k][0] + "</a></div>";
  }
  // ---------------------------------------------------------------- recipes (compact data -> inventory GUI)
  function icon(id, size) {
    var it = W.items[id] || [0, id, 0];
    var n = it[0], c = W.cols;
    var span = '<span class="ic s' + size + '" style="--x:' + (n % c) + ";--y:" + Math.floor(n / c) + '" title="' + esc(it[1]) + '"></span>';
    return it[2] ? '<a href="#/item/' + id.slice(7) + '">' + span + "</a>" : span;
  }
  function slot(ids) {
    if (!ids || !ids.length) return '<span class="slot"></span>';
    return '<span class="slot' + (ids.length > 1 ? " multi" : "") + '">' + ids.map(function (x, k) {
      return '<span class="cyc' + (k ? "" : " on") + '">' + icon(x, 32) + "</span>";
    }).join("") + "</span>";
  }
  function recipe(r) {
    if (!r) return "";
    var lay = r[3], s = r[4], body;
    if (lay === "g") body = '<span class="grid3">' + s.map(slot).join("") + "</span>";
    else if (lay === "r") body = '<span class="row">' + s.map(slot).join("") + "</span>";
    else if (lay === "b") body = '<span class="row">' + slot(s[0]) + '<span class="tag">' + esc(r[6]) + "</span>" + slot(s[1]) + "</span>";
    else body = '<span class="row">' + slot(s[0]) + '<span class="flame"></span>' + (r[6] ? '<span class="tag">' + esc(r[6]) + "</span>" : "") + "</span>";
    var out = '<span class="slot big">' + icon(r[1], 32) + (r[2] > 1 ? '<span class="cnt">' + r[2] + "</span>" : "") + "</span>";
    return '<div class="recipe"><div class="rk">' + esc(r[0]) + '</div><div class="rb">' + body + '<span class="arrow">➜</span>' + out +
      '</div><div class="rn">' + esc(r[5]) + "</div></div>";
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  window.addEventListener("hashchange", route);
  route();

  // ---------------------------------------------------------------- search
  var KLABEL = { item: "物品", mob: "生物", biome: "生態域", structure: "建築", "": "頁面" };
  function search(term) {
    term = term.trim().toLowerCase();
    if (!term) { results.hidden = true; return; }
    var hits = [];
    for (var i = 0; i < W.search.length && hits.length < 40; i++) {
      var s = W.search[i];
      var hay = (s[1] + " " + s[2]).toLowerCase();
      var at = hay.indexOf(term);
      if (at >= 0) hits.push([at === 0 ? 0 : s[1].toLowerCase().indexOf(term) >= 0 ? 1 : 2, s]);
    }
    hits.sort(function (a, b) { return a[0] - b[0] || a[1][1].length - b[1][1].length; });
    results.innerHTML = hits.length ? hits.map(function (h) {
      var s = h[1];
      return '<a href="#' + enc(s[0]) + '"><span class="k">' + (KLABEL[s[3]] || "頁面") + "</span>" + esc(s[1]) + "</a>";
    }).join("") : '<div class="none">找不到符合的結果</div>';
    results.hidden = false;
  }
  q.addEventListener("input", function () { search(q.value); });
  q.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { var a = results.querySelector("a"); if (a) { location.hash = a.getAttribute("href"); q.blur(); results.hidden = true; } }
    if (e.key === "Escape") { results.hidden = true; q.blur(); }
  });
  results.addEventListener("click", function () { results.hidden = true; q.value = ""; });
  document.addEventListener("click", function (e) { if (!e.target.closest(".search")) results.hidden = true; });

  // ---------------------------------------------------------------- cycling ingredients (tags), like the wiki
  setInterval(function () {
    [].forEach.call(document.querySelectorAll(".slot.multi"), function (s) {
      var c = s.querySelectorAll(".cyc");
      for (var i = 0; i < c.length; i++) {
        if (c[i].classList.contains("on")) { c[i].classList.remove("on"); c[(i + 1) % c.length].classList.add("on"); break; }
      }
    });
  }, 1400);
})();
