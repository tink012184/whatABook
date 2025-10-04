
(() => {
  if (window.getJSON) return;

  const API_BASE = (() => {
    const configured = (window.API_BASE || "").replace(/\/+$/, "");
    if (configured) return configured;
    const origin = window.location.origin;
    if (origin === "null" || origin.startsWith("file:"))
      return "http://127.0.0.1:5000";
    return origin.replace(/\/+$/, "");
  })();
  window.API_BASE = API_BASE;

  window.getJSON = async function (path) {
    const url = path.startsWith("http")
      ? path
      : `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
    let res;
    try {
      res = await fetch(url, { headers: { Accept: "application/json" } });
    } catch (err) {
      throw new Error(`Network error to ${url}: ${err.message}`);
    }
    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(
        `HTTP ${res.status} ${res.statusText} for ${url}\n${txt.slice(0, 200)}`
      );
    }
    return res.json();
  };
})();

// scripts.js - API-backed version
function $(sel) {
  return document.querySelector(sel);
}
function $all(sel) {
  return Array.from(document.querySelectorAll(sel));
}
function renderYear() {
  $all("#year").forEach((el) => (el.textContent = new Date().getFullYear()));
}
renderYear();

async function searchTitle() {
  const q = ($("#search")?.value || "").trim();
  const url = q ? `/api/books?title=${encodeURIComponent(q)}` : `/api/books`;
  const res = await fetch(url);
  const data = await res.json();
  const el = $("#results");
  if (!el) return;
  el.innerHTML = "";
  if (!data.length) {
    el.innerHTML = "<p>No results. Try another title.</p>";
    return;
  }
  data.forEach((b) => el.appendChild(renderItem(b)));
}
window.searchTitle = searchTitle;

let __BOOKS = [];
let __GENRES = [];

async function initGenresPage() {
  try {
    // Load all books once
    __BOOKS = await getJSON("/api/books");

    // Build unique, sorted genres
    __GENRES = [...new Set(__BOOKS.map((b) => b.genre).filter(Boolean))].sort(
      (a, b) => a.localeCompare(b)
    );

    buildAlphaNav(__GENRES);
    buildGenreGroups(__GENRES);

    // NEW: show placeholder instead of auto-selecting first genre
    const panelTitle = document.getElementById("bookPanelTitle");
    const results = document.getElementById("bookResults");
    if (panelTitle) panelTitle.textContent = "Pick a genre";
    if (results) {
      results.innerHTML = `<p class="muted">Select a genre from the middle column.</p>`;
    }

    // (no auto-call to showGenre)
    // if (__GENRES.length) showGenre(__GENRES[0]);  <-- REMOVE this line
  } catch (err) {
    console.error("Failed to initialize genres page:", err);
    const gg = document.getElementById("genreGroups");
    if (gg) gg.innerHTML = `<p>${err.message}</p>`;
  }
}

function buildAlphaNav(genres) {
  const nav = document.getElementById("alphaNav");
  if (!nav) return;
  nav.innerHTML = "";
  const letters = Array.from("ABCDEFGHIJKLMNOPQRSTUVWXYZ");
  const present = new Set(genres.map((g) => g[0].toUpperCase()));
  letters.forEach((L) => {
    const a = document.createElement("a");
    a.textContent = L;
    if (present.has(L)) a.href = `#letter-${L}`;
    else {
      a.setAttribute("aria-disabled", "true");
      a.href = "javascript:void(0)";
    }
    nav.appendChild(a);
  });
}

