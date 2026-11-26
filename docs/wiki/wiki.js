(function () {
  "use strict";
  // Data comes as data.zh.js / data.en.js (script tags: works from file:// and GitHub Pages) or, on the claude.ai page,
  // as data.<lang>.json fetched beside the page (window.WIKI_FETCH).
  var UI = {
    zh: { search: "搜尋隙浮 Wiki", nav: "導覽", game: "遊戲內容", toc: "目錄", home: "首頁", notFound: "找不到頁面",
      notFoundText: "沒有這一頁。可以用上方的搜尋找看看。", noHits: "找不到符合的結果", loadFail: "資料載入失敗，請重新整理頁面。",
      kinds: { item: "物品", mob: "生物", biome: "生態域", structure: "建築", "": "頁面" },
      lists: { item: ["物品", "items"], mob: ["生物", "mobs"], biome: ["生態域", "biomes"], structure: ["建築與地形", "structures"] },
      foot: "本 Wiki 由模組資料自動產生（tools/wiki/build_wiki.py）。", source: "原始碼", menu: "導覽選單", theme: "切換深色／淺色",
      brand: "隙浮 Wiki", other: "English" },
    en: { search: "Search the Sift Wiki", nav: "Navigation", game: "Game content", toc: "Contents", home: "Home",
      notFound: "Page not found", notFoundText: "There is no such page. Try the search box above.", noHits: "No results",
      loadFail: "Could not load the wiki data. Reload the page.",
      kinds: { item: "Item", mob: "Mob", biome: "Biome", structure: "Structure", "": "Page" },
      lists: { item: ["Items", "items"], mob: ["Mobs", "mobs"], biome: ["Biomes", "biomes"], structure: ["Structures and terrain", "structures"] },
      foot: "This wiki is generated from the mod's data (tools/wiki/build_wiki.py).", source: "Source code",
      menu: "Navigation menu", theme: "Switch dark / light", brand: "The Sift Wiki", other: "中文" }
  };
  var REPO = "https://github.com/PrYuan05/the-sift-pryuan-version";
  var main = document.getElementById("main");
  var nav = document.getElementById("nav");
  var q = document.getElementById("q");
  var results = document.getElementById("results");
  var W = null, T = UI.zh, lang = "zh";

  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  // routes like "item/soul_essence" travel in the hash as "item--soul-essence" (letters, digits, hyphens only);
  // ids never contain "-", so the mapping is reversible. Old "#/item/soul_essence" links still work.
  function enc(r) { return r.replace(/\//g, "--").replace(/_/g, "-"); }
  function dec(h) { return h.charAt(0) === "/" ? h.slice(1) : h.replace(/--/g, "/").replace(/-/g, "_"); }
  function fixLinks(root) {
    [].forEach.call(root.querySelectorAll('a[href^="#/"]'), function (a) { a.setAttribute("href", "#" + enc(a.getAttribute("href").slice(2))); });
  }

  // ---------------------------------------------------------------- theme (a per-viewer convenience)
  var savedTheme = store("sift-theme");
  if (savedTheme) document.documentElement.setAttribute("data-theme", savedTheme);
  document.getElementById("theme").onclick = function () {
    var cur = document.documentElement.getAttribute("data-theme");
    if (!cur) cur = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    var next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    store("sift-theme", next);
  };
  document.getElementById("menu").onclick = function () { document.body.classList.toggle("nav-open"); };

  // ---------------------------------------------------------------- language
  function load(l, done) {
    var D = window.WIKI_DATA || (window.WIKI_DATA = {});
    if (D[l]) return done(D[l]);
    if (window.WIKI_FETCH) {
      fetch("data." + l + ".json").then(function (r) { return r.json(); }).then(function (d) { D[l] = d; done(d); })
        .catch(function () { main.innerHTML = "<p>" + UI[l].loadFail + "</p>"; });
      return;
    }
    var s = document.createElement("script");
    s.src = "data." + l + ".js";
    s.onload = function () { done(D[l]); };
    s.onerror = function () { main.innerHTML = "<p>" + UI[l].loadFail + "</p>"; };
    document.head.appendChild(s);
  }
  function setLang(l) {
    load(l, function (d) {
      W = d; lang = l; T = UI[l];
      store("sift-lang", l);
      document.documentElement.lang = l === "zh" ? "zh-Hant" : "en";
      document.getElementById("lang").textContent = T.other;
      document.getElementById("lang").title = T.other;
      document.getElementById("brand").textContent = T.brand;
      document.getElementById("menu").setAttribute("aria-label", T.menu);
      document.getElementById("theme").setAttribute("aria-label", T.theme);
      document.getElementById("theme").title = T.theme;
      q.placeholder = T.search;
      q.setAttribute("aria-label", T.search);
      nav.setAttribute("aria-label", T.nav);
      var logo = W.items["pysift:soul_crystal_block"];
      var n = logo ? logo[0] : 0;
      document.getElementById("logo").setAttribute("style", "--x:" + (n % W.cols) + ";--y:" + Math.floor(n / W.cols));
      buildNav();
      document.getElementById("foot").innerHTML = esc(T.foot) + ' <a href="' + REPO + '">' + esc(T.source) + "</a>";
      route();
    });
  }
  document.getElementById("lang").onclick = function () { setLang(lang === "zh" ? "en" : "zh"); };

  // ---------------------------------------------------------------- nav (MediaWiki-style portlets)
  function buildNav() {
    var groups = [[T.nav, []]], g = groups[0];
    W.nav.forEach(function (n) {
      if (!n[1]) { g = [T.game, []]; groups.push(g); return; }
      g[1].push('<a href="#' + enc(n[1]) + '" data-r="' + n[1] + '">' + esc(n[0]) + "</a>");
    });
    nav.innerHTML = groups.map(function (g) { return '<div class="portlet"><h3>' + esc(g[0]) + "</h3>" + g[1].join("") + "</div>"; }).join("");
  }

  // ---------------------------------------------------------------- router
  function route() {
    if (!W) return;
    var r = dec(decodeURIComponent((location.hash || "#home").slice(1))) || "home";
    var p = W.pages[r];
    if (!p) {
      main.innerHTML = "<h1>" + T.notFound + "</h1><p>" + T.notFoundText + "</p>";
      document.title = T.notFound + " - " + T.brand;
      return;
    }
    main.innerHTML = crumbs(r) + p[1] + navbox(r);
    [].forEach.call(main.querySelectorAll(".rcp"), function (d) { d.outerHTML = recipe(W.recipes[+d.getAttribute("data-i")]); });
    fixLinks(main);
    toc();
    document.title = r === "home" ? T.brand : p[0] + " - " + T.brand;
    var sec = { item: "items", mob: "mobs", biome: "biomes", structure: "structures" }[r.split("/")[0]];
    [].forEach.call(nav.querySelectorAll("a"), function (a) {
      var dr = a.getAttribute("data-r");
      a.classList.toggle("on", dr === r || dr === sec);
    });
    document.body.classList.remove("nav-open");
    window.scrollTo(0, 0);
  }
  function crumbs(r) {
    var l = T.lists[r.split("/")[0]];
    if (!l) return "";
    return '<div class="crumbs"><a href="#home">' + T.home + '</a> › <a href="#' + l[1] + '">' + esc(l[0]) + "</a></div>";
  }
  // table of contents, MediaWiki style, for pages with three or more sections
  function toc() {
    var hs = [].filter.call(main.querySelectorAll("h2, h3"), function (h) { return !h.closest(".infobox, .navbox"); });
    if (hs.filter(function (h) { return h.tagName === "H2"; }).length < 3) return;
    var a = 0, b = 0, items = "";
    hs.forEach(function (h, i) {
      h.id = "s" + i;
      if (h.tagName === "H2") { a++; b = 0; items += '<li><a href="#" data-t="s' + i + '"><span class="tn">' + a + "</span>" + esc(h.textContent) + "</a></li>"; }
      else { b++; items += '<li class="sub"><a href="#" data-t="s' + i + '"><span class="tn">' + a + "." + b + "</span>" + esc(h.textContent) + "</a></li>"; }
    });
    var box = document.createElement("div");
    box.className = "toc";
    box.innerHTML = '<div class="toc-t">' + T.toc + "</div><ul>" + items + "</ul>";
    var first = hs[0];
    first.parentNode.insertBefore(box, first);
    box.addEventListener("click", function (e) {
      var t = e.target.closest("a");
      if (t) { e.preventDefault(); document.getElementById(t.getAttribute("data-t")).scrollIntoView(); }
    });
  }
  // navbox at the foot of mob / biome / structure pages: every page of that kind
  function navbox(r) {
    var k = r.split("/")[0], l = T.lists[k];
    if (!l || k === "item") return "";
    var links = W.search.filter(function (s) { return s[3] === k; }).map(function (s) {
      return s[0] === r ? "<b>" + esc(s[1]) + "</b>" : '<a href="#' + enc(s[0]) + '">' + esc(s[1]) + "</a>";
    });
    return '<table class="navbox"><tr><th><a href="#' + l[1] + '">' + esc(l[0]) + "</a></th></tr><tr><td>" + links.join(" · ") + "</td></tr></table>";
  }

  // ---------------------------------------------------------------- recipes (compact data -> inventory GUI)
  function icon(id, size) {
    var it = W.items[id] || [0, id, 0];
    var n = it[0], c = W.cols;
    var span = '<span class="ic s' + size + '" style="--x:' + (n % c) + ";--y:" + Math.floor(n / c) + '" title="' + esc(it[1]) + '"></span>';
    return it[2] ? '<a href="#' + enc("item/" + id.slice(7)) + '">' + span + "</a>" : span;
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

  // ---------------------------------------------------------------- search (titles in both languages)
  function search(term) {
    term = term.trim().toLowerCase();
    if (!term || !W) { results.hidden = true; return; }
    var hits = [];
    for (var i = 0; i < W.search.length && hits.length < 40; i++) {
      var s = W.search[i];
      var hay = (s[1] + " " + s[2]).toLowerCase();
      if (hay.indexOf(term) >= 0) hits.push([s[1].toLowerCase().indexOf(term) === 0 ? 0 : s[1].toLowerCase().indexOf(term) > 0 ? 1 : 2, s]);
    }
    hits.sort(function (a, b) { return a[0] - b[0] || a[1][1].length - b[1][1].length; });
    results.innerHTML = hits.length ? hits.map(function (h) {
      var s = h[1];
      return '<a href="#' + enc(s[0]) + '"><span class="k">' + (T.kinds[s[3]] || T.kinds[""]) + "</span>" + esc(s[1]) + "</a>";
    }).join("") : '<div class="none">' + T.noHits + "</div>";
    results.hidden = false;
  }
  q.addEventListener("input", function () { search(q.value); });
  q.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { var a = results.querySelector("a"); if (a) { location.hash = a.getAttribute("href"); q.blur(); results.hidden = true; q.value = ""; } }
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

  window.addEventListener("hashchange", route);
  var start = store("sift-lang") || ((navigator.language || "").toLowerCase().indexOf("zh") === 0 ? "zh" : "en");
  setLang(start === "en" ? "en" : "zh");
})();
