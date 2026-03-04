const DEFAULT_FILTER_OPTIONS = [
  { id: 2, label: "Most recent" },
  { id: 0, label: "Closest" },
  { id: 1, label: "Highest rated" },
];

export class FilterDropdown {
  constructor({ mountEl, tagList, options = DEFAULT_FILTER_OPTIONS }) {
    this.mountEl = mountEl;
    this.tagList = tagList;
    this.options = Array.isArray(options) ? options : DEFAULT_FILTER_OPTIONS;

    if (!this.mountEl) {
      throw new Error("FilterDropdown: mountEl is required.");
    }
    if (!this.tagList || typeof this.tagList.add_item !== "function") {
      throw new Error("FilterDropdown: valid tagList instance is required.");
    }

    this.render();
  }

  render() {
    this.mountEl.textContent = "";

    const select = document.createElement("select");
    select.className = "filter-dropdown-select";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select filter";
    placeholder.disabled = true;
    placeholder.selected = true;
    select.appendChild(placeholder);

    this.options.forEach((optionData) => {
      const option = document.createElement("option");
      option.value = String(optionData.id);
      option.textContent = optionData.label;
      select.appendChild(option);
    });

    select.addEventListener("change", (event) => {
      const value = Number(event.target.value);
      if (!Number.isFinite(value)) return;

      this.tagList.add_item({
        id: value,
        type: "filter",
      });

      select.selectedIndex = 0;
    });

    this.mountEl.appendChild(select);
  }
}
