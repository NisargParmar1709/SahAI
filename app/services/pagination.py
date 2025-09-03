"""Simple pagination helpers + Jinja snippet example (see README)."""
from __future__ import annotations
from math import ceil


def page_meta(total_items: int, page: int, per_page: int) -> dict:
    total_pages = max(1, ceil(total_items / max(1, per_page)))
    return {
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }


# Jinja snippet example to render Bootstrap pagination:
PAGINATION_SNIPPET = """
<nav aria-label="Page navigation">
  <ul class="pagination">
    <li class="page-item {{ 'disabled' if not meta.has_prev }}">
      <a class="page-link" href="{{ url_for(request.endpoint, page=meta.page-1, **request.view_args) }}">Prev</a>
    </li>
    <li class="page-item disabled"><span class="page-link">Page {{ meta.page }} / {{ meta.total_pages }}</span></li>
    <li class="page-item {{ 'disabled' if not meta.has_next }}">
      <a class="page-link" href="{{ url_for(request.endpoint, page=meta.page+1, **request.view_args) }}">Next</a>
    </li>
  </ul>
</nav>
""".strip()
