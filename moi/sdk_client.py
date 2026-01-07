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


class ExistedTableOption:
    """Constants for existing table import options."""
    APPEND = "append"      # Append new data to the existing table
    OVERWRITE = "overwrite"  # Overwrite the existing table with new data


@dataclass
class ExistedTableOptions:
    """
    Options for importing data into an existing table.
    
    This specifies how to handle data when importing into an existing table:
    - append: Append new data to the table (default behavior)
    - overwrite: Overwrite the table with new data
    
    Example:
        opts = ExistedTableOptions(method=ExistedTableOption.APPEND)
        table_config = {
            "new_table": False,
            "table_id": 123,
            "database_id": 456,
            "conn_file_ids": ["file-id"],
            "existed_table_opts": opts
        }
    """
    method: str = ExistedTableOption.APPEND  # "append" or "overwrite", default is "append" (empty string also means "append")


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
        """
        Import an already uploaded local file into a table using connector upload.
        
        ExistedTableOptions Usage:
            from moi import ExistedTableOption, ExistedTableOptions
            
            # Append to existing table
            config = {
                "new_table": False,
                "table_id": 123,
                "database_id": 456,
                "conn_file_ids": ["file-id"],
                "existed_table": [],
                "existed_table_opts": ExistedTableOptions(method=ExistedTableOption.APPEND)
            }
            sdk.import_local_file_to_table(config)
        """
        if not table_config:
            raise ValueError("table_config is required")

        config = copy.deepcopy(table_config)
        conn_file_ids = config.get("conn_file_ids") or []
        if not conn_file_ids:
            raise ValueError("table_config.conn_file_ids must contain at least one file ID")

        if not config.get("new_table"):
            if not config.get("table_id"):
                raise ValueError("table_config.table_id is required when new_table is False")
            # Initialize existed_table to empty list if it's None or doesn't exist
            if config.get("existed_table") is None:
                config["existed_table"] = []
            else:
                config.setdefault("existed_table", [])
            
            # Convert ExistedTableOptions to dict if needed
            if "existed_table_opts" in config and isinstance(config["existed_table_opts"], ExistedTableOptions):
                config["existed_table_opts"] = asdict(config["existed_table_opts"])

        conn_file_id = conn_file_ids[0]
        meta = [{"filename": conn_file_id, "path": "/"}]

        return self.raw.upload_connector_file(
            "123456",
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

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def find_files_by_name(
        self,
        file_name: str,
        volume_id: str,
        *opts: CallOption,
    ) -> Any:
        """
        Search for files by name within a specific volume.
        
        This is a high-level convenience method that uses list_files with filters
        to find files matching the given file name in the specified volume.
        The search is performed in the root directory (parent_id is empty).
        
        Args:
            file_name: The file name to search for (required)
            volume_id: The volume ID to search within (required)
            *opts: Optional call configuration options
        
        Returns:
            FileListResponse dict containing matching files
        
        Example:
            resp = sdk.find_files_by_name("许继电气：关于召开2", "019b39fc-f4ee-7915-b701-66ae6a48d9fc")
            for file in resp.get("list", []):
                print(f"Found file: {file['name']} (ID: {file['id']})")
        """
        if not file_name or not file_name.strip():
            raise ValueError("file_name is required")
        if not volume_id or not volume_id.strip():
            raise ValueError("volume_id is required")
        
        # Build the request with filters matching the provided JSON example
        req = {
            "keyword": "",
            "common_condition": {
                "page": 1,
                "page_size": 10,
                "order": "desc",
                "order_by": "",
                "filters": [
                    {
                        "name": "volume_id",
                        "values": [volume_id],
                        "fuzzy": False,
                    },
                    {
                        "name": "parent_id",
                        "values": [""],
                        "fuzzy": False,
                    },
                    {
                        "name": "file_name",
                        "values": [file_name],
                        "fuzzy": False,
                    },
                ],
            },
        }
        
        # Call the raw client's list_files method
        return self.raw.list_files(req, *opts)

    # ------------------------------------------------------------------
    # Workflow helpers
    # ------------------------------------------------------------------

    def create_document_processing_workflow(
        self,
        workflow_name: str,
        source_volume_id: str,
        target_volume_id: str,
        *opts: CallOption,
    ) -> str:
        """
        Create a workflow for processing documents from a source volume to a target volume.
        
        This is a high-level convenience method that creates a complete document processing pipeline
        with the following nodes:
        - RootNode: Reads files from the source volume
        - DocumentParseNode: Parses various document formats
        - CleanerNodeV2: Cleans parsed documents
        - ChunkNodeV2: Splits documents into chunks
        - EmbeddingNodeV2: Generates embeddings for document chunks
        - WriteNode: Writes processed results to the target volume
        
        The workflow is configured to trigger automatically when files are loaded into the source volume
        (ProcessMode.Interval = -1).
        
        Supported file types:
        - Text files: TXT (1), Markdown (6), HTM (27), HTML (28)
        - Office documents: PDF (2), PPT (4), DOCX (11), PPTX (12), XLS (24), XLSX (25)
        - Spreadsheets: CSV (7)
        
        Args:
            workflow_name: The name of the workflow (required)
            source_volume_id: The source volume ID where source documents are located (required)
            target_volume_id: The target volume ID where processed results will be written (required)
            *opts: Optional call configuration options
        
        Returns:
            The ID of the created workflow
        
        Example:
            workflow_id = sdk.create_document_processing_workflow(
                "My Workflow",
                "source-vol-456",
                "target-vol-123"
            )
        """
        from .models import FileType
        
        if not target_volume_id or not target_volume_id.strip():
            raise ValueError("target_volume_id is required")
        if not source_volume_id or not source_volume_id.strip():
            raise ValueError("source_volume_id is required")
        if not workflow_name or not workflow_name.strip():
            raise ValueError("workflow_name is required")
        
        # Build the workflow metadata with a complete document processing pipeline
        req = {
            "name": workflow_name,
            "source_volume_ids": [source_volume_id],
            "target_volume_id": target_volume_id,
            # Supported file types: TXT, PDF, PPT, DOCX, Markdown, PPTX, CSV, XLS, XLSX, HTM, HTML
            "file_types": [
                FileType.TXT, FileType.PDF, FileType.PPT, FileType.DOCX,
                FileType.MARKDOWN, FileType.PPTX, FileType.CSV,
                FileType.XLS, FileType.XLSX, FileType.HTM, FileType.HTML,
            ],
            # ProcessMode with Interval = -1 means trigger on file load
            "process_mode": {
                "interval": -1,  # -1 means trigger on file load
                "offset": 0,
            },
            # Complete document processing pipeline
            "workflow": {
                "nodes": [
                    {
                        "id": "RootNode_1",
                        "type": "RootNode",
                        "init_parameters": {},
                    },
                    {
                        "id": "DocumentParseNode_2",
                        "type": "DocumentParseNode",
                        "init_parameters": {},
                    },
                    {
                        "id": "CleanerNode_3",
                        "type": "CleanerNodeV2",
                        "init_parameters": {},
                    },
                    {
                        "id": "ChunkNode_4",
                        "type": "ChunkNodeV2",
                        "init_parameters": {},
                    },
                    {
                        "id": "EmbedNode_5",
                        "type": "EmbeddingNodeV2",
                        "init_parameters": {},
                    },
                    {
                        "id": "WriteNode_6",
                        "type": "WriteNode",
                        "init_parameters": {},
                    },
                ],
                "connections": [
                    {
                        "sender": "RootNode_1",
                        "receiver": "DocumentParseNode_2",
                    },
                    {
                        "sender": "DocumentParseNode_2",
                        "receiver": "CleanerNode_3",
                    },
                    {
                        "sender": "CleanerNode_3",
                        "receiver": "ChunkNode_4",
                    },
                    {
                        "sender": "ChunkNode_4",
                        "receiver": "EmbedNode_5",
                    },
                    {
                        "sender": "EmbedNode_5",
                        "receiver": "WriteNode_6",
                    },
                ],
            },
        }
        
        resp = self.raw.create_workflow(req, *opts)
        if not resp or not isinstance(resp, dict) or not resp.get("id"):
            raise ValueError("workflow created but ID is empty")
        
        return resp["id"]

    def get_workflow_job(
        self,
        workflow_id: str,
        source_file_id: str,
        *opts: CallOption,
    ) -> Dict[str, Any]:
        """
        Retrieve a single workflow job by workflow ID and source file ID.
        
        This is a high-level convenience method that queries workflow jobs using list_workflow_jobs
        with filters for workflow ID and source file ID, then returns the first matching job.
        
        Args:
            workflow_id: The workflow ID (required)
            source_file_id: The source file ID (required)
            *opts: Optional call configuration options
        
        Returns:
            The matching workflow job dict
        
        Example:
            job = sdk.get_workflow_job("workflow-123", "file-456")
            print(f"Job ID: {job['job_id']}, Status: {job['status']}")
        """
        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id is required")
        if not source_file_id or not source_file_id.strip():
            raise ValueError("source_file_id is required")
        
        # Query jobs with both filters
        resp = self.raw.list_workflow_jobs({
            "workflow_id": workflow_id,
            "source_file_id": source_file_id,
            "page": 1,
            "page_size": 1,  # We only need one result
        }, *opts)
        
        if not resp or not isinstance(resp, dict) or not resp.get("jobs") or len(resp["jobs"]) == 0:
            raise ValueError(f"workflow job not found for workflow_id={workflow_id}, source_file_id={source_file_id}")
        
        # Return the first matching job
        return resp["jobs"][0]

    def wait_for_workflow_job(
        self,
        workflow_id: str,
        source_file_id: str,
        poll_interval: float = 2.0,
        timeout: float = 60.0,
        *opts: CallOption,
    ) -> Dict[str, Any]:
        """
        Poll for a workflow job until it is found or the timeout expires.
        
        This method continuously queries for a workflow job matching the given workflow ID and source file ID
        until either:
        - The job is found (returns the job immediately)
        - The timeout expires (raises an error)
        
        Args:
            workflow_id: The workflow ID (required)
            source_file_id: The source file ID (required)
            poll_interval: The interval between polling attempts in seconds (default: 2.0)
            timeout: The maximum time to wait in seconds (default: 60.0)
            *opts: Optional call configuration options
        
        Returns:
            The matching workflow job dict
        
        Example:
            import time
            job = sdk.wait_for_workflow_job("workflow-123", "file-456", poll_interval=2.0, timeout=30.0)
            print(f"Job found: {job['job_id']}, Status: {job['status']}")
        """
        import time
        
        if not workflow_id or not workflow_id.strip():
            raise ValueError("workflow_id is required")
        if not source_file_id or not source_file_id.strip():
            raise ValueError("source_file_id is required")
        
        if poll_interval <= 0:
            poll_interval = 2.0
        
        if timeout <= 0:
            timeout = 60.0
        
        start_time = time.time()
        
        # Try once immediately
        try:
            job = self.get_workflow_job(workflow_id, source_file_id, *opts)
            if job:
                return job
        except ValueError:
            pass  # Job not found yet, continue polling
        
        # Poll until found or timeout expires
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"workflow job not found within timeout ({timeout}s) "
                    f"for workflow_id={workflow_id}, source_file_id={source_file_id}"
                )
            
            time.sleep(poll_interval)
            
            try:
                job = self.get_workflow_job(workflow_id, source_file_id, *opts)
                if job:
                    return job
            except ValueError:
                pass  # Job not found yet, continue polling

