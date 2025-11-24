"""Core client implementation for the MOI SDK."""

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Optional, Any, Dict, Iterable, Tuple, IO
from urllib.parse import urlparse, urljoin
import requests

from .errors import ErrBaseURLRequired, ErrAPIKeyRequired, ErrNilRequest, APIError, HTTPError
from .options import ClientOptions, CallOptions, ClientOption, CallOption
from .response import APIEnvelope
from .stream import FileStream


class RawClient:
    """
    RawClient provides typed access to the catalog service HTTP APIs.
    
    This is a low-level client that provides direct access to API endpoints.
    For higher-level convenience methods, use SDKClient instead.
    """
    
    def __init__(self, base_url: str, api_key: str, *opts: ClientOption):
        """
        Create a new client using the provided baseURL and apiKey.
        
        Args:
            base_url: The base URL of the catalog service (e.g., "https://api.example.com")
            api_key: The API key for authentication
            *opts: Optional client configuration options
        """
        trimmed_base = base_url.strip()
        if not trimmed_base:
            raise ErrBaseURLRequired("baseURL is required")
        
        trimmed_key = api_key.strip()
        if not trimmed_key:
            raise ErrAPIKeyRequired("apiKey is required")
        
        # Parse and normalize URL
        parsed = urlparse(trimmed_base)
        if not parsed.scheme or not parsed.hostname:
            raise ValueError("baseURL must include scheme and host")
        
        # Normalize URL (remove query and fragment, ensure no trailing slash)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        
        # Apply options
        cfg = ClientOptions()
        for opt in opts:
            if opt is not None:
                opt(cfg)
        
        # Setup HTTP client
        if cfg.http_client is None:
            session = requests.Session()
            self._http_client = session
        else:
            self._http_client = cfg.http_client
        
        self._base_url = normalized
        self._api_key = trimmed_key
        self._user_agent = cfg.user_agent
        self._default_headers = cfg.default_headers.copy()
        self._timeout = cfg.timeout
    
    def _build_url(self, path: str, query_params: Optional[Dict[str, Any]] = None) -> str:
        """Build a full URL from a path and optional query parameters."""
        if not path.startswith("/"):
            path = "/" + path
        
        url = urljoin(self._base_url, path)
        
        if query_params:
            # Convert query params to strings
            params = {}
            for k, v in query_params.items():
                if v is not None:
                    if isinstance(v, (list, tuple)):
                        params[k] = [str(item) for item in v]
                    else:
                        params[k] = str(v)
            
            # Build query string
            from urllib.parse import urlencode
            query_string = urlencode(params, doseq=True)
            if query_string:
                url = f"{url}?{query_string}"
        
        return url
    
    def _build_headers(self, call_opts: CallOptions, content_type: Optional[str] = None) -> Dict[str, str]:
        """Build headers for a request."""
        headers = self._default_headers.copy()
        headers["moi-key"] = self._api_key
        
        if self._user_agent:
            headers["User-Agent"] = self._user_agent
        
        if call_opts.request_id:
            headers["X-Request-ID"] = call_opts.request_id
        
        # Call options headers override default headers
        headers.update(call_opts.headers)
        
        if content_type:
            headers["Content-Type"] = content_type
            headers["Accept"] = "application/json"
        
        return headers
    
    def _parse_response(self, response: requests.Response, resp_type: Optional[type] = None) -> Any:
        """Parse the API response envelope."""
        # Check HTTP status
        if not (200 <= response.status_code < 300):
            body = response.content
            raise HTTPError(response.status_code, body)
        
        # Parse envelope
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise HTTPError(response.status_code, response.content) from e
        
        envelope = APIEnvelope.from_dict(data)
        
        # Check for API errors
        if envelope.code and envelope.code != "OK":
            raise APIError(
                code=envelope.code,
                message=envelope.msg,
                request_id=envelope.request_id,
                http_status=response.status_code
            )
        
        # Extract data
        if resp_type is None:
            return envelope.data
        
        if envelope.data is None or envelope.data == "null":
            return None
        
        # Deserialize to response type if provided
        if isinstance(envelope.data, dict):
            return resp_type(**envelope.data)
        elif isinstance(envelope.data, list):
            return [resp_type(**item) if isinstance(item, dict) else item for item in envelope.data]
        else:
            return envelope.data
    
    def post_json(
        self,
        path: str,
        req_body: Optional[Any] = None,
        resp_type: Optional[type] = None,
        *opts: CallOption
    ) -> Any:
        """
        Issue a JSON POST request and decode the enveloped response payload.
        
        Args:
            path: The API endpoint path
            req_body: The request body (will be JSON serialized)
            resp_type: Optional response type to deserialize to
            *opts: Optional call configuration options
        
        Returns:
            The decoded response data
        """
        return self._do_json("POST", path, req_body, resp_type, *opts)
    
    def get_json(
        self,
        path: str,
        resp_type: Optional[type] = None,
        *opts: CallOption
    ) -> Any:
        """
        Issue a JSON GET request and decode the enveloped response payload.
        
        Args:
            path: The API endpoint path
            resp_type: Optional response type to deserialize to
            *opts: Optional call configuration options
        
        Returns:
            The decoded response data
        """
        return self._do_json("GET", path, None, resp_type, *opts)
    
    def _do_json(
        self,
        method: str,
        path: str,
        body: Optional[Any],
        resp_type: Optional[type],
        *opts: CallOption
    ) -> Any:
        """Execute a JSON request."""
        if self is None:
            raise ValueError("sdk client is None")
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build URL
        url = self._build_url(path, call_opts.query_params)
        
        # Serialize body
        payload = self._prepare_body(body)
        json_body = None
        if payload is not None:
            json_body = json.dumps(payload, default=str)
        
        # Build headers
        headers = self._build_headers(call_opts, "application/json")
        
        # Make request
        response = self._http_client.request(
            method=method,
            url=url,
            headers=headers,
            data=json_body,
            timeout=self._timeout
        )
        
        return self._parse_response(response, resp_type)
    
    @staticmethod
    def _prepare_body(body: Optional[Any]) -> Optional[Any]:
        """Convert dataclasses to dictionaries before serialization."""
        if body is None:
            return None
        if is_dataclass(body):
            return asdict(body)
        return body

    @staticmethod
    def _normalize_file_items(
        file_items: Iterable[Tuple[IO[bytes], str]],
        field_name: str = "file",
    ) -> Iterable[Tuple[str, Tuple[str, IO[bytes]]]]:
        """Convert (fileobj, filename) pairs to the format expected by requests."""
        normalized = []
        for index, item in enumerate(file_items):
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise ValueError(f"file item at index {index} must be a (fileobj, filename) tuple")
            file_obj, filename = item
            if file_obj is None:
                raise ValueError(f"file object at index {index} cannot be None")
            if not filename:
                raise ValueError(f"filename at index {index} cannot be empty")
            normalized.append((field_name, (filename, file_obj)))
        return normalized

    def _request_json(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        *opts: CallOption,
    ) -> Any:
        """Internal helper to issue JSON requests without manual resp_type wiring."""
        return self._do_json(method, path, body, None, *opts)

    def post_multipart(
        self,
        path: str,
        files: Dict[str, Any],
        fields: Optional[Dict[str, Any]] = None,
        resp_type: Optional[type] = None,
        *opts: CallOption
    ) -> Any:
        """
        Issue a multipart/form-data POST request.
        
        Args:
            path: The API endpoint path
            files: Dictionary of file fields (can be file objects, tuples, etc.)
            fields: Dictionary of form fields
            resp_type: Optional response type to deserialize to
            *opts: Optional call configuration options
        
        Returns:
            The decoded response data
        """
        if self is None:
            raise ValueError("sdk client is None")
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build URL
        url = self._build_url(path, call_opts.query_params)
        
        # Build headers (without Content-Type, let requests set it for multipart)
        headers = self._build_headers(call_opts)
        # Remove Content-Type so requests can set it with boundary
        headers.pop("Content-Type", None)
        
        # Prepare form data
        data = self._prepare_body(fields) or {}
        
        # Make request
        response = self._http_client.request(
            method="POST",
            url=url,
            headers=headers,
            data=data,
            files=files,
            timeout=self._timeout
        )
        
        return self._parse_response(response, resp_type)
    
    def get_raw(
        self,
        path: str,
        *opts: CallOption
    ) -> requests.Response:
        """
        Issue a raw GET request and return the response object.
        
        Args:
            path: The API endpoint path
            *opts: Optional call configuration options
        
        Returns:
            The raw requests.Response object
        """
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build URL
        url = self._build_url(path, call_opts.query_params)
        
        # Build headers
        headers = self._build_headers(call_opts)
        
        # Make request
        response = self._http_client.request(
            method="GET",
            url=url,
            headers=headers,
            timeout=self._timeout
        )
        
        # Check HTTP status
        if not (200 <= response.status_code < 300):
            raise HTTPError(response.status_code, response.content)
        
        return response

    # ----------------------------------------------------------------------
    # Catalog APIs
    # ----------------------------------------------------------------------

    def create_catalog(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """Create a new catalog."""
        if request is None:
            raise ErrNilRequest("create_catalog requires a request payload")
        return self._request_json("POST", "/catalog/create", request, *opts)

    def delete_catalog(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """Delete a catalog by ID."""
        if request is None:
            raise ErrNilRequest("delete_catalog requires a request payload")
        return self._request_json("POST", "/catalog/delete", request, *opts)

    def update_catalog(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """Update catalog information."""
        if request is None:
            raise ErrNilRequest("update_catalog requires a request payload")
        return self._request_json("POST", "/catalog/update", request, *opts)

    def get_catalog(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """Fetch catalog information by ID."""
        if request is None:
            raise ErrNilRequest("get_catalog requires a request payload")
        return self._request_json("POST", "/catalog/info", request, *opts)

    def list_catalogs(self, *opts: CallOption) -> Any:
        """List all catalogs."""
        return self._request_json("POST", "/catalog/list", {}, *opts)

    def get_catalog_tree(self, *opts: CallOption) -> Any:
        """Retrieve the hierarchical catalog tree."""
        return self._request_json("POST", "/catalog/tree", {}, *opts)

    def get_catalog_ref_list(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """List objects referencing the specified catalog."""
        if request is None:
            raise ErrNilRequest("get_catalog_ref_list requires a request payload")
        return self._request_json("POST", "/catalog/ref_list", request, *opts)

    # ----------------------------------------------------------------------
    # Database APIs
    # ----------------------------------------------------------------------

    def create_database(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_database requires a request payload")
        return self._request_json("POST", "/catalog/database/create", request, *opts)

    def delete_database(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_database requires a request payload")
        return self._request_json("POST", "/catalog/database/delete", request, *opts)

    def update_database(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_database requires a request payload")
        return self._request_json("POST", "/catalog/database/update", request, *opts)

    def get_database(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_database requires a request payload")
        return self._request_json("POST", "/catalog/database/info", request, *opts)

    def list_databases(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_databases requires a request payload")
        return self._request_json("POST", "/catalog/database/list", request, *opts)

    def get_database_children(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_database_children requires a request payload")
        return self._request_json("POST", "/catalog/database/children", request, *opts)

    def get_database_ref_list(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_database_ref_list requires a request payload")
        return self._request_json("POST", "/catalog/database/ref_list", request, *opts)

    # ----------------------------------------------------------------------
    # Table APIs
    # ----------------------------------------------------------------------

    def create_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_table requires a request payload")
        return self._request_json("POST", "/catalog/table/create", request, *opts)

    def get_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_table requires a request payload")
        return self._request_json("POST", "/catalog/table/info", request, *opts)

    def get_table_overview(self, *opts: CallOption) -> Any:
        return self._request_json("POST", "/catalog/table/overview", {}, *opts)

    def check_table_exists(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("check_table_exists requires a request payload")
        return self._request_json("POST", "/catalog/table/exist", request, *opts)

    def preview_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("preview_table requires a request payload")
        return self._request_json("POST", "/catalog/table/preview", request, *opts)

    def load_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("load_table requires a request payload")
        return self._request_json("POST", "/catalog/table/load", request, *opts)

    def get_table_download_link(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_table_download_link requires a request payload")
        return self._request_json("POST", "/catalog/table/download", request, *opts)

    def truncate_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("truncate_table requires a request payload")
        return self._request_json("POST", "/catalog/table/truncate", request, *opts)

    def delete_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_table requires a request payload")
        return self._request_json("POST", "/catalog/table/delete", request, *opts)

    def get_table_full_path(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_table_full_path requires a request payload")
        return self._request_json("POST", "/catalog/table/full_path", request, *opts)

    def get_table_ref_list(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_table_ref_list requires a request payload")
        return self._request_json("POST", "/catalog/table/ref_list", request, *opts)

    # ----------------------------------------------------------------------
    # Volume APIs
    # ----------------------------------------------------------------------

    def create_volume(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_volume requires a request payload")
        return self._request_json("POST", "/catalog/volume/create", request, *opts)

    def delete_volume(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_volume requires a request payload")
        return self._request_json("POST", "/catalog/volume/delete", request, *opts)

    def update_volume(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_volume requires a request payload")
        return self._request_json("POST", "/catalog/volume/update", request, *opts)

    def get_volume(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_volume requires a request payload")
        return self._request_json("POST", "/catalog/volume/info", request, *opts)

    def get_volume_ref_list(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_volume_ref_list requires a request payload")
        return self._request_json("POST", "/catalog/volume/ref_list", request, *opts)

    def get_volume_full_path(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_volume_full_path requires a request payload")
        return self._request_json("POST", "/catalog/volume/full_path", request, *opts)

    def add_volume_workflow_ref(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("add_volume_workflow_ref requires a request payload")
        return self._request_json("POST", "/catalog/volume/add_ref_workflow", request, *opts)

    def remove_volume_workflow_ref(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("remove_volume_workflow_ref requires a request payload")
        return self._request_json("POST", "/catalog/volume/remove_ref_workflow", request, *opts)

    # ----------------------------------------------------------------------
    # File APIs
    # ----------------------------------------------------------------------

    def create_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_file requires a request payload")
        return self._request_json("POST", "/catalog/file/create", request, *opts)

    def update_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_file requires a request payload")
        return self._request_json("POST", "/catalog/file/update", request, *opts)

    def delete_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_file requires a request payload")
        return self._request_json("POST", "/catalog/file/delete", request, *opts)

    def delete_file_ref(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_file_ref requires a request payload")
        return self._request_json("POST", "/catalog/file/delete_ref", request, *opts)

    def get_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_file requires a request payload")
        return self._request_json("POST", "/catalog/file/info", request, *opts)

    def list_files(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_files requires a request payload")
        return self._request_json("POST", "/catalog/file/list", request, *opts)

    def upload_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("upload_file requires a request payload")
        return self._request_json("POST", "/catalog/file/upload", request, *opts)

    def get_file_download_link(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_file_download_link requires a request payload")
        return self._request_json("POST", "/catalog/file/download", request, *opts)

    def get_file_preview_link(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_file_preview_link requires a request payload")
        return self._request_json("POST", "/catalog/file/preview_link", request, *opts)

    def get_file_preview_stream(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_file_preview_stream requires a request payload")
        return self._request_json("POST", "/catalog/file/preview_stream", request, *opts)

    # ----------------------------------------------------------------------
    # Folder APIs
    # ----------------------------------------------------------------------

    def create_folder(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_folder requires a request payload")
        return self._request_json("POST", "/catalog/folder/create", request, *opts)

    def update_folder(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_folder requires a request payload")
        return self._request_json("POST", "/catalog/folder/update", request, *opts)

    def delete_folder(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_folder requires a request payload")
        return self._request_json("POST", "/catalog/folder/delete", request, *opts)

    def clean_folder(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("clean_folder requires a request payload")
        return self._request_json("POST", "/catalog/folder/clean", request, *opts)

    def get_folder_ref_list(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_folder_ref_list requires a request payload")
        return self._request_json("POST", "/catalog/folder/ref_list", request, *opts)

    # ----------------------------------------------------------------------
    # Connector APIs (file upload + preview)
    # ----------------------------------------------------------------------

    def upload_local_files(
        self,
        file_items: Iterable[Tuple[IO[bytes], str]],
        meta: Iterable[Dict[str, Any]],
        *opts: CallOption,
    ) -> Any:
        """
        Upload multiple local files to connector temporary storage.
        
        Args:
            file_items: Iterable of (fileobj, filename) tuples.
            meta: Iterable of metadata dicts, one per file, matching connector requirements.
        """
        file_list = list(file_items or [])
        if not file_list:
            raise ValueError("upload_local_files requires at least one file item")
        if not meta:
            raise ValueError("meta is required for upload_local_files")
        files_payload = list(self._normalize_file_items(file_list))
        fields = {"meta": json.dumps(list(meta))}
        return self.post_multipart(
            "/connectors/file/upload",
            files=files_payload,
            fields=fields,
            *opts,
        )

    def upload_local_file(
        self,
        file_obj: IO[bytes],
        file_name: str,
        meta: Iterable[Dict[str, Any]],
        *opts: CallOption,
    ) -> Any:
        """Convenience wrapper to upload a single local file."""
        return self.upload_local_files([(file_obj, file_name)], meta, *opts)

    def upload_local_file_from_path(
        self,
        file_path: str,
        meta: Iterable[Dict[str, Any]],
        *opts: CallOption,
    ) -> Any:
        """Open a file from disk and upload it via upload_local_files."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"file not found: {file_path}")
        with path.open("rb") as handle:
            return self.upload_local_file(handle, path.name, meta, *opts)

    def preview_connector_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """Preview a connector/local uploaded file to derive schema details."""
        if request is None:
            raise ErrNilRequest("preview_connector_file requires a request payload")
        return self._request_json("POST", "/connectors/file/preview", request, *opts)

    def upload_connector_file(
        self,
        volume_id: str,
        file_items: Optional[Iterable[Tuple[IO[bytes], str]]] = None,
        *,
        meta: Optional[Iterable[Dict[str, Any]]] = None,
        file_types: Optional[Iterable[int]] = None,
        path_regex: Optional[str] = None,
        unzip_keep_structure: bool = False,
        dedup_config: Optional[Dict[str, Any]] = None,
        table_config: Optional[Dict[str, Any]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        *opts: CallOption,
    ) -> Any:
        """
        Upload files (or reference existing connector files) to trigger table import.
        
        This mirrors the Go SDK's UploadConnectorFile helper.
        """
        if not volume_id:
            raise ValueError("volume_id is required")
        if not file_items and not table_config:
            raise ValueError("either file_items or table_config (with conn_file_ids) must be provided")

        files_payload = []
        if file_items:
            files_payload = list(self._normalize_file_items(file_items))

        fields: Dict[str, Any] = {"VolumeID": str(volume_id)}
        if meta:
            fields["meta"] = json.dumps(list(meta))
        if file_types:
            fields["file_types"] = json.dumps(list(file_types))
        if path_regex:
            fields["path_regex"] = path_regex
        if unzip_keep_structure:
            fields["unzip_keep_structure"] = "true"
        if dedup_config:
            fields["dedup"] = json.dumps(dedup_config)
        if table_config:
            fields["table_config"] = json.dumps(table_config)
        if extra_fields:
            fields.update(extra_fields)

        files_arg = files_payload if files_payload else {}
        return self.post_multipart(
            "/connectors/upload",
            files=files_arg,
            fields=fields,
            *opts,
        )

    # ----------------------------------------------------------------------
    # User APIs
    # ----------------------------------------------------------------------

    def create_user(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_user requires a request payload")
        return self._request_json("POST", "/user/create", request, *opts)

    def delete_user(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_user requires a request payload")
        return self._request_json("POST", "/user/delete", request, *opts)

    def get_user_detail(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_user_detail requires a request payload")
        return self._request_json("POST", "/user/detail_info", request, *opts)

    def list_users(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_users requires a request payload")
        return self._request_json("POST", "/user/list", request, *opts)

    def update_user_password(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_user_password requires a request payload")
        return self._request_json("POST", "/user/update_password", request, *opts)

    def update_user_info(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_user_info requires a request payload")
        return self._request_json("POST", "/user/update_info", request, *opts)

    def update_user_roles(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_user_roles requires a request payload")
        return self._request_json("POST", "/user/update_role_list", request, *opts)

    def update_user_status(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_user_status requires a request payload")
        return self._request_json("POST", "/user/update_status", request, *opts)

    def get_my_api_key(self, *opts: CallOption) -> Any:
        return self._request_json("POST", "/user/me/api-key", None, *opts)

    def refresh_my_api_key(self, *opts: CallOption) -> Any:
        return self._request_json("POST", "/user/me/api-key/refresh", None, *opts)

    def get_my_info(self, *opts: CallOption) -> Any:
        return self._request_json("POST", "/user/me/info", None, *opts)

    def update_my_info(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_my_info requires a request payload")
        return self._request_json("POST", "/user/me/update_info", request, *opts)

    def update_my_password(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_my_password requires a request payload")
        return self._request_json("POST", "/user/me/update_password", request, *opts)

    # ----------------------------------------------------------------------
    # Role APIs
    # ----------------------------------------------------------------------

    def create_role(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_role requires a request payload")
        return self._request_json("POST", "/role/create", request, *opts)

    def delete_role(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_role requires a request payload")
        return self._request_json("POST", "/role/delete", request, *opts)

    def get_role(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_role requires a request payload")
        return self._request_json("POST", "/role/info", request, *opts)

    def list_roles(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_roles requires a request payload")
        return self._request_json("POST", "/role/list", request, *opts)

    def list_roles_by_category_and_object(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_roles_by_category_and_object requires a request payload")
        return self._request_json("POST", "/role/list_by_category_and_obj", request, *opts)

    def update_role_code_list(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_role_code_list requires a request payload")
        return self._request_json("POST", "/role/update_code_list", request, *opts)

    def update_role_info(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_role_info requires a request payload")
        return self._request_json("POST", "/role/update_info", request, *opts)

    def update_roles_by_object(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_roles_by_object requires a request payload")
        return self._request_json("POST", "/role/update_roles_by_obj", request, *opts)

    def update_role_status(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_role_status requires a request payload")
        return self._request_json("POST", "/role/update_status", request, *opts)

    # ----------------------------------------------------------------------
    # Privilege APIs
    # ----------------------------------------------------------------------

    def list_objects_by_category(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_objects_by_category requires a request payload")
        return self._request_json("POST", "/rbac/priv/list_obj_by_category", request, *opts)

    # ----------------------------------------------------------------------
    # GenAI APIs
    # ----------------------------------------------------------------------

    def create_genai_pipeline(
        self,
        request: Optional[Dict[str, Any]],
        file_items: Optional[Iterable[Tuple[IO[bytes], str]]] = None,
        *opts: CallOption,
    ) -> Any:
        if file_items:
            if request is None:
                raise ErrNilRequest("create_genai_pipeline requires a request payload when uploading files")
            payload = json.dumps(request, default=str)
            fields: Dict[str, Any] = {"payload": payload}
            if "file_names" in request and request["file_names"]:
                fields["file_names"] = json.dumps(request["file_names"])
            files_payload = list(self._normalize_file_items(file_items, field_name="files"))
            return self.post_multipart("/v1/genai/pipeline", files=files_payload, fields=fields, *opts)

        if request is None:
            raise ErrNilRequest("create_genai_pipeline requires a request payload")
        return self._request_json("POST", "/v1/genai/pipeline", request, *opts)

    def get_genai_job(self, job_id: str, *opts: CallOption) -> Any:
        if not job_id:
            raise ValueError("job_id cannot be empty")
        path = f"/v1/genai/jobs/{job_id}"
        return self._request_json("GET", path, None, *opts)

    def download_genai_result(self, file_id: str, *opts: CallOption) -> FileStream:
        if not file_id:
            raise ValueError("file_id cannot be empty")

        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)

        path = f"/v1/genai/results/file/{file_id}"
        url = self._build_url(path, call_opts.query_params)
        headers = self._build_headers(call_opts)

        response = self._http_client.request(
            method="GET",
            url=url,
            headers=headers,
            timeout=self._timeout,
            stream=True,
        )

        if not (200 <= response.status_code < 300):
            body = response.content
            response.close()
            raise HTTPError(response.status_code, body)

        return FileStream(response)

    # ----------------------------------------------------------------------
    # NL2SQL APIs
    # ----------------------------------------------------------------------

    def run_nl2sql(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("run_nl2sql requires a request payload")
        return self._request_json("POST", "/nl2sql/run_sql", request, *opts)

    def create_knowledge(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("create_knowledge requires a request payload")
        return self._request_json("POST", "/catalog/nl2sql_knowledge/create", request, *opts)

    def update_knowledge(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("update_knowledge requires a request payload")
        return self._request_json("POST", "/catalog/nl2sql_knowledge/update", request, *opts)

    def delete_knowledge(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_knowledge requires a request payload")
        return self._request_json("POST", "/catalog/nl2sql_knowledge/delete", request, *opts)

    def get_knowledge(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_knowledge requires a request payload")
        return self._request_json("POST", "/catalog/nl2sql_knowledge/get", request, *opts)

    def list_knowledge(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_knowledge requires a request payload")
        return self._request_json("POST", "/catalog/nl2sql_knowledge/list", request, *opts)

    def search_knowledge(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("search_knowledge requires a request payload")
        return self._request_json("POST", "/catalog/nl2sql_knowledge/search", request, *opts)

    # ----------------------------------------------------------------------
    # Health + Log APIs
    # ----------------------------------------------------------------------

    def health_check(self, *opts: CallOption) -> Any:
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)

        url = self._build_url("/healthz", call_opts.query_params)
        headers = self._build_headers(call_opts)
        response = self._http_client.request("GET", url=url, headers=headers, timeout=self._timeout)
        if not (200 <= response.status_code < 300):
            raise HTTPError(response.status_code, response.content)
        return response.json()

    def list_user_logs(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_user_logs requires a request payload")
        return self._request_json("POST", "/log/user", request, *opts)

    def list_role_logs(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("list_role_logs requires a request payload")
        return self._request_json("POST", "/log/role", request, *opts)

