export class TagList {
  constructor({ mountEl, initialItems = [] }) {
    if (!mountEl) throw new Error("TagList requires mountEl");
    this.mountEl = mountEl;
    this.items = Array.isArray(initialItems) ? initialItems.slice() : [];
    this._listeners = new Set();
    this.render();
  }

  get_items() {
    return this.items.slice();
  }

  set_items(items) {
    this.items = Array.isArray(items) ? items.slice() : [];
    this.render();
    this._emitChange();
  }

  on_change(fn) {
    if (typeof fn === "function") this._listeners.add(fn);
    return () => this._listeners.delete(fn);
  }

  add_item(item) {
    if (!item || typeof item.id !== "number" || typeof item.type !== "string") return;
    this.items.push({ id: item.id, type: item.type });
    this.render();
    this._emitChange();
  }

  remove_item_at(index) {
    if (index < 0 || index >= this.items.length) return;
    this.items.splice(index, 1);
    this.render();
    this._emitChange();
  }

  render() {
    this.mountEl.innerHTML = "";

    const container = document.createElement("div");
    container.className = "taglist";

    if (this.items.length === 0) {
      const empty = document.createElement("p");
      empty.textContent = "No filters/tags selected.";
      container.appendChild(empty);
      this.mountEl.appendChild(container);
      return;
    }

    const ul = document.createElement("ul");
    ul.style.listStyle = "none";
    ul.style.padding = "0";
    ul.style.margin = "0";
    ul.style.display = "flex";
    ul.style.flexWrap = "wrap";
    ul.style.gap = "8px";

    this.items.forEach((item, idx) => {
      const li = document.createElement("li");
      li.style.display = "inline-flex";
      li.style.alignItems = "center";
      li.style.gap = "6px";
      li.style.border = "1px solid #ccc";
      li.style.borderRadius = "999px";
      li.style.padding = "4px 10px";

      const text = document.createElement("span");
      text.textContent = `${item.type}:${item.id}`;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "×";
      btn.setAttribute("aria-label", `Remove ${item.type}:${item.id}`);
      btn.style.border = "none";
      btn.style.background = "transparent";
      btn.style.cursor = "pointer";
      btn.style.fontSize = "16px";
      btn.addEventListener("click", () => this.remove_item_at(idx));

      li.appendChild(text);
      li.appendChild(btn);
      ul.appendChild(li);
    });

    container.appendChild(ul);
    this.mountEl.appendChild(container);
  }

  _emitChange() {
    const snapshot = this.get_items();
    for (const fn of this._listeners) fn(snapshot);
  }
}