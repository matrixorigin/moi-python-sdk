"""High-level SDKClient that builds on top of RawClient."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .client import RawClient
from .errors import ErrNilRequest
from .options import CallOption


@dataclass
class TablePrivInfo:
    """Represents table privilege information for role creation/update."""

    table_id: int
    priv_codes: Sequence[str] = field(default_factory=list)
    authority_code_list: Optional[Sequence[Dict[str, Any]]] = None


class SDKClient:
    """High-level convenience client built on top of RawClient."""

    def __init__(self, raw: RawClient):
        if raw is None:
            raise ValueError("RawClient cannot be None")
        self.raw = raw

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------

    def create_table_role(
        self,
        role_name: str,
        comment: str,
        table_privs: Iterable[TablePrivInfo | Dict[str, Any]],
    ) -> tuple[Optional[int], bool]:
        """Create a role dedicated to table privileges, or return the existing ID."""
        if not role_name:
            raise ValueError("role_name is required")

        existing = self._find_role_by_name(role_name)
        if existing:
            return existing.get("id"), False

        obj_priv_list = self._build_obj_priv_list(table_privs)
        payload = {
            "name": role_name,
            "description": comment,
            "authority_code_list": [],
            "obj_authority_code_list": obj_priv_list,
        }
        response = self.raw.create_role(payload)
        return response.get("id") if isinstance(response, dict) else None, True

    def update_table_role(
        self,
        role_id: int,
        comment: str,
        table_privs: Iterable[TablePrivInfo | Dict[str, Any]],
        global_privs: Optional[Sequence[str]],
    ) -> Any:
        """Update role privileges while optionally preserving comment/global privileges."""
        if not role_id:
            raise ValueError("role_id is required")

        current_comment = comment
        priv_list = list(global_privs) if global_privs is not None else None

        if not comment or global_privs is None:
            role_resp = self.raw.get_role({"id": role_id})
            if not role_resp:
                raise ErrNilRequest(f"role {role_id} not found")
            if not comment:
                current_comment = role_resp.get("description", "")
            if global_privs is None:
                authority_list = role_resp.get("authority_list", [])
                priv_list = [item.get("code") for item in authority_list if item.get("code")]

        obj_priv_list = self._build_obj_priv_list(table_privs)
        payload = {
            "id": role_id,
            "description": current_comment or "",
            "authority_code_list": priv_list or [],
            "obj_authority_code_list": obj_priv_list,
        }
        return self.raw.update_role_info(payload)

    def import_local_file_to_table(self, table_config: Dict[str, Any]) -> Any:
        """Import an already uploaded local file into a table using connector upload."""
        if not table_config:
            raise ValueError("table_config is required")

        config = copy.deepcopy(table_config)
        conn_file_ids = config.get("conn_file_ids") or []
        if not conn_file_ids:
            raise ValueError("table_config.conn_file_ids must contain at least one file ID")

        if not config.get("new_table"):
            if not config.get("table_id"):
                raise ValueError("table_config.table_id is required when new_table is False")
            config.setdefault("existed_table", [])

        conn_file_id = conn_file_ids[0]
        meta = [{"filename": conn_file_id, "path": "/"}]

        return self.raw.upload_connector_file(
            "123456",
            None,
            meta=meta,
            table_config=config,
        )

    def run_sql(self, statement: str, *opts: CallOption) -> Any:
        """Run a SQL statement via the NL2SQL RunSQL operation."""
        if not statement or not statement.strip():
            raise ValueError("statement is required")
        payload = {
            "operation": "run_sql",
            "statement": statement,
        }
        return self.raw.run_nl2sql(payload, *opts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_role_by_name(self, role_name: str) -> Optional[Dict[str, Any]]:
        page = 1
        page_size = 100
        max_pages = 1000

        while page <= max_pages:
            request = {
                "keyword": "",
                "common_condition": {
                    "page": page,
                    "page_size": page_size,
                    "order": "desc",
                    "order_by": "created_at",
                    "filters": [
                        {
                            "name": "name_description",
                            "values": [role_name],
                            "fuzzy": True,
                        }
                    ],
                },
            }
            response = self.raw.list_roles(request)
            role_list = []
            total = 0
            if isinstance(response, dict):
                role_list = response.get("role_list") or response.get("list") or []
                total = response.get("total") or 0

            for role in role_list:
                if role.get("name") == role_name:
                    return role

            if len(role_list) < page_size:
                break
            if total and page * page_size >= total:
                break
            page += 1

        return None

    def _build_obj_priv_list(
        self, table_privs: Iterable[TablePrivInfo | Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        obj_priv_list: List[Dict[str, Any]] = []
        for entry in table_privs:
            payload = self._normalize_table_priv(entry)
            if not payload:
                continue
            obj_priv_list.append(payload)
        return obj_priv_list

    @staticmethod
    def _normalize_table_priv(
        entry: TablePrivInfo | Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if entry is None:
            return None

        if is_dataclass(entry):
            data = asdict(entry)
        elif isinstance(entry, dict):
            data = entry
        else:
            raise TypeError("table_privs entries must be TablePrivInfo or dicts")

        table_id = data.get("table_id")
        if not table_id:
            return None

        authority_code_list = data.get("authority_code_list")
        priv_codes = data.get("priv_codes") or []

        if authority_code_list:
            acl = authority_code_list
        elif priv_codes:
            acl = [{"code": code, "rule_list": None} for code in priv_codes]
        else:
            return None

        return {
            "id": str(table_id),
            "category": "table",
            "name": "",
            "authority_code_list": acl,
        }

