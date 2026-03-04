# User Promo Component

This module provides a reusable component for displaying user promotions, including their avatar, name, and barbershop name if applicable.

## Functions

### `mountUserPromo(containerEl, userId, options?)`
- **Parameters:**
  - `containerEl`: The DOM element to mount the promo.
  - `userId`: The ID of the user to fetch promo data for.
  - `options`: Optional settings for customization.

### `initUserPromos(root=document)`
- **Parameters:**
  - `root`: The root element to search for promo elements.

## Usage
1. Include this module in your project.
2. Call `initUserPromos()` to automatically mount promos for elements with the class `.js-user-promo` and a `data-user-id` attribute.
