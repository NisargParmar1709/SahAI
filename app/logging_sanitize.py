from __future__ import annotations
import json
import datetime as _dt
from typing import Any, Mapping

_RESERVED = {
    "name","msg","args","levelname","levelno","pathname","filename","module",
    "exc_info","exc_text","stack_info","lineno","funcName","created","msecs",
    "relativeCreated","thread","threadName","processName","process","message"
}

def _jsonable(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (str,int,float,bool,dict,list)):
        return val
    if isinstance(val, (_dt.date,_dt.datetime)):
        return val.isoformat()
    try:
        json.dumps(val)
        return val
    except Exception:
        return str(val)

def sanitize_extra(extra: Mapping[str, Any] | None, prefix: str = "x_") -> dict[str, Any]:
    if not extra:
        return {}
    out: dict[str, Any] = {}
    for k,v in extra.items():
        key = k if k not in _RESERVED else f"{prefix}{k}"
        out[key] = _jsonable(v)
    return out
