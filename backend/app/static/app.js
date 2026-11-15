/* Nexora web reader — vanilla JS, no build step. */

const state = {
  category: "top",
  query: "",
  articles: [],
  categories: [],
  updatedAt: null,
  live: false,
  total: 0,
  loading: false,
};

const els = {
  topics: document.getElementById("topics"),
  hero: document.getElementById("hero"),
  grid: document.getElementById("grid"),
  title: document.getElementById("feedTitle"),
  meta: document.getElementById("feedMeta"),
  empty: document.getElementById("empty"),
  feedView: document.getElementById("feedView"),
  story: document.getElementById("story"),
  dateline: document.getElementById("dateline"),
  footerMeta: document.getElementById("footerMeta"),
  searchToggle: document.getElementById("searchToggle"),
  searchBar: document.getElementById("searchBar"),
  searchInput: document.getElementById("searchInput"),
  searchClear: document.getElementById("searchClear"),
  progress: document.getElementById("progress"),
};

const TOPIC_LABELS = {
  top: "Latest dispatches",
  world: "World",
  tech: "Technology",
  science: "Science",
  business: "Business",
  culture: "Culture",
};

/* ------------------------------------------------------------------ utils */
const escapeHtml = (value = "") =>
  String(value).replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])
  );

const hueFor = (id = "") => {
  let hash = 0;
  for (const char of String(id)) hash = (hash * 31 + char.charCodeAt(0)) % 360;
  return hash;
};

