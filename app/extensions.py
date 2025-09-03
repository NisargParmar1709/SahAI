"""Flask extensions initialized here to avoid circular imports."""
from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
import time
from app.logging_config import get_logger, log_extra_safe
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

limiter = Limiter(key_func=get_remote_address, default_limits=[])

__all__ = ["db", "migrate", "csrf", "login_manager", "limiter"]

log = get_logger("sql")

def init_sql_listeners(app):
	if not app.config.get("SQL_ECHO"):
		return
	engine = db.engine

	@event.listens_for(engine, "before_cursor_execute")
	def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore
		conn.info.setdefault('_query_start_time', []).append(time.time())
		stmt_clean = ' '.join(statement.strip().split())[:120]
		log_extra_safe(log, "debug", "sql_start", extra={"event":"sql_start","stmt_summary":stmt_clean,"params_count":len(parameters) if parameters else 0})

	@event.listens_for(engine, "after_cursor_execute")
	def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore
		start = conn.info.get('_query_start_time').pop(-1) if conn.info.get('_query_start_time') else None
		dur = int((time.time() - start) * 1000) if start else 0
		log_extra_safe(log, "debug", "sql_end", extra={"event":"sql_end","duration_ms":dur,"rowcount":getattr(cursor, 'rowcount', -1)})
