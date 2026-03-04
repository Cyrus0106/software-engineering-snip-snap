/**
 * TagList Component - Reusable Tag Display & Management
 * 
 * A pure UI component that displays a list of removable tags.
 * Supports types: filter, tag, barber, barbershop
 * 
 * Public API:
 *   - add_item(json): Add a tag to the list
 *   - get_items(): Get all current tags as JSON array
 * 
 * Author: MIRZA MD SAKIF SHAHNOOR
 * University of Portsmouth - Group 7E
 */

class TagList {
  constructor(mountElementId) {
    // Internal state - stores all current tags
    this.tags = [];
    
    // Mount point - where this component renders
    this.mountElement = document.getElementById(mountElementId);
    
    if (!this.mountElement) {
      console.error(`TagList: Mount element '${mountElementId}' not found`);
      return;
    }
    
    // Initial render
    this.render();
  }

  /**
   * PUBLIC API: Add a tag to the list
   * @param {Object} tagJson - Must contain {id: number, type: string, label: string}
   * @returns {boolean} - Success status
   * 
   * Example usage:
   *   tagList.add_item({"id": 0, "type": "filter", "label": "closest"})
   */
  add_item(tagJson) {
    // Validate input
    if (!tagJson || typeof tagJson !== 'object') {
      console.error('TagList.add_item: Invalid input - must be JSON object');
      return false;
    }

    if (tagJson.id === undefined || typeof tagJson.id !== 'number') {
      console.error('TagList.add_item: Missing or invalid "id" field (must be a number)');
      return false;
    }

    if (!tagJson.type || typeof tagJson.type !== 'string') {
      console.error('TagList.add_item: Missing or invalid "type" field');
      return false;
    }

    if (!tagJson.label || typeof tagJson.label !== 'string') {
      console.error('TagList.add_item: Missing or invalid "label" field');
      return false;
    }

    // Validate type is one of the supported types
    const validTypes = ['filter', 'tag', 'barber', 'barbershop'];
    if (!validTypes.includes(tagJson.type)) {
      console.error(`TagList.add_item: Invalid type "${tagJson.type}". Must be one of: ${validTypes.join(', ')}`);
      return false;
    }

    // Check for duplicates by ID
    const isDuplicate = this.tags.some(tag => tag.id === tagJson.id);
    
    if (isDuplicate) {
      console.warn('TagList.add_item: Tag with this ID already exists in list');
      return false;
    }

    // Add tag to internal state
    this.tags.push({
      id: tagJson.id,
      type: tagJson.type,
      label: tagJson.label
    });

    // Re-render UI
    this.render();
    
    return true;
  }

  /**
   * PUBLIC API: Get all current tags
   * @returns {Array} - JSON array of all tags with id, type, and label
   * 
   * Example output:
   *   [
   *     {"id": 0, "type": "filter", "label": "closest"},
   *     {"id": 21, "type": "tag", "label": "fade"},
   *     {"id": 23, "type": "barber", "label": "alex_barber"}
   *   ]
   */
  get_items() {
    // Return a copy to prevent external modification
    return this.tags.map(tag => ({
      id: tag.id,
      type: tag.type,
      label: tag.label
    }));
  }

  /**
   * PRIVATE: Remove a tag by index
   * @param {number} index - Index of tag to remove
   */
  _removeTag(index) {
    if (index >= 0 && index < this.tags.length) {
      this.tags.splice(index, 1);
      this.render();
    }
  }

  /**
   * PRIVATE: Get CSS class for tag type (for styling)
   * @param {string} type - Tag type
   * @returns {string} - CSS class name
   */
  _getTagClass(type) {
    const classMap = {
      'filter': 'tag-filter',
      'tag': 'tag-generic',
      'barber': 'tag-barber',
      'barbershop': 'tag-barbershop'
    };
    return classMap[type] || 'tag-default';
  }

  /**
   * PRIVATE: Render the component
   * Updates the DOM with current tag state
   */
  render() {
    if (!this.mountElement) return;

    // Clear existing content
    this.mountElement.innerHTML = '';

    // Create container
    const container = document.createElement('div');
    container.className = 'taglist-container';

    // Render each tag
    this.tags.forEach((tag, index) => {
      const tagElement = document.createElement('div');
      tagElement.className = `taglist-item ${this._getTagClass(tag.type)}`;
      
      // Tag label text
      const labelSpan = document.createElement('span');
      labelSpan.className = 'taglist-label';
      labelSpan.textContent = tag.label;
      
      // Remove button (X)
      const removeBtn = document.createElement('button');
      removeBtn.className = 'taglist-remove';
      removeBtn.textContent = '×';
      removeBtn.setAttribute('aria-label', `Remove ${tag.label} tag`);
      
      // Click handler for remove
      removeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this._removeTag(index);
      });
      
      // Assemble tag element
      tagElement.appendChild(labelSpan);
      tagElement.appendChild(removeBtn);
      container.appendChild(tagElement);
    });

    // Mount to DOM
    this.mountElement.appendChild(container);
  }
}

/**
 * OPTIONAL: Auto-inject basic styles
 * Remove this if you want to use external CSS
 */
(function injectStyles() {
  if (document.getElementById('taglist-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'taglist-styles';
  style.textContent = `
    .taglist-container {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 8px 0;
    }

    .taglist-item {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s ease;
    }

    .taglist-label {
      user-select: none;
    }

    .taglist-remove {
      background: none;
      border: none;
      font-size: 20px;
      line-height: 1;
      cursor: pointer;
      padding: 0;
      margin: 0;
      color: inherit;
      opacity: 0.7;
      transition: opacity 0.2s ease;
    }

    .taglist-remove:hover {
      opacity: 1;
    }

    /* Type-specific styles */
    .tag-filter {
      background: #D4AF37;
      color: #000;
    }

    .tag-generic {
      background: #2A2A2A;
      color: #FFF;
    }

    .tag-barber {
      background: #1A1A1A;
      color: #D4AF37;
      border: 1px solid #D4AF37;
    }

    .tag-barbershop {
      background: #0A0A0A;
      color: #FFF;
      border: 1px solid #2A2A2A;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .taglist-item {
        font-size: 12px;
        padding: 5px 10px;
      }
    }
  `;
  document.head.appendChild(style);
})();

// Export for use in other modules (if using module system)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TagList;
}
