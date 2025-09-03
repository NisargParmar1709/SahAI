from __future__ import annotations

def assert_unique_endpoints(app):  # pragma: no cover - dev aid
    seen = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint in seen:
            raise AssertionError(f"Duplicate endpoint detected: {rule.endpoint}")
        seen.add(rule.endpoint)
