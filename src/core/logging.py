"""llm-router 로깅 (Phase 0)"""
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "llm-router",
            "model": getattr(record, "model", "unknown"),
            "message": record.getMessage(),
        })
