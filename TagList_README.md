# TagList Component - Documentation

## Overview
A reusable, pure UI component for displaying and managing removable tags. Built for the SnipSnap barber discovery app.

**Author:** MIRZA MD SAKIF SHAHNOOR
**Project:** SnipSnap - Group 7E, University of Portsmouth  
**Component Type:** UI



## Quick Start

### 1. Include the component
```html
<script src="TagList.js"></script>
```

### 2. Create mount point in HTML
```html
<div id="myTagList"></div>
```

### 3. Initialize
```javascript
const tagList = new TagList('myTagList');
```

### 4. Use it
```javascript
// Add tags
tagList.add_item({"id": 0, "type": "filter", "label": "closest"});
tagList.add_item({"id": 21, "type": "tag", "label": "fade"});

// Get all tags
const currentTags = tagList.get_items();
console.log(currentTags);
// Output: [{"id":0,"type":"filter","label":"closest"}, {"id":21,"type":"tag","label":"fade"}]
```

---

## Public API

### `add_item(json)`
Adds a tag to the list.

**Parameters:**
- `json` (Object): Must contain `id` (number), `type` (string), and `label` (string)

**Returns:**
- `boolean`: `true` if successful, `false` if validation fails

**Supported Types:**
- `"filter"` - Filter tags (e.g., id: 0 = "closest", id: 1 = "highest rated")
- `"tag"` - Generic tags (e.g., id: 21 for specific tags like "fade", "curly hair")
- `"barber"` - Barber tags (e.g., id: 23 for barber filter)
- `"barbershop"` - Barbershop tags (e.g., id: 12 for barbershop filter)

**Example:**
```javascript
tagList.add_item({"id": 21, "type": "tag", "label": "fade"});
tagList.add_item({"id": 23, "type": "barber", "label": "alex_barber"});
```

**Validation:**
- Checks if input is valid JSON object
- Validates `id` field exists and is a number
- Validates `type` and `label` fields exist and are strings
- Ensures `type` is one of the 4 supported types
- Prevents duplicate IDs (can't add tag with same ID twice)

---

### `get_items()`
Returns all current tags as a JSON array.

**Parameters:** None

**Returns:**
- `Array`: JSON array of tag objects, each with `id`, `type`, and `label`

**Example:**
```javascript
const tags = tagList.get_items();
console.log(tags);
// Output: [
//   {"id": 0, "type": "filter", "label": "closest"},
//   {"id": 21, "type": "tag", "label": "fade"}
// ]
```

---

## Integration Examples

### Example 1: Discover Page Filters
```javascript
// User selects a filter from dropdown
function onFilterSelected(filterId, filterLabel) {
  tagList.add_item({
    "id": filterId,
    "type": "filter",
    "label": filterLabel
  });
  
  // Get all active filters to send to backend
  const activeFilters = tagList.get_items();
  
  // Send to backend (handled by backend team)
  // updateDiscoverFeed(activeFilters);
}
```

### Example 2: Search Bar Tag Addition
```javascript
// User types a tag in search bar and hits enter
searchInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    const tagLabel = e.target.value.trim();
    
    tagList.add_item({
      "id": 21,  // Generic tag ID
      "type": "tag",
      "label": tagLabel
    });
    
    e.target.value = ''; // Clear input
  }
});
```

### Example 3: Following a Barber
```javascript
// User clicks "Follow" button on barber profile
function followBarber(barberId, barberName) {
  tagList.add_item({
    "id": barberId,
    "type": "barber",
    "label": barberName
  });
  
  // Get followed barbers to filter discover feed
  const followedBarbers = tagList.get_items()
    .filter(tag => tag.type === 'barber');
}
```

---

## Styling

### Default Styling
The component includes built-in styles that match the SnipSnap urban streetwear aesthetic:
- Dark mode colors (blacks, golds, whites)
- Gold accent for filter tags
- Different colors for each tag type
- Smooth hover/remove animations
- Mobile responsive

### Custom Styling
To use your own CSS, remove the auto-injected styles section from `TagList.js` and target these classes:

```css
.taglist-container   /* Main container */
.taglist-item        /* Individual tag */
.taglist-label       /* Tag label text */
.taglist-remove      /* Remove button (X) */

/* Type-specific classes */
.tag-filter         /* Filter tags */
.tag-generic        /* Generic tags */
.tag-barber         /* Barber tags */
.tag-barbershop     /* Barbershop tags */
```

---

## Component Scope & Responsibility

### What it DOES:
- Manages internal tag state
- Renders tags with remove buttons
- Handles add/remove interactions
- Exposes public API for external use
- Validates input data

### What it DOES NOT do:
- Make backend API calls
- Contain filtering logic
- Perform search operations
- Handle business logic
- Store data persistently (state resets on page refresh)

---

## File Structure
```
TagList.js           - Main component file
TagList_Demo.html    - Demo page with usage examples
README.md           - This documentation
```

---

## Browser Support
- Chrome/Edge
- Firefox
- Safari
- Mobile browsers

**Requirements:** ES6+ support (modern browsers)

---

## Testing the Component

### Manual Testing
1. Open `TagList_Demo.html` in a browser
2. Click "Add Filter Tag" - should display gold tag
3. Click "Add Generic Tag" - should display gray tag
4. Click "Add Barber Tag" - should display gold-bordered tag
5. Click X on any tag - should remove immediately
6. Click "Get All Tags" - check console for JSON output

### Integration Testing
```javascript
// Test 1: Add valid tag
console.assert(
  tagList.add_item({"id": 0, "type": "filter", "label": "test"}) === true,
  "Should add valid tag"
);

// Test 2: Reject invalid type
console.assert(
  tagList.add_item({"id": 99, "type": "invalid", "label": "test"}) === false,
  "Should reject invalid type"
);

// Test 3: Get items returns array
console.assert(
  Array.isArray(tagList.get_items()),
  "get_items should return array"
);

// Test 4: Prevent duplicate IDs
tagList.add_item({"id": 21, "type": "tag", "label": "fade"});
const beforeCount = tagList.get_items().length;
tagList.add_item({"id": 21, "type": "tag", "label": "different_label"});
const afterCount = tagList.get_items().length;
console.assert(
  beforeCount === afterCount,
  "Should prevent duplicate IDs"
);
```

---

## Troubleshooting

### Tags not displaying
- Check if mount element ID is correct
- Verify `TagList.js` is loaded before initialization
- Check browser console for errors

### Styles not applying
- Ensure auto-inject styles section is present in `TagList.js`
- Check for CSS conflicts with existing styles
- Verify no `!important` rules overriding component styles

### Remove button not working
- Check browser console for JavaScript errors
- Ensure clicks aren't being blocked by parent elements
- Verify event listeners are attached (inspect element)

---

## Future Enhancements (Optional)
- Drag-and-drop reordering
- Tag grouping by type
- Keyboard navigation support
- Animation on add/remove
- Maximum tag limit
- Persistent storage (localStorage)

---

## Specification Compliance

**All requirements met:**
-  Displays a list of tags with name + "X"
-  Supports types: filter, tag, barber, barbershop
-  Clicking "X" removes the tag
-  `add_item(JSON)` adds a tag
-  `get_items()` returns all tags as JSON
-  No backend calls or business logic

---

## Contact & Support
**Component Owner:** Database Team  
**Project:** SnipSnap - Group 7E  
**University:** University of Portsmouth

For questions or issues, contact the database team lead or raise an issue in the project's GitHub repository.

---

**Last Updated:** February 27, 2026  