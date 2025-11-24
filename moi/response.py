"""Response envelope handling for the MOI SDK."""

from typing import Any, Optional
import json


class APIEnvelope:
    """Represents the API response envelope."""
    
    def __init__(self, code: str = "", msg: str = "", data: Any = None, request_id: str = ""):
        self.code = code
        self.msg = msg
        self.data = data
        self.request_id = request_id
    
    @classmethod
    def from_dict(cls, d: dict) -> 'APIEnvelope':
        """Create an APIEnvelope from a dictionary."""
        return cls(
            code=d.get("code", ""),
            msg=d.get("msg", ""),
            data=d.get("data"),
            request_id=d.get("request_id", "")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'APIEnvelope':
        """Create an APIEnvelope from a JSON string."""
        return cls.from_dict(json.loads(json_str))

