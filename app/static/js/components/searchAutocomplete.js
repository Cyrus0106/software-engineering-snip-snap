/* Reusable search bar with autocomplete + disambiguation.
 *
 * Spec highlights:
 * - items: [{ id: number, type: "tag"|"barber"|"barbershop", label: string }]
 * - minimum characters: 1
 * - matching: case-insensitive contains
 * - limit: 6
 * - no matches: show "No results" (not selectable)
 * - Enter with no highlighted suggestion: do nothing
 * - selection sets input value, calls onSelect(selectedItem), dropdown STAYS OPEN
 * - dropdown closes only when Enter is pressed again while a selected item is in the search bar
 */

(function () {
  const TYPE_ICON_SVG = {
    tag: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M20.59 13.41 12 4.83V2h-2.83L2 9.17V12l8.59 8.59a2 2 0 0 0 2.82 0l7.18-7.18a2 2 0 0 0 0-2.82ZM11.41 19.17 4 11.76V10l6-6h1.76l7.41 7.41-7.76 7.76ZM7.5 7.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z"/>
      </svg>
    `,
    barber: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Z"/>
      </svg>
    `,
    barbershop: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 3 2 9v2h2v10h6v-6h4v6h6V11h2V9L12 3Zm6 16h-2v-6H8v6H6V10.26l6-3.6 6 3.6V19Z"/>
      </svg>
    `,
  };

  function normalise(str) {
    return (str ?? "").toString().trim().toLowerCase();
  }

  function isValidItem(item) {
    return (
      item &&
      typeof item === "object" &&
      typeof item.id === "number" &&
      (item.type === "tag" || item.type === "barber" || item.type === "barbershop") &&
      typeof item.label === "string"
    );
  }

  function createEl(tag, className, attrs = {}) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    for (const [k, v] of Object.entries(attrs)) {
      if (v === undefined || v === null) continue;
      el.setAttribute(k, v);
    }
    return el;
  }

  /**
   * createSearchBarAutocomplete(mountEl, onSelect, items, opts?)
   * - mountEl: DOM element OR selector string
   * - onSelect: function(itemObj) {}
   * - items: array of {id,type,label}
   * - opts: { placeholder?: string }
   */
  function createSearchBarAutocomplete(mountEl, onSelect, items, opts = {}) {
    const mount =
      typeof mountEl === "string" ? document.querySelector(mountEl) : mountEl;

    if (!mount) {
      throw new Error("createSearchBarAutocomplete: mount element not found.");
    }
    if (typeof onSelect !== "function") {
      throw new Error("createSearchBarAutocomplete: onSelect must be a function.");
    }
    if (!Array.isArray(items)) {
      throw new Error("createSearchBarAutocomplete: items must be an array.");
    }

    const cleanItems = items.filter(isValidItem);
    const placeholder = opts.placeholder ?? "Search…";

    // Component state
    let isOpen = false;
    let highlightedIndex = -1; // index within renderedResults
    let selectedItem = null;   // full object when selected
    let renderedResults = [];  // current filtered list (max 6)

    // Build DOM
    const root = createEl("div", "sa-root");
    const field = createEl("div", "sa-field");
    const input = createEl("input", "sa-input", {
      type: "text",
      placeholder,
      autocomplete: "off",
      "aria-autocomplete": "list",
      "aria-expanded": "false",
      "aria-haspopup": "listbox",
    });

    const dropdown = createEl("div", "sa-dropdown", { role: "listbox" });

    field.appendChild(input);
    root.appendChild(field);
    root.appendChild(dropdown);

    mount.innerHTML = "";
    mount.appendChild(root);

    function open() {
      if (isOpen) return;
      isOpen = true;
      input.setAttribute("aria-expanded", "true");
      dropdown.classList.add("is-open");
    }

    function close() {
      if (!isOpen) return;
      isOpen = false;
      highlightedIndex = -1;
      input.setAttribute("aria-expanded", "false");
      dropdown.classList.remove("is-open");
      dropdown.innerHTML = "";
      renderedResults = [];
    }

    function setHighlight(newIndex) {
      highlightedIndex = newIndex;
      const rows = dropdown.querySelectorAll(".sa-item[role='option']");
      rows.forEach((row, idx) => {
        if (idx === highlightedIndex) row.classList.add("is-highlighted");
        else row.classList.remove("is-highlighted");
      });
    }

    function renderNoResults() {
      dropdown.innerHTML = "";
      const row = createEl("div", "sa-item sa-item--empty", { role: "option" });
      row.textContent = "No results";
      dropdown.appendChild(row);
      renderedResults = [];
      highlightedIndex = -1;
      open();
    }

    function renderResults(results) {
      dropdown.innerHTML = "";
      renderedResults = results;

      if (results.length === 0) {
        renderNoResults();
        return;
      }

      results.forEach((item, idx) => {
        const row = createEl("div", "sa-item", { role: "option" });
        row.dataset.index = String(idx);

        const icon = createEl("span", "sa-icon");
        icon.innerHTML = TYPE_ICON_SVG[item.type] ?? "";

        const label = createEl("span", "sa-label");
        label.textContent = item.label;

        // Small type pill to make disambiguation obvious
        const pill = createEl("span", "sa-type");
        pill.textContent = item.type;

        row.appendChild(icon);
        row.appendChild(label);
        row.appendChild(pill);

        row.addEventListener("mousedown", (e) => {
          // mousedown so click doesn't blur input before we select
          e.preventDefault();
          selectItem(item);
          setHighlight(idx);
        });

        row.addEventListener("mousemove", () => {
          setHighlight(idx);
        });

        dropdown.appendChild(row);
      });

      // Keep dropdown open
      open();

      // Default: no highlight until user arrows/moves mouse
      highlightedIndex = -1;
    }

    function filterItems(query) {
      const q = normalise(query);
      if (q.length < 1) return [];
      const results = [];
      for (const it of cleanItems) {
        if (normalise(it.label).includes(q)) {
          results.push(it);
          if (results.length >= 6) break;
        }
      }
      return results;
    }

    function selectItem(item) {
      selectedItem = item;
      input.value = item.label;

      // Call back with full object as requested
      onSelect(item);
        
      // Close selection menu
      close();
    }

    function refresh() {
      const q = input.value ?? "";

      // If user edits after a selection, selection is no longer valid
      if (selectedItem && q !== selectedItem.label) {
        selectedItem = null;
      }

      if (q.trim().length < 1) {
        close();
        return;
      }

      const results = filterItems(q);
      renderResults(results);
    }

    // Input events
    input.addEventListener("input", () => {
      refresh();
    });

    input.addEventListener("focus", () => {
      // Show suggestions when focused if >= 1 char
      if ((input.value ?? "").trim().length >= 1) refresh();
    });

    input.addEventListener("keydown", (e) => {
      if (!isOpen && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
        // Open and render if user starts arrowing
        refresh();
      }

      if (e.key === "ArrowDown") {
        if (!isOpen) return;
        e.preventDefault();
        if (renderedResults.length === 0) return;
        const next = highlightedIndex < renderedResults.length - 1 ? highlightedIndex + 1 : 0;
        setHighlight(next);
      }

      if (e.key === "ArrowUp") {
        if (!isOpen) return;
        e.preventDefault();
        if (renderedResults.length === 0) return;
        const prev = highlightedIndex > 0 ? highlightedIndex - 1 : renderedResults.length - 1;
        setHighlight(prev);
      }

      if (e.key === "Escape") {
        e.preventDefault();
        close();
        input.blur(); // IMPORTANT: prevents immediate re-open
        return;
      }


      if (e.key === "Enter") {
        // Spec:
        // - If Enter with no highlighted suggestion: do nothing
        // - If Enter with highlighted suggestion: fill search lable and close DropDownList

        if (isOpen && highlightedIndex >= 0 && highlightedIndex < renderedResults.length) {
            e.preventDefault();
            selectItem(renderedResults[highlightedIndex]); // now closes
            return;
        }

        // Otherwise do nothing
      }
    });

    document.addEventListener("mousedown", (e) => {
        if (!isOpen) return;

        // If the click is outside the autocomplete component, close it
        if (!root.contains(e.target)) {
            close();
        }
    });


    // Public API (optional, for later)
    return {
      open,
      close,
      setItems(newItems) {
        if (!Array.isArray(newItems)) return;
        items = newItems;
        // refresh using new list
        refresh();
      },
      getSelected() {
        return selectedItem;
      },
    };
  }

  // Expose globally (no bundler)
  window.createSearchBarAutocomplete = createSearchBarAutocomplete;
})();
