"use strict";

// ===== Platform config =====
const PLATFORM_COLORS = {
  mercari:    "#ff4757",
  rakuma:     "#8e44ad",
  yahoo_flea: "#e74c3c",
};

// ===== State =====
let allItems = [];
let currentSummary = {};

// ===== DOM refs =====
const searchForm      = document.getElementById("searchForm");
const searchInput     = document.getElementById("searchInput");
const searchBtn       = document.getElementById("searchBtn");
const statusMsg       = document.getElementById("statusMsg");
const summarySection  = document.getElementById("summarySection");
const summaryCards    = document.getElementById("summaryCards");
const resultsSection  = document.getElementById("resultsSection");
const itemGrid        = document.getElementById("itemGrid");
const resultCount     = document.getElementById("resultCount");
const filterPlatform  = document.getElementById("filterPlatform");
const sortOrder       = document.getElementById("sortOrder");

// ===== Event listeners =====
searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const keyword = searchInput.value.trim();
  if (keyword) doSearch(keyword);
});

filterPlatform.addEventListener("change", renderItems);
sortOrder.addEventListener("change", renderItems);

// ===== Search =====
async function doSearch(keyword) {
  setLoading(true);
  showStatus(`「${keyword}」を検索中... 🔍`, "loading");
  summarySection.hidden = true;
  resultsSection.hidden = true;
  allItems = [];
  currentSummary = {};

  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(keyword)}`);
    const data = await res.json();

    if (!res.ok) {
      showStatus(data.error || "エラーが発生しました", "error");
      return;
    }

    allItems = data.all_items || [];
    currentSummary = data.summary || {};

    renderSummary();
    renderItems();

    const total = allItems.length;
    if (total === 0) {
      showStatus("検索結果が見つかりませんでした。別のキーワードをお試しください。", "error");
    } else {
      hideStatus();
      summarySection.hidden = false;
      resultsSection.hidden = false;
    }
  } catch (err) {
    console.error(err);
    showStatus("通信エラーが発生しました。ネットワーク接続を確認してください。", "error");
  } finally {
    setLoading(false);
  }
}

// ===== Summary =====
function renderSummary() {
  summaryCards.innerHTML = "";

  for (const [key, info] of Object.entries(currentSummary)) {
    const color = PLATFORM_COLORS[key] || "#666";
    const card = document.createElement("div");
    card.className = "summary-card";
    card.style.setProperty("--accent", color);

    if (info.error) {
      card.innerHTML = `
        <div class="summary-card-header">
          <span class="platform-badge">${info.name}</span>
        </div>
        <p class="summary-error">⚠️ ${info.error}</p>
      `;
    } else {
      card.innerHTML = `
        <div class="summary-card-header">
          <span class="platform-badge">${info.name}</span>
          <span class="summary-count">${info.count} 件</span>
        </div>
        <div class="summary-stats">
          <div class="stat-item">
            <span class="stat-label">最安値</span>
            <span class="stat-value min">${info.min_price_text}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">平均値</span>
            <span class="stat-value avg">${info.avg_price_text}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最高値</span>
            <span class="stat-value max">${info.max_price_text}</span>
          </div>
        </div>
      `;
    }

    summaryCards.appendChild(card);
  }
}

// ===== Items =====
function renderItems() {
  const platformFilter = filterPlatform.value;
  const sort = sortOrder.value;

  let items = [...allItems];

  // Filter
  if (platformFilter !== "all") {
    items = items.filter((it) => it.platform_key === platformFilter);
  }

  // Sort
  if (sort === "price_asc") {
    items.sort((a, b) => a.price - b.price);
  } else if (sort === "price_desc") {
    items.sort((a, b) => b.price - a.price);
  } else if (sort === "platform") {
    items.sort((a, b) => a.platform_key.localeCompare(b.platform_key) || a.price - b.price);
  }

  resultCount.textContent = `${items.length} 件表示`;
  itemGrid.innerHTML = "";

  if (items.length === 0) {
    itemGrid.innerHTML = '<p style="color:#888;grid-column:1/-1;text-align:center;padding:32px 0;">該当する商品が見つかりませんでした。</p>';
    return;
  }

  for (const item of items) {
    itemGrid.appendChild(buildCard(item));
  }
}

function buildCard(item) {
  const color = PLATFORM_COLORS[item.platform_key] || "#666";

  const a = document.createElement("a");
  a.className = "item-card";
  a.href = item.url || "#";
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.style.setProperty("--accent", color);

  const imgHtml = item.image
    ? `<img class="item-img" src="${escHtml(item.image)}" alt="${escHtml(item.name)}" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.hidden=false;" /><div class="item-img-placeholder" hidden>🛍️</div>`
    : `<div class="item-img-placeholder">🛍️</div>`;

  const condHtml = item.condition
    ? `<span class="item-condition">${escHtml(item.condition)}</span>`
    : "";

  a.innerHTML = `
    <div class="item-img-wrap">
      ${imgHtml}
      <span class="item-platform-tag">${escHtml(item.platform)}</span>
    </div>
    <div class="item-body">
      <p class="item-name">${escHtml(item.name)}</p>
      <p class="item-price">${escHtml(item.price_text)}</p>
      ${condHtml}
    </div>
  `;

  return a;
}

// ===== Helpers =====
function setLoading(on) {
  searchBtn.disabled = on;
  searchBtn.querySelector(".btn-text").hidden = on;
  searchBtn.querySelector(".btn-spinner").hidden = !on;
}

function showStatus(msg, type) {
  statusMsg.textContent = msg;
  statusMsg.className = `container status-msg ${type}`;
  statusMsg.hidden = false;
  if (type === "loading") {
    statusMsg.classList.add("loading-text");
  }
}

function hideStatus() {
  statusMsg.hidden = true;
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
