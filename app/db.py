"""Compatibility exports for database query helpers.

Use `app.db.queries` for implementation details.
"""

from app.db.queries import get_user_promo

__all__ = ["get_user_promo"]