function buildGenreGroups(genres) {
  const container = document.getElementById("genreGroups");
  if (!container) return;
  container.innerHTML = "";
  const groups = genres.reduce((acc, g) => {
    const L = g[0].toUpperCase();
    (acc[L] ||= []).push(g);
    return acc;
  }, {});
  Object.keys(groups)
    .sort()
    .forEach((L) => {
      const section = document.createElement("section");
      section.className = "genre-group";
      section.id = `letter-${L}`;
      const h = document.createElement("h3");
      h.textContent = L;
      section.appendChild(h);
      const ul = document.createElement("div");
      ul.className = "genre-list";
      groups[L].forEach((g) => {
        const a = document.createElement("a");
        a.href = "#";
        a.className = "genre-link";
        a.textContent = g;
        a.setAttribute("data-genre", g);
        a.addEventListener("click", (e) => {
          e.preventDefault();
          showGenre(g);
          document
            .querySelectorAll('.genre-link[aria-current="true"]')
            .forEach((el) => el.setAttribute("aria-current", "false"));
          a.setAttribute("aria-current", "true");
        });
        ul.appendChild(a);
      });
      section.appendChild(ul);
      container.appendChild(section);
    });
}

function showGenre(g) {
  const panelTitle = document.getElementById("bookPanelTitle");
  const results = document.getElementById("bookResults");
  if (!results) return;

  panelTitle && (panelTitle.textContent = `Books — ${g}`);

  const books = __BOOKS
    .filter((b) => b.genre === g)
    .sort((a, b) => a.title.localeCompare(b.title));

  results.innerHTML = "";
  if (!books.length) {
    results.innerHTML = `<p>No books in "${g}".</p>`;
    return;
  }

  books.forEach((b) => {
    const div = document.createElement("div");
    div.className = "book-item";
    div.innerHTML = `
      <strong>${b.title}</strong><br/>
      <span>${b.author}</span><br/>
      <small>ID: ${b.bookId}</small>
    `;

    // Add-to-wishlist button
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn--accent";
    btn.textContent = "Add to wishlist";
    btn.addEventListener("click", async () => {
      // Optional UX: disable while adding
      const oldLabel = btn.textContent;
      btn.disabled = true;
      btn.textContent = "Adding…";
      try {
        await addToWishlist(b.bookId); // uses your existing function
        btn.textContent = "Added ✓";
      } catch (e) {
        console.error(e);
        btn.textContent = oldLabel;
        btn.disabled = false;
        alert("Could not add to wishlist. Please try again.");
      }
    });

    div.appendChild(document.createElement("br"));
    div.appendChild(btn);
    results.appendChild(div);
  });
}

window.initGenresPage = initGenresPage;

const DEMO_CUSTOMER = "c1007";
const w = $("#wishlist");
if (w) {
  renderWishlist();
}

function renderItem(b) {
  const div = document.createElement("div");
  div.className = "item";
  div.innerHTML = `<strong>${b.title}</strong><br/>${b.author} — ${b.genre}<br/><small>ID: ${b.bookId}</small>`;
  const btn = document.createElement("button");
  btn.textContent = "Add to wishlist";
  btn.addEventListener("click", () => addToWishlist(b.bookId));
  div.appendChild(document.createElement("br"));
  div.appendChild(btn);
  return div;
}

async function addToWishlist(bookId) {
  await fetch(`/api/wishlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customerId: DEMO_CUSTOMER, bookId }),
  });
  alert("Added to wishlist");
  renderWishlist();
}

async function removeFromWishlist(bookId) {
  await fetch(`/api/wishlist`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customerId: DEMO_CUSTOMER, bookId }),
  });
  alert("Removed from wishlist");
  renderWishlist();
}

async function renderWishlist() {
  const el = $("#wishlist");
  if (!el) return;
  const res = await fetch(`/api/wishlist?customerId=${DEMO_CUSTOMER}`);
  const items = await res.json();
  el.innerHTML = "";
  if (!items.length) {
    el.innerHTML = "<p>Your wishlist is empty.</p>";
    return;
  }
  items.forEach((b) => {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `<strong>${b.title}</strong><br/>${b.author} — ${b.genre}<br/><small>ID: ${b.bookId}</small>`;
    const btn = document.createElement("button");
    btn.textContent = "Remove";
    btn.addEventListener("click", () => removeFromWishlist(b.bookId));
    div.appendChild(document.createElement("br"));
    div.appendChild(btn);
    el.appendChild(div);
  });
}