function timeAgo(iso) {
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "";
  const seconds = Math.max(0, (Date.now() - then.getTime()) / 1000);
  if (seconds < 90) return "just now";
  if (seconds < 3600) return `${Math.round(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)} h ago`;
  if (seconds < 604800) return `${Math.round(seconds / 86400)} d ago`;
  return then.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function clock(iso) {
  const value = new Date(iso || "");
  if (Number.isNaN(value.getTime())) return "";
  return value.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function mediaMarkup(article, className) {
  const image = article.image
    ? `<img src="${escapeHtml(article.image)}" alt="" loading="lazy" decoding="async"
         referrerpolicy="no-referrer" onload="this.classList.add('is-loaded')"
         onerror="this.remove()">`
    : "";
  return `<div class="media ${className}" style="--h:${hueFor(article.id)}">${image}</div>`;
}

const metaLine = (article) =>
  `${escapeHtml(article.source || "Nexora")} · ${timeAgo(article.publishedAt || article.published_at)} · ${article.read_minutes ?? article.readMinutes ?? 2} min`;

/* ------------------------------------------------------------------ render */
function renderTopics() {
  els.topics.innerHTML = state.categories
    .map((topic) => {
      const active = topic.id === state.category ? " is-active" : "";
      return `<button class="topic${active}" type="button" data-topic="${escapeHtml(topic.id)}">
        ${escapeHtml(topic.label)}<span class="topic__count">${topic.count ?? ""}</span>
      </button>`;
    })
    .join("");
}

function cardMarkup(article) {
  return `<a class="card" href="#/story/${encodeURIComponent(article.id)}">
    ${mediaMarkup(article, "card__media")}
    <p class="kicker">${escapeHtml(article.category_label || article.categoryLabel || "News")}<span>${escapeHtml(article.source || "")}</span></p>
    <h3 class="card__title">${escapeHtml(article.title)}</h3>
    <p class="card__summary">${escapeHtml(article.summary)}</p>
    <p class="card__meta">${metaLine(article)}</p>
  </a>`;
}

function heroMarkup(article) {
  return `<a class="hero__story" href="#/story/${encodeURIComponent(article.id)}">
    <div class="hero__copy">
      <span class="hero__flag">Lead story</span>
      <h1 class="hero__title">${escapeHtml(article.title)}</h1>
      <p class="hero__summary">${escapeHtml(article.summary)}</p>
      <span class="hero__cta">Read the story
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg>
      </span>
    </div>
    ${mediaMarkup(article, "hero__media")}
  </a>`;
}

function renderFeed() {
  const searching = Boolean(state.query.trim());
  const [lead, ...rest] = state.articles;

  els.title.textContent = searching
    ? `Results for “${state.query.trim()}”`
    : TOPIC_LABELS[state.category] || "Latest dispatches";

  els.meta.textContent = state.total
    ? `${state.total} ${state.total === 1 ? "story" : "stories"}${state.updatedAt ? ` · updated ${clock(state.updatedAt)}` : ""}`
    : "";

  if (!state.articles.length) {
    els.hero.innerHTML = "";
    els.grid.innerHTML = "";
    els.empty.hidden = false;
    els.empty.innerHTML = searching
      ? `<strong>Nothing matches “${escapeHtml(state.query.trim())}”</strong>Try a broader word, or browse another topic above.`
      : `<strong>No stories in this topic yet</strong>Pull the latest edition from the newsroom and try again.
         <br><button type="button" id="emptyRetry">Refresh edition</button>`;
    const retry = document.getElementById("emptyRetry");
    if (retry) retry.addEventListener("click", () => loadFeed({ skeleton: true }));
    return;
  }

  els.empty.hidden = true;
  els.hero.innerHTML = searching || !lead ? "" : heroMarkup(lead);
  els.grid.innerHTML = (searching ? state.articles : rest).map(cardMarkup).join("");
  els.footerMeta.textContent = state.live
    ? `Live edition · ${state.total} stories from the newsroom · refreshed ${clock(state.updatedAt)}`
    : "Offline edition · bundled sample stories (feeds unreachable)";
}

function renderSkeleton() {
  els.hero.innerHTML = "";
  els.empty.hidden = true;
  els.grid.classList.add("skeleton");
  els.grid.innerHTML = Array.from({ length: 6 })
    .map(
      () => `<div class="card">
        <div class="card__media"></div>
        <div class="skeleton-line is-short"></div>
        <div class="skeleton-line is-title"></div>
        <div class="skeleton-line"></div>
        <div class="skeleton-line is-short"></div>
      </div>`
    )
    .join("");
}

function renderError(message) {
  els.grid.classList.remove("skeleton");
  els.hero.innerHTML = "";
  els.grid.innerHTML = "";
  els.empty.hidden = false;
  els.empty.innerHTML = `<strong>The newsroom is unreachable</strong>
    ${escapeHtml(message)}<br>
    <button type="button" id="emptyRetry">Try again</button>`;
  const retry = document.getElementById("emptyRetry");
  if (retry) retry.addEventListener("click", () => loadFeed({ skeleton: true }));
}

/* ------------------------------------------------------------------ loading */
async function loadFeed({ skeleton = false } = {}) {
  if (state.loading) return;
  state.loading = true;
  els.grid.classList.remove("skeleton");
  if (skeleton) renderSkeleton();

  try {
    const params = new URLSearchParams({ category: state.category, limit: "60" });
    const query = state.query.trim();
    if (query) params.set("q", query);

    const response = await fetch(`/api/articles?${params.toString()}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    state.articles = data.articles || [];
    state.categories = data.categories || [];
    state.updatedAt = data.updated_at;
    state.live = Boolean(data.live);
    state.total = data.total ?? state.articles.length;

    renderTopics();
    renderFeed();
  } catch (error) {
    renderError(error.message || "Request failed");
  } finally {
    state.loading = false;
    els.grid.classList.remove("skeleton");
  }
}

/* ------------------------------------------------------------------ story view */
function storyMarkup(article) {
  const body = (article.body || []).length
    ? article.body.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")
    : `<p>${escapeHtml(article.summary)}</p>`;

  const source = escapeHtml(article.source || "Nexora");
  const original = article.url
    ? `<a class="button" href="${escapeHtml(article.url)}" target="_blank" rel="noreferrer noopener">
         Read at ${source}
         <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg>
       </a>`
    : "";

  return `<a class="back" href="#/">Back to the front page</a>
    <p class="story__kicker">${escapeHtml(article.category_label || article.categoryLabel || "News")} · ${source}</p>
    <h1 class="story__title">${escapeHtml(article.title)}</h1>
    <p class="story__lead">${escapeHtml(article.summary)}</p>
    <div class="story__byline">
      <span>${timeAgo(article.published_at)}</span>
      <span>${article.read_minutes} min read</span>
      ${article.url ? `<a class="ghost-link" href="${escapeHtml(article.url)}" target="_blank" rel="noreferrer noopener">Original at ${source}</a>` : ""}
    </div>
    ${article.image ? mediaMarkup(article, "story__media") : ""}
    <div class="story__body">${body}</div>
    <div class="story__end">
      ${original}
      <p>Aggregated by the Nexora engine. Headlines and summaries belong to their publishers.</p>
    </div>`;
}

async function showStory(id) {
  els.feedView.hidden = true;
  els.story.hidden = false;
  els.story.innerHTML = `<a class="back" href="#/">Back to the front page</a>
    <div class="skeleton"><div class="skeleton-line is-short"></div>
    <div class="skeleton-line is-title" style="height:38px;margin:18px 0"></div>
    <div class="skeleton-line"></div></div>`;

  let article = state.articles.find((item) => item.id === id) || null;

  if (!article) {
    try {
      const response = await fetch(`/api/articles/${encodeURIComponent(id)}`);
      if (!response.ok) throw new Error("not found");
      article = await response.json();
    } catch {
      article = null;
    }
  }

  if (!article) {
    els.story.innerHTML = `<a class="back" href="#/">Back to the front page</a>
      <div class="empty"><strong>That story has moved</strong>
      It may have dropped out of the current edition.
      <br><button type="button" onclick="location.hash='#/'">Back to the front page</button></div>`;
    return;
  }

  els.story.innerHTML = storyMarkup(article);
  document.title = `${article.title} — Nexora`;
  window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  updateProgress();
}

function showFeed() {
  els.story.hidden = true;
  els.feedView.hidden = false;
  els.story.innerHTML = "";
  els.progress.style.setProperty("--p", "0%");
  document.title = "Nexora — a quieter read of the day";
}

function updateProgress() {
  if (els.story.hidden) {
    els.progress.style.setProperty("--p", "0%");
    return;
  }
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const ratio = scrollable > 0 ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0;
  els.progress.style.setProperty("--p", `${(ratio * 100).toFixed(2)}%`);
}

/* ------------------------------------------------------------------ routing */
function route() {
  const match = location.hash.match(/^#\/story\/(.+)$/);
  if (match) {
    showStory(decodeURIComponent(match[1]));
  } else {
    showFeed();
  }
}

/* ------------------------------------------------------------------ wiring */
els.topics.addEventListener("click", (event) => {
  const button = event.target.closest("[data-topic]");
  if (!button) return;
  state.category = button.dataset.topic;
  renderTopics();
  if (location.hash.startsWith("#/story/")) location.hash = "#/";
  loadFeed({ skeleton: true });
});

els.searchToggle.addEventListener("click", () => {
  const open = els.searchBar.hidden;
  els.searchBar.hidden = !open;
  els.searchToggle.setAttribute("aria-expanded", String(open));
  if (open) els.searchInput.focus();
  else clearSearch();
});

els.searchClear.addEventListener("click", () => {
  els.searchInput.value = "";
  clearSearch();
  els.searchInput.focus();
});

let searchTimer;
els.searchInput.addEventListener("input", () => {
  const value = els.searchInput.value;
  els.searchClear.hidden = !value;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.query = value;
    if (location.hash.startsWith("#/story/")) location.hash = "#/";
    loadFeed({ skeleton: true });
  }, 280);
});

function clearSearch() {
  els.searchInput.value = "";
  els.searchClear.hidden = true;
  if (!state.query) return;
  state.query = "";
  loadFeed({ skeleton: true });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    if (els.searchBar.hidden) els.searchToggle.click();
    else els.searchInput.focus();
  }
  if (event.key === "Escape" && !els.searchBar.hidden) {
    els.searchToggle.click();
  }
});

window.addEventListener("scroll", updateProgress, { passive: true });
window.addEventListener("hashchange", route);

/* ------------------------------------------------------------------ boot */
els.dateline.textContent = new Date().toLocaleDateString(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
});

loadFeed({ skeleton: true }).then(route);
