"""High-level SDKClient that builds on top of RawClient."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, IO, Union

from .client import RawClient
from .errors import ErrNilRequest
from .options import CallOption
from .models import DedupConfig


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
    
    def with_special_user(self, api_key: str) -> "SDKClient":
        """
        Create a new SDKClient with the same configuration but a different API key.
        
        The cloned client uses a cloned RawClient with the new API key.
        Raises ValueError if the API key is empty.
        
        Args:
            api_key: The new API key to use
            
        Returns:
            A new SDKClient instance with the new API key
            
        Example:
            original = SDKClient(RawClient("https://api.example.com", "original-key"))
            new_client = original.with_special_user("new-key")
        """
        cloned_raw = self.raw.with_special_user(api_key)
        return SDKClient(cloned_raw)

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

    def import_local_file_to_volume(
        self,
        file_path: str,
        volume_id: str,
        meta: Dict[str, str],
        dedup: Optional[Union[DedupConfig, Dict[str, Any]]] = None,
        *opts: CallOption,
    ) -> Any:
        """
        Upload a local unstructured file to a target volume.
        
        This is a high-level convenience method that uploads a local file to a volume
        with metadata and deduplication configuration.
        
        Parameters:
            file_path: the local file path to upload (required)
            volume_id: the target volume ID (required)
            meta: file metadata describing the file location in the target volume (required)
                Format: {"filename": "file.docx", "path": "file.docx"}
            dedup: deduplication configuration (optional)
                Can be a DedupConfig object or a dict: {"by": ["name", "md5"], "strategy": "skip"}
        
        Returns:
            Response from the upload operation
        
        Example:
            from moi.models import new_dedup_config_skip_by_name_and_md5
            
            resp = sdk_client.import_local_file_to_volume(
                "/path/to/file.docx",
                "123456",
                {"filename": "file.docx", "path": "file.docx"},
                new_dedup_config_skip_by_name_and_md5()
            )
            print(f"Uploaded file: {resp.get('file_id')}")
        """
        if not file_path or not file_path.strip():
            raise ValueError("file_path is required")
        if not volume_id:
            raise ValueError("volume_id is required")
        if not meta or not meta.get("filename"):
            raise ValueError("meta.filename is required")
        
        # Convert DedupConfig to dict if needed
        dedup_dict = None
        if dedup is not None:
            if isinstance(dedup, DedupConfig):
                dedup_dict = asdict(dedup)
            elif isinstance(dedup, dict):
                dedup_dict = dedup
            else:
                raise TypeError("dedup must be a DedupConfig object or a dict")
        
        # Open the local file
        from pathlib import Path
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Open file and keep it open until upload completes
        file_handle = path.open("rb")
        try:
            # Build file upload items
            file_items = [(file_handle, path.name)]
            
            # Wrap meta in an array as required by upload_connector_file
            meta_list = [meta]
            
            # Call the raw client's upload_connector_file method
            return self.raw.upload_connector_file(
                volume_id,
                *opts,
                file_items=file_items,
                meta=meta_list,
                dedup_config=dedup_dict,
            )
        finally:
            # Close file handle after upload completes
            try:
                file_handle.close()
            except Exception:
                pass

    def import_local_files_to_volume(
        self,
        file_paths: List[str],
        volume_id: str,
        metas: Optional[List[Dict[str, str]]] = None,
        dedup: Optional[Union[DedupConfig, Dict[str, Any]]] = None,
        *opts: CallOption,
    ) -> Any:
        """
        Upload multiple local unstructured files to a target volume.
        
        This is a high-level convenience method that uploads multiple local files to a volume
        with metadata and deduplication configuration.
        
        Parameters:
            file_paths: array of local file paths to upload (required, must not be empty)
            volume_id: the target volume ID (required)
            metas: array of file metadata describing the file locations in the target volume (optional)
                If provided, must have the same length as file_paths.
                If empty or None, metadata will be auto-generated from file paths.
                Format: [{"filename": "file1.docx", "path": "file1.docx"}, ...]
            dedup: deduplication configuration (optional, applied to all files)
                Can be a DedupConfig object or a dict: {"by": ["name", "md5"], "strategy": "skip"}
        
        Returns:
            Response from the upload operation
        
        Example:
            from moi.models import new_dedup_config_skip_by_name_and_md5
            
            resp = sdk_client.import_local_files_to_volume(
                ["/path/to/file1.docx", "/path/to/file2.docx"],
                "123456",
                [
                    {"filename": "file1.docx", "path": "file1.docx"},
                    {"filename": "file2.docx", "path": "file2.docx"},
                ],
                new_dedup_config_skip_by_name_and_md5()
            )
            print(f"Uploaded files, task_id: {resp.get('task_id')}")
        """
        if not file_paths or len(file_paths) == 0:
            raise ValueError("at least one file path is required")
        if not volume_id:
            raise ValueError("volume_id is required")
        
        # Convert DedupConfig to dict if needed
        dedup_dict = None
        if dedup is not None:
            if isinstance(dedup, DedupConfig):
                dedup_dict = asdict(dedup)
            elif isinstance(dedup, dict):
                dedup_dict = dedup
            else:
                raise TypeError("dedup must be a DedupConfig object or a dict")
        
        # Validate metas if provided
        if metas is not None and len(metas) > 0 and len(metas) != len(file_paths):
            raise ValueError(
                f"metas array length ({len(metas)}) must match file_paths length ({len(file_paths)})"
            )
        
        # Open all files and build file upload items
        from pathlib import Path
        
        file_items: List[Tuple[IO[bytes], str]] = []
        meta_list: List[Dict[str, str]] = []
        file_handles: List[IO[bytes]] = []
        
        try:
            for i, file_path in enumerate(file_paths):
                if not file_path or not file_path.strip():
                    raise ValueError(f"file_path[{i}] is empty")
                
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                # Open the local file
                file_handle = path.open("rb")
                file_handles.append(file_handle)
                
                # Extract filename from path
                file_name = path.name
                
                # Build file upload item
                file_items.append((file_handle, file_name))
                
                # Build meta - use provided meta or auto-generate from file path
                if metas and i < len(metas) and metas[i].get("filename"):
                    # Use provided meta
                    meta_list.append(metas[i])
                else:
                    # Auto-generate meta from file path
                    meta_list.append({"filename": file_name, "path": file_name})
            
            # Call the raw client's upload_connector_file method
            return self.raw.upload_connector_file(
                volume_id,
                *opts,
                file_items=file_items,
                meta=meta_list,
                dedup_config=dedup_dict,
            )
        finally:
            # Close all opened files
            for handle in file_handles:
                try:
                    handle.close()
                except Exception:
                    pass

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

