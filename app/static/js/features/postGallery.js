import { renderPostImageCard } from "../components/postImageCard.js";

function normaliseTagListItems(items) {
  const filter_ids = [];
  const tag_ids = [];
  const barber_ids = [];
  const barbershop_ids = [];

  for (const it of items || []) {
    if (!it || typeof it.id !== "number" || typeof it.type !== "string") continue;

    if (it.type === "filter") filter_ids.push(it.id);
    if (it.type === "tag") tag_ids.push(it.id);
    if (it.type === "barber") barber_ids.push(it.id);
    if (it.type === "barbershop") barbershop_ids.push(it.id);
  }

  return {
    filter_ids,
    tag_ids,
    barber_ids,
    barbershop_ids
  };
}

function resolveEffectiveSort(filter_ids) {
  const set = new Set(filter_ids || []);

  const hasClosest = set.has(0);
  const hasHighestRated = set.has(1);
  const hasMostRecent = set.has(2);

  const selectedCount =
    (hasClosest ? 1 : 0) +
    (hasHighestRated ? 1 : 0) +
    (hasMostRecent ? 1 : 0);

  if (selectedCount === 0) return "most_recent";
  if (selectedCount > 1) return "blended";
  if (hasClosest) return "closest";
  if (hasHighestRated) return "highest_rated";
  return "most_recent";
}

async function fetchPosts({ endpoint, payload }) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return await res.json();
}

function createGalleryLoader() {
  const el = document.createElement("div");
  el.className = "postGalleryLoader";
  el.hidden = true;
  el.innerHTML = `
    <div class="postGalleryLoader__spinner" aria-hidden="true"></div>
    <div class="postGalleryLoader__text">Loading…</div>
  `;
  return el;
}

export function initPostGallery({ mountEl, sentinelEl, tagList, config }) {
  const state = {
    items: [],
    cursor: null,
    has_more: true,
    loading: false,
    error: null,
    lastPayloadKey: ""
  };

  const endpoint = (config && config.endpoint) || "/api/gallery/posts";
  const columns = (config && config.columns) || 3;
  const limit = (config && config.limit) || 18;

  let gridEl = null;

  const loaderEl = createGalleryLoader();

  if (sentinelEl && sentinelEl.parentNode) {
    sentinelEl.parentNode.insertBefore(loaderEl, sentinelEl);
  } else {
    mountEl.parentNode?.appendChild(loaderEl);
  }

  function setLoadingVisible(visible) {
    loaderEl.hidden = !visible;
  }

  function getOrCreateGrid() {
    if (!gridEl || !mountEl.contains(gridEl)) {
      mountEl.innerHTML = "";
      gridEl = document.createElement("div");
      gridEl.className = "galleryGrid";
      gridEl.style.setProperty("--gallery-columns", String(columns));
      mountEl.appendChild(gridEl);
    }
    return gridEl;
  }

  function appendItemsToGrid(newItems) {
    const grid = getOrCreateGrid();
    for (const item of newItems) {
      const cell = document.createElement("div");
      cell.className = "galleryGrid__cell";
      cell.appendChild(renderPostImageCard(item));
      grid.appendChild(cell);
    }
  }

  function render() {
    if (state.error) {
      mountEl.innerHTML = "";
      gridEl = null;
      const p = document.createElement("p");
      p.textContent = "Could not load posts. Refresh or adjust filters.";
      mountEl.appendChild(p);
      return;
    }

    if (!state.loading && state.items.length === 0) {
      mountEl.innerHTML = "";
      gridEl = null;
      const emptyState = document.createElement("div");
      emptyState.className = "empty-state";
      const title = document.createElement("h2"); title.textContent = "No cuts found";
      const message = document.createElement("p"); message.textContent = "Try removing a filter or searching for a nearby barber.";
      emptyState.appendChild(title); emptyState.appendChild(message);
      mountEl.appendChild(emptyState); return;
    }
    }
  }

  function buildPayload({ cursor }) {
    const tagItems = tagList.get_items();
    const parts = normaliseTagListItems(tagItems);
    const effective_sort = resolveEffectiveSort(parts.filter_ids);

    return {
      filter_ids: parts.filter_ids,
      effective_sort,
      tag_ids: parts.tag_ids,
      barber_ids: parts.barber_ids,
      barbershop_ids: parts.barbershop_ids,
      cursor: cursor,
      offset: state.items.length,
      limit: limit
    };
  }

  function payloadKey(payload) {
    const keyObj = {
      filter_ids: payload.filter_ids.slice().sort((a, b) => a - b),
      effective_sort: payload.effective_sort,
      tag_ids: payload.tag_ids.slice().sort((a, b) => a - b),
      barber_ids: payload.barber_ids.slice().sort((a, b) => a - b),
      barbershop_ids: payload.barbershop_ids.slice().sort((a, b) => a - b),
      limit: payload.limit
    };
    return JSON.stringify(keyObj);
  }

  async function loadFirstPage() {
    state.loading = true;
    state.error = null;
    state.items = [];
    state.cursor = null;
    state.has_more = true;
    gridEl = null;

    setLoadingVisible(true);

    const payload = buildPayload({ cursor: null });
    state.lastPayloadKey = payloadKey(payload);

    try {
      const data = await fetchPosts({ endpoint, payload });
      state.items = Array.isArray(data.items) ? data.items : [];
      state.cursor = data.next_cursor || null;
      state.has_more = !!data.has_more;
    } catch (e) {
      state.error = e;
    } finally {
      state.loading = false;
      setLoadingVisible(false);

      const skeleton = document.getElementById("gallerySkeleton");
      if (skeleton) skeleton.remove();


      render();
      if (!state.error) appendItemsToGrid(state.items);
    }
  }

  async function loadNextPage() {
    if (state.loading || !state.has_more) return;

    const payload = buildPayload({ cursor: state.cursor });
    const key = payloadKey(payload);

    if (key !== state.lastPayloadKey) return;

    state.loading = true;
    state.error = null;

    setLoadingVisible(true);

    try {
      const data = await fetchPosts({ endpoint, payload });
      const newItems = Array.isArray(data.items) ? data.items : [];
      state.items = state.items.concat(newItems);
      state.cursor = data.next_cursor || null;
      state.has_more = !!data.has_more;
      appendItemsToGrid(newItems);
    } catch (e) {
      state.error = e;
      render();
    } finally {
      state.loading = false;
      setLoadingVisible(false);
    }
  }

  tagList.on_change(() => {
    loadFirstPage();
  });

  const io = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) loadNextPage();
    }
  });

  io.observe(sentinelEl);

  loadFirstPage();

  return {
    reload: loadFirstPage
  };
}
