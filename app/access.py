"""
Route protection decorators for the Snip-Snap Flask application.

Provides :func:`login_required` and :func:`roles_required` which can be
applied to any Flask view to enforce authentication and role-based access
control using the Flask session.
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable

from flask import session, redirect, url_for, abort


def current_role() -> str | None:
    """Return the role string of the currently logged-in user, or ``None``."""
    user = session.get("user") or {}
    return user.get("role")


def login_required(view: Callable):
    """Decorator that redirects unauthenticated requests to the login page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def roles_required(*allowed_roles: str):
    """
    Decorator factory that restricts a view to users with one of the given roles.

    Args:
        *allowed_roles: Role strings (e.g. ``"barber"``, ``"customer"``) that
            are permitted to access the decorated view.

    Returns:
        A decorator that returns 403 for authenticated users without the
        required role, or redirects to login for unauthenticated users.
    """
    allowed = set(allowed_roles)

    def decorator(view: Callable):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for("login"))

            role = user.get("role")
            if role not in allowed:
                return abort(403)

            return view(*args, **kwargs)
        return wrapper
    return decorator