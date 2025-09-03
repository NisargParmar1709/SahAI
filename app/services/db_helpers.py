"""DB helper utilities with safe wrappers and minimal logging.

All helpers avoid logging raw user content. Messages include IDs/lengths only.
"""
from __future__ import annotations
from typing import Any, Optional, Tuple, Type
import logging

from flask import abort
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query

from ..extensions import db

logger = logging.getLogger(__name__)


def safe_add(instance) -> tuple[bool, str | None]:
    """Add an instance to the session with error capture."""
    try:
        db.session.add(instance)
        return True, None
    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        logger.error("safe_add error", extra={"model": type(instance).__name__})
        return False, str(exc)


def safe_commit() -> tuple[bool, str | None]:
    """Commit session safely."""
    try:
        db.session.commit()
        return True, None
    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        logger.error("safe_commit error")
        return False, str(exc)


def safe_delete(instance, *, soft: bool = True) -> tuple[bool, str | None]:
    """Soft-delete if model has `is_deleted`; else hard delete."""
    try:
        if soft and hasattr(instance, "is_deleted"):
            setattr(instance, "is_deleted", True)
        else:
            db.session.delete(instance)
        db.session.commit()
        return True, None
    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        logger.error("safe_delete error", extra={"model": type(instance).__name__})
        return False, str(exc)


def get_or_404(Model: Type, **filters):
    """Fetch a single row or 404."""
    row = Model.query.filter_by(**filters).first()
    if not row:
        abort(404)
    return row


def list_paginated(Model: Type, *, user_id: int | None = None, page: int = 1, per_page: int = 10,
                   order: str = "-created_at"):
    """Generic pagination helper."""
    query: Query = Model.query
    if user_id is not None and hasattr(Model, "user_id"):
        query = query.filter_by(user_id=user_id)
    if order:
        desc = order.startswith("-")
        field = order.lstrip("-")
        if hasattr(Model, field):
            col = getattr(Model, field)
            query = query.order_by(col.desc() if desc else col.asc())
    return query.paginate(page=page, per_page=per_page, error_out=False)
