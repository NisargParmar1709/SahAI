from __future__ import annotations
"""Lightweight smoke tests for journal creation fallback logic.

These are illustrative and may require a configured test client + login helper.
"""
import json
import pytest
from flask import url_for

# NOTE: The real project may already define a create_app fixture.

@pytest.mark.smoke
def test_journal_save_minimal(app, client, auth):  # type: ignore
    auth.login()  # ensure a user session
    resp = client.post('/journal/new', data={'text': 'Feeling calm and focused today.', 'store_raw': 'y'}, follow_redirects=True)
    assert resp.status_code in (200, 302)
    # Should contain either success or fallback toast keywords
    assert b'Entry saved' in resp.data or b'Saved your entry' in resp.data

@pytest.mark.smoke
def test_journal_empty_reject(app, client, auth):  # type: ignore
    auth.login()
    resp = client.post('/journal/new', data={'text': '   '}, follow_redirects=True)
    assert b'Please write something first' in resp.data

# For malformed JSON / AI failure scenarios you could monkeypatch get_ai_client().
