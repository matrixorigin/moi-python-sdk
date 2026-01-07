"""Core client implementation for the MOI SDK."""

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Optional, Any, Dict, Iterable, Tuple, IO, List
from urllib.parse import urlparse, urljoin
import requests

from .errors import ErrBaseURLRequired, ErrAPIKeyRequired, ErrNilRequest, APIError, HTTPError
from .options import ClientOptions, CallOptions, ClientOption, CallOption
from .response import APIEnvelope
from .stream import FileStream, DataAnalysisStream


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
    
    def with_special_user(self, api_key: str) -> "RawClient":
        """
        Create a new RawClient with the same configuration but a different API key.
        
        The cloned client shares the same HTTP client instance but has its own API key.
        Raises ValueError if the API key is empty.
        
        Args:
            api_key: The new API key to use
            
        Returns:
            A new RawClient instance with the new API key
            
        Example:
            original = RawClient("https://api.example.com", "original-key")
            new_client = original.with_special_user("new-key")
        """
        trimmed_key = api_key.strip()
        if not trimmed_key:
            raise ValueError("API key is required")
        
        # Create a new client with the same configuration but different API key
        new_client = RawClient.__new__(RawClient)
        new_client._base_url = self._base_url
        new_client._api_key = trimmed_key
        new_client._http_client = self._http_client  # Share the same HTTP client (thread-safe)
        new_client._user_agent = self._user_agent
        new_client._default_headers = self._default_headers.copy()  # Copy headers
        new_client._timeout = self._timeout
        
        return new_client
    
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

    def get_multi_table(self, request: Optional[List[Dict[str, Any]]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_multi_table requires a request payload")
        request = {"table_list": request}
        resp = self._request_json("POST", "/catalog/table/multi_info", request, *opts)
        return resp["info_map"]

    def get_table_overview(self, *opts: CallOption) -> Any:
        return self._request_json("POST", "/catalog/table/overview", {}, *opts)

    def check_table_exists(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("check_table_exists requires a request payload")
        return self._request_json("POST", "/catalog/table/exist", request, *opts)

    def preview_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Preview table data without loading it into memory.
        
        This method internally uses get_table_data to fetch the data.
        
        Args:
            request: Dict with table ID and optional lines:
                - id: Table ID (required)
                - lines: Number of rows to preview (optional, default 10)
            *opts: Optional call configuration options
        
        Returns:
            Dict with columns and data:
                - columns: List of column definitions
                - data: List of data rows (limited to requested lines)
        """
        if request is None:
            raise ErrNilRequest("preview_table requires a request payload")
        
        table_id = request.get("id")
        if table_id is None:
            raise ValueError("id is required in request")
        
        # Convert preview request to get_table_data request
        lines = request.get("lines", 10)
        if lines <= 0:
            lines = 10  # Default preview size
        
        # Call get_table_data internally
        data_req = {
            "id": table_id,
            "page": 1,
            "page_size": lines,
        }
        # database_id is optional for get_table_data when only table_id is provided
        if "database_id" in request:
            data_req["database_id"] = request["database_id"]
        
        data_resp = self.get_table_data(data_req, *opts)
        
        # Convert get_table_data response to preview response
        # Limit data rows to the requested lines
        preview_data = data_resp.get("data", [])
        if len(preview_data) > lines:
            preview_data = preview_data[:lines]
        
        return {
            "columns": data_resp.get("columns", []),
            "data": preview_data,
        }

    def get_table_data(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_table_data requires a request payload")
        return self._request_json("POST", "/catalog/table/data", request, *opts)

    def load_table(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("load_table requires a request payload")
        return self._request_json("POST", "/catalog/table/load", request, *opts)

    def get_table_download_link(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("get_table_download_link requires a request payload")
        return self._request_json("POST", "/catalog/table/download", request, *opts)

    def download_table_data(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> "FileStream":
        """
        Download table data as a CSV file stream.
        
        Returns a FileStream that must be closed by the caller. The stream contains
        the CSV content that can be read directly.
        
        This method uses a client with no timeout to allow downloading large files.
        The download can still be cancelled using the provided context.
        
        Args:
            request: Dict with table ID:
                - id: Table ID (required)
            *opts: Optional call configuration options
        
        Returns:
            FileStream object that must be closed by the caller
        
        Example:
            stream = client.download_table_data({"id": 1})
            try:
                data = stream.read()
                print(f"Downloaded {len(data)} bytes")
            finally:
                stream.close()
        """
        if request is None:
            raise ErrNilRequest("download_table_data requires a request payload")
        
        table_id = request.get("id")
        if table_id is None:
            raise ValueError("id is required in request")
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build URL
        path = "/catalog/table/download_data"
        url = self._build_url(path, call_opts.query_params)
        
        # Build headers
        headers = self._build_headers(call_opts, "application/json")
        
        # Serialize body
        payload = json.dumps({"id": table_id}, default=str)
        
        # Use HTTP client with no timeout for downloading large files
        # The download can still be cancelled via context if needed
        # Temporarily save original timeout
        original_timeout = self._timeout
        try:
            # Set timeout to None for large file downloads
            self._timeout = None
            
            # Make POST request with stream=True
            response = self._http_client.request(
                method="POST",
                url=url,
                headers=headers,
                data=payload,
                timeout=None,  # No timeout - allows downloading large files
                stream=True
            )
        finally:
            # Restore original timeout
            self._timeout = original_timeout
        
        # Check for HTTP errors
        if not (200 <= response.status_code < 300):
            body = response.content
            response.close()
            raise HTTPError(response.status_code, body)
        
        return FileStream(response)

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
        /,
        *opts: CallOption,
        file_items: Optional[Iterable[Tuple[IO[bytes], str]]] = None,
        meta: Optional[Iterable[Dict[str, Any]]] = None,
        file_types: Optional[Iterable[int]] = None,
        path_regex: Optional[str] = None,
        unzip_keep_structure: bool = False,
        dedup_config: Optional[Dict[str, Any]] = None,
        table_config: Optional[Dict[str, Any]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
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

        # Ensure multipart/form-data is used even when only table_config is provided.
        # requests requires a non-empty files dict to set multipart content-type.
        files_arg = files_payload if files_payload else {"__empty": ("", b"")}
        # Use positional arguments to avoid conflicting with *opts when callers pass None.
        return self.post_multipart("/connectors/upload", files_arg, fields, *opts)

    def download_connector_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("download_connector_file requires a request payload")
        conn_file_id = str(request.get("conn_file_id", "")).strip()
        if not conn_file_id:
            raise ValueError("conn_file_id is required")
        payload = dict(request) if isinstance(request, dict) else {}
        payload["conn_file_id"] = conn_file_id
        return self._request_json("POST", "/connectors/file/download", payload, *opts)

    def delete_connector_file(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("delete_connector_file requires a request payload")
        conn_file_id = str(request.get("conn_file_id", "")).strip()
        if not conn_file_id:
            raise ValueError("conn_file_id is required")
        payload = dict(request) if isinstance(request, dict) else {}
        payload["conn_file_id"] = conn_file_id
        return self._request_json("POST", "/connectors/file/delete", payload, *opts)

    # ----------------------------------------------------------------------
    # Task APIs
    # ----------------------------------------------------------------------

    def get_task(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Retrieve detailed information about a task by its ID.
        
        This method queries the task information endpoint to get task details
        including status, configuration, and results.
        
        Example:
            resp = client.get_task({"task_id": 123})
            print(f"Task: {resp['name']}, Status: {resp['status']}")
        """
        if request is None:
            raise ErrNilRequest("get_task requires a request payload")
        task_id = request.get("task_id")
        if not task_id:
            raise ValueError("task_id is required")
        
        # Add task_id as query parameter using with_query_param
        from .options import with_query_param
        opts = list(opts) + [with_query_param("task_id", str(task_id))]
        return self._request_json("GET", "/task/get", None, *opts)

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
    # Workflow APIs
    # ----------------------------------------------------------------------

    def create_workflow(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Create a new workflow.
        
        This method creates a workflow using workflow metadata, which includes:
        - Workflow name
        - Source volume names/IDs
        - Target volume ID/name
        - Process mode (interval and offset)
        - File types
        - Workflow definition (nodes and connections)
        
        Args:
            request: WorkflowMetadata dict with workflow configuration
            *opts: Optional call configuration options
        
        Returns:
            WorkflowCreateResponse dict with workflow ID and metadata
        
        Example:
            resp = client.create_workflow({
                "name": "my-workflow",
                "source_volume_ids": ["vol-123"],
                "target_volume_id": "vol-456",
                "file_types": [1, 2, 3],
                "process_mode": {
                    "interval": 3600,
                    "offset": 0
                },
                "workflow": {
                    "nodes": [
                        {
                            "id": "node1",
                            "type": "ParseNode",
                            "init_parameters": {}
                        }
                    ],
                    "connections": [
                        {
                            "sender": "node1",
                            "receiver": "node2"
                        }
                    ]
                }
            })
        """
        if request is None:
            raise ErrNilRequest("create_workflow requires a request payload")
        
        # Ensure required fields are initialized to avoid serializing them as null
        # The server requires these fields to be present even if empty
        if "source_volume_names" not in request or request["source_volume_names"] is None:
            request["source_volume_names"] = []
        if "source_volume_ids" not in request or request["source_volume_ids"] is None:
            request["source_volume_ids"] = []
        if "process_mode" not in request or request["process_mode"] is None:
            request["process_mode"] = {
                "interval": -1,  # Default: trigger on file load
                "offset": 0
            }
        if "file_types" not in request or request["file_types"] is None:
            request["file_types"] = []
        
        # Ensure all workflow nodes have InitParameters initialized to empty dict
        # to avoid serializing them as null
        if "workflow" in request and request["workflow"] is not None:
            workflow = request["workflow"]
            if "nodes" in workflow and workflow["nodes"] is not None:
                for node in workflow["nodes"]:
                    if "init_parameters" not in node or node["init_parameters"] is None:
                        node["init_parameters"] = {}
        
        return self._request_json("POST", "/v1/genai/workflow", request, *opts)

    def list_workflow_jobs(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        List workflow jobs with optional filtering and pagination.
        
        This method calls the workflow-be API endpoint /byoa/api/v1/workflow_job to retrieve
        a list of workflow jobs. The request supports filtering by workflow ID, source file ID, and status,
        as well as pagination.
        
        Args:
            request: WorkflowJobListRequest dict with optional filters and pagination parameters:
                - workflow_id: Filter by workflow ID
                - source_file_id: Filter by source file ID
                - status: Filter by job status
                - page: Page number (starts from 1, default 1)
                - page_size: Page size (default 20)
            *opts: Optional call configuration options
        
        Returns:
            WorkflowJobListResponse dict with jobs list and total count
        
        Example:
            resp = client.list_workflow_jobs({
                "workflow_id": "workflow-123",
                "status": "running",
                "page": 1,
                "page_size": 20
            })
            for job in resp["jobs"]:
                print(f"Job: {job['job_id']}, Status: {job['status']}")
        """
        if request is None:
            raise ErrNilRequest("list_workflow_jobs requires a request payload")
        
        # Build query parameters
        from .options import with_query_param
        opts_list = list(opts)
        
        if request.get("workflow_id"):
            opts_list.append(with_query_param("workflow_id", request["workflow_id"]))
        if request.get("source_file_id"):
            opts_list.append(with_query_param("source_file_id", request["source_file_id"]))
        if request.get("status"):
            opts_list.append(with_query_param("status", request["status"]))
        if request.get("page", 0) > 0:
            opts_list.append(with_query_param("page", str(request["page"])))
        if request.get("page_size", 0) > 0:
            opts_list.append(with_query_param("page_size", str(request["page_size"])))
        
        # Make GET request
        call_opts = CallOptions()
        for opt in opts_list:
            if opt is not None:
                opt(call_opts)
        
        path = "/byoa/api/v1/workflow_job"
        url = self._build_url(path, call_opts.query_params)
        
        headers = self._build_headers(call_opts)
        
        response = self._http_client.request(
            method="GET",
            url=url,
            headers=headers,
            data=None,
            timeout=self._timeout
        )
        
        # Parse response - API returns {"code":"ok","msg":"ok","data":{"total":1,"jobs":[...]}}
        resp_data = self._parse_response(response)
        
        # Convert raw jobs to match WorkflowJob structure
        # API returns status as int (1=running, 2=completed, 3=failed)
        if isinstance(resp_data, dict) and "jobs" in resp_data:
            jobs = resp_data["jobs"]
            converted_jobs = []
            source_file_id = request.get("source_file_id", "")
            
            for raw_job in jobs:
                job = {
                    "job_id": raw_job.get("id", ""),
                    "workflow_id": raw_job.get("workflow_id", ""),
                    "source_file_id": source_file_id,  # Populate from request filter
                    "status": raw_job.get("status", 0),  # Keep as int
                    "start_time": raw_job.get("start_time", ""),
                    "end_time": raw_job.get("end_time") or "",  # Handle null
                }
                
                # Try to extract source_file_id from description if available
                if not job["source_file_id"] and "description" in raw_job:
                    desc = raw_job["description"]
                    if isinstance(desc, dict) and "triggerTaskID" in desc:
                        trigger_task_id = desc["triggerTaskID"]
                        if isinstance(trigger_task_id, str):
                            job["source_file_id"] = trigger_task_id
                        elif isinstance(trigger_task_id, (int, float)):
                            job["source_file_id"] = str(int(trigger_task_id))
                
                converted_jobs.append(job)
            
            resp_data["jobs"] = converted_jobs
        
        # Ensure jobs is never None
        if isinstance(resp_data, dict) and "jobs" not in resp_data:
            resp_data["jobs"] = []
        
        return resp_data

    # ----------------------------------------------------------------------
    # NL2SQL APIs
    # ----------------------------------------------------------------------

    def run_nl2sql(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        if request is None:
            raise ErrNilRequest("run_nl2sql requires a request payload")
        return self._request_json("POST", "/catalog/nl2sql/run_sql", request, *opts)

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

    # ----------------------------------------------------------------------
    # LLM Proxy APIs
    # ----------------------------------------------------------------------

    def _do_llm_json(
        self,
        method: str,
        path: str,
        body: Optional[Any],
        *opts: CallOption
    ) -> Any:
        """
        Issue a JSON request to LLM Proxy API and decode the direct response (no envelope).
        
        LLM Proxy APIs return data directly or error in ErrorResponse format, not in envelope format.
        """
        if self is None:
            raise ValueError("sdk client is None")
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build full URL with /llm-proxy prefix
        full_path = "/llm-proxy" + (path if path.startswith("/") else "/" + path)
        url = self._build_url(full_path, call_opts.query_params)
        
        # Serialize body
        json_body = None
        if body is not None:
            json_body = json.dumps(body, default=str)
        
        # Build headers
        headers = self._build_headers(call_opts, "application/json")
        
        # Make request
        response = self._http_client.request(
            method=method,
            url=url,
            headers=headers,
            data=json_body
        )
        
        # Read response body
        data = response.content
        
        # Check for error response format
        if response.status_code >= 400:
            try:
                err_data = response.json()
                if isinstance(err_data, dict) and "error" in err_data:
                    error_info = err_data["error"]
                    raise APIError(
                        code=error_info.get("code", ""),
                        message=error_info.get("message", ""),
                        http_status=response.status_code
                    )
            except (json.JSONDecodeError, KeyError):
                pass
            # If not in error format, return HTTP error
            raise HTTPError(response.status_code, data)
        
        # Parse successful response
        if len(data) > 0 and data != b"null":
            try:
                return response.json()
            except json.JSONDecodeError:
                return data.decode('utf-8') if isinstance(data, bytes) else data
        return None

    def create_llm_session(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Create a new session in LLM Proxy.
        
        Example:
            resp = client.create_llm_session({
                "title": "My Session",
                "source": "my-app",
                "user_id": "user123",
                "tags": ["alpha", "beta"]
            })
        """
        if request is None:
            raise ErrNilRequest("create_llm_session requires a request payload")
        return self._do_llm_json("POST", "/api/sessions", request, *opts)

    def list_llm_sessions(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        List sessions with optional filtering and pagination.
        
        Example:
            resp = client.list_llm_sessions({
                "user_id": "user123",
                "source": "my-app",
                "page": 1,
                "page_size": 20
            })
        """
        if request is None:
            raise ErrNilRequest("list_llm_sessions requires a request payload")
        
        # Build query parameters
        query_params = {}
        if request.get("user_id"):
            query_params["user_id"] = request["user_id"]
        if request.get("source"):
            query_params["source"] = request["source"]
        if request.get("keyword"):
            query_params["keyword"] = request["keyword"]
        if request.get("tags"):
            tags = request["tags"]
            if isinstance(tags, list):
                query_params["tags"] = ",".join(tags)
            else:
                query_params["tags"] = tags
        if request.get("page"):
            query_params["page"] = str(request["page"])
        if request.get("page_size"):
            query_params["page_size"] = str(request["page_size"])
        
        # Add query params to call options
        from .options import with_query
        opts_list = list(opts)
        if query_params:
            opts_list.append(with_query(query_params))
        
        return self._do_llm_json("GET", "/api/sessions", None, *opts_list)

    def get_llm_session(self, session_id: int, *opts: CallOption) -> Any:
        """
        Retrieve a single session by ID.
        
        Example:
            session = client.get_llm_session(1)
        """
        return self._do_llm_json("GET", f"/api/sessions/{session_id}", None, *opts)

    def update_llm_session(self, session_id: int, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Update a session (supports partial updates).
        
        Example:
            updated = client.update_llm_session(1, {
                "title": "Updated Title",
                "tags": ["release"]
            })
        """
        if request is None:
            raise ErrNilRequest("update_llm_session requires a request payload")
        return self._do_llm_json("PUT", f"/api/sessions/{session_id}", request, *opts)

    def delete_llm_session(self, session_id: int, *opts: CallOption) -> Any:
        """
        Delete a session.
        
        Example:
            client.delete_llm_session(1)
        """
        return self._do_llm_json("DELETE", f"/api/sessions/{session_id}", None, *opts)

    def list_llm_session_messages(self, session_id: int, request: Optional[Dict[str, Any]] = None, *opts: CallOption) -> Any:
        """
        List messages for a specific session with optional filtering.
        
        The messages list endpoint does not return original_content and content fields
        to reduce data transfer. Use get_llm_chat_message to get full message content.
        
        Args:
            session_id: The session ID
            request: Optional dict with filtering parameters:
                - source: Filter by source
                - role: Filter by role (e.g., "user", "assistant")
                - status: Filter by status (e.g., "success", "failed")
                - model: Filter by model
                - after: Get messages after this message ID (exclusive, > relation)
                - limit: Limit number of messages to return (default 20, max 100)
        
        Example:
            messages = client.list_llm_session_messages(1, {
                "role": "user",
                "status": "success",
                "after": 5,   # Get messages after message ID 5
                "limit": 50   # Limit to 50 messages
            })
            for msg in messages:
                print(f"Message ID: {msg['id']}")
        """
        if request is None:
            request = {}
        
        # Build query parameters
        query_params = {}
        if request.get("source"):
            query_params["source"] = request["source"]
        if request.get("role"):
            query_params["role"] = request["role"]
        if request.get("status"):
            query_params["status"] = request["status"]
        if request.get("model"):
            query_params["model"] = request["model"]
        if request.get("after") is not None:
            query_params["after"] = str(request["after"])
        if request.get("limit") is not None:
            query_params["limit"] = str(request["limit"])
        
        # Add query params to call options
        from .options import with_query
        opts_list = list(opts)
        if query_params:
            opts_list.append(with_query(query_params))
        
        return self._do_llm_json("GET", f"/api/sessions/{session_id}/messages", None, *opts_list)

    def get_llm_session_latest_completed_message(self, session_id: int, *opts: CallOption) -> Any:
        """
        Retrieve the latest completed message ID for a session.
        
        This method only returns messages with status "success".
        
        Example:
            resp = client.get_llm_session_latest_completed_message(1)
        """
        return self._do_llm_json("GET", f"/api/sessions/{session_id}/messages/latest-completed", None, *opts)

    def get_llm_session_latest_message(self, session_id: int, *opts: CallOption) -> Any:
        """
        Retrieve the latest message ID for a session (regardless of status).
        
        This method differs from get_llm_session_latest_completed_message:
        - get_llm_session_latest_completed_message: only returns messages with status "success"
        - get_llm_session_latest_message: returns the latest message regardless of status (success, failed, retry, aborted, etc.)
        
        Example:
            resp = client.get_llm_session_latest_message(1)
        """
        return self._do_llm_json("GET", f"/api/sessions/{session_id}/messages/latest", None, *opts)

    def modify_llm_session_message_response(self, session_id: int, message_id: int, modified_response: str, *opts: CallOption) -> Any:
        """
        Modify the modified_response field of a message in a session.
        
        The request body is sent as plain text (not JSON), containing the modified response content.
        
        Args:
            session_id: The session ID
            message_id: The message ID
            modified_response: The modified response content (plain text)
            *opts: Optional call configuration options
        
        Returns:
            Response containing session_id, message_id, and modified_response
        
        Example:
            resp = client.modify_llm_session_message_response(1, 10, "This is the modified response")
            print(f"Modified message ID: {resp['message_id']}")
        """
        if self is None:
            raise ValueError("sdk client is None")
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build full URL with /llm-proxy prefix
        full_path = f"/llm-proxy/api/sessions/{session_id}/messages/{message_id}/modify-response"
        url = self._build_url(full_path, call_opts.query_params)
        
        # Build headers
        headers = self._build_headers(call_opts)
        headers["Content-Type"] = "text/plain"
        headers["Accept"] = "application/json"
        
        # Make request with plain text body
        response = self._http_client.request(
            method="PUT",
            url=url,
            headers=headers,
            data=modified_response.encode('utf-8'),
            timeout=self._timeout
        )
        
        # Read response body
        data = response.content
        
        # Check for error response format
        if response.status_code >= 400:
            try:
                err_data = response.json()
                if isinstance(err_data, dict) and "error" in err_data:
                    error_info = err_data["error"]
                    raise APIError(
                        code=error_info.get("code", ""),
                        message=error_info.get("message", ""),
                        http_status=response.status_code
                    )
            except (json.JSONDecodeError, ValueError):
                pass
            # If not in error format, return HTTP error
            raise HTTPError(response.status_code, data)
        
        # Parse successful response
        if len(data) > 0 and data != b"null":
            try:
                return response.json()
            except json.JSONDecodeError:
                return data.decode('utf-8') if isinstance(data, bytes) else data
        return None

    def append_llm_session_message_modified_response(self, session_id: int, message_id: int, append_content: str, *opts: CallOption) -> Any:
        """
        Append content to the modified_response field of a message in a session.
        
        The request body is sent as plain text (not JSON), containing the content to append.
        The content will be appended to the existing modified_response field.
        
        Args:
            session_id: The session ID
            message_id: The message ID
            append_content: The content to append (plain text)
            *opts: Optional call configuration options
        
        Returns:
            Response containing session_id, message_id, and append_content
        
        Example:
            resp = client.append_llm_session_message_modified_response(1, 10, "Additional content to append")
            print(f"Appended content to message ID: {resp['message_id']}")
        """
        if self is None:
            raise ValueError("sdk client is None")
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build full URL with /llm-proxy prefix
        full_path = f"/llm-proxy/api/sessions/{session_id}/messages/{message_id}/append-modified-response"
        url = self._build_url(full_path, call_opts.query_params)
        
        # Build headers
        headers = self._build_headers(call_opts)
        headers["Content-Type"] = "text/plain"
        headers["Accept"] = "application/json"
        
        # Make request with plain text body
        response = self._http_client.request(
            method="POST",
            url=url,
            headers=headers,
            data=append_content.encode('utf-8'),
            timeout=self._timeout
        )
        
        # Read response body
        data = response.content
        
        # Check for error response format
        if response.status_code >= 400:
            try:
                err_data = response.json()
                if isinstance(err_data, dict) and "error" in err_data:
                    error_info = err_data["error"]
                    raise APIError(
                        code=error_info.get("code", ""),
                        message=error_info.get("message", ""),
                        http_status=response.status_code
                    )
            except (json.JSONDecodeError, ValueError):
                pass
            # If not in error format, return HTTP error
            raise HTTPError(response.status_code, data)
        
        # Parse successful response
        if len(data) > 0 and data != b"null":
            try:
                return response.json()
            except json.JSONDecodeError:
                return data.decode('utf-8') if isinstance(data, bytes) else data
        return None

    def create_llm_chat_message(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Create a new chat message record.
        
        Args:
            request: Dict with message fields:
                - user_id: User ID (required)
                - source: Source identifier (required)
                - role: Message role (required, e.g., "user", "assistant")
                - content: Message content (required)
                - model: Model name (required)
                - session_id: Session ID (optional)
                - status: Message status (optional, default: "success")
                - response: LLM reply content (optional)
                - config: Message configuration as JSON string (optional)
                - tags: Tag names list (optional)
        
        Example:
            msg = client.create_llm_chat_message({
                "user_id": "user123",
                "source": "my-app",
                "role": "user",
                "content": "Hello, world!",
                "model": "gpt-4",
                "status": "success",
                "config": '{"temperature": 0.7}',
                "tags": ["tag1", "tag2"]
            })
        """
        if request is None:
            raise ErrNilRequest("create_llm_chat_message requires a request payload")
        return self._do_llm_json("POST", "/api/chat-messages", request, *opts)


    def get_llm_chat_message(self, message_id: int, *opts: CallOption) -> Any:
        """
        Retrieve a single chat message by ID.
        
        Example:
            msg = client.get_llm_chat_message(1)
        """
        return self._do_llm_json("GET", f"/api/chat-messages/{message_id}", None, *opts)

    def update_llm_chat_message(self, message_id: int, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Update a chat message.
        
        Args:
            message_id: The message ID
            request: Dict with optional fields to update:
                - status: Message status (e.g., "success", "failed")
                - response: LLM reply content (for streaming, use CONCAT to append)
                - modified_response: Modified reply content
                - content: Actual content sent to LLM
                - config: Message configuration as JSON string (optional)
                - tags: Tag list (complete replacement)
        
        Example:
            updated = client.update_llm_chat_message(1, {
                "status": "success",
                "response": "Updated response",
                "modified_response": "Modified response",
                "config": '{"temperature": 0.8}'
            })
        """
        if request is None:
            raise ErrNilRequest("update_llm_chat_message requires a request payload")
        return self._do_llm_json("PUT", f"/api/chat-messages/{message_id}", request, *opts)

    def delete_llm_chat_message(self, message_id: int, *opts: CallOption) -> Any:
        """
        Delete a chat message.
        
        Example:
            client.delete_llm_chat_message(1)
        """
        return self._do_llm_json("DELETE", f"/api/chat-messages/{message_id}", None, *opts)

    def update_llm_chat_message_tags(self, message_id: int, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Update message tags (complete replacement).
        
        Example:
            updated = client.update_llm_chat_message_tags(1, {
                "tags": ["tag1", "tag2", "tag3"]
            })
        """
        if request is None:
            raise ErrNilRequest("update_llm_chat_message_tags requires a request payload")
        return self._do_llm_json("PUT", f"/api/chat-messages/{message_id}/tags", request, *opts)

    def delete_llm_chat_message_tag(self, message_id: int, source: str, name: str, *opts: CallOption) -> Any:
        """
        Delete a single tag from a message.
        
        Example:
            client.delete_llm_chat_message_tag(1, "my-app", "tag1")
        """
        from urllib.parse import quote
        path = f"/api/chat-messages/{message_id}/tags/{quote(source)}/{quote(name)}"
        return self._do_llm_json("DELETE", path, None, *opts)

    # ----------------------------------------------------------------------
    # Data Analysis APIs
    # ----------------------------------------------------------------------

    def analyze_data_stream(
        self,
        request: Optional[Dict[str, Any]],
        *opts: CallOption
    ) -> DataAnalysisStream:
        """
        Perform data analysis and return a streaming response.
        
        This method sends a POST request to /byoa/api/v1/data_asking/analyze and
        returns a stream of Server-Sent Events (SSE) containing analysis results.
        
        The stream includes events such as:
          - init: Initialization event (first event) with request_id and session_title
            (step_type="init", data contains request_id and session_title)
          - classification: Question classification result
          - decomposition: Attribution question decomposition (attribution only)
          - step_start: Step start (attribution only)
          - step_complete: Step completion (attribution only)
          - chunks/answer_chunk: RAG interface data (with source="rag")
          - step_type/step_name: NL2SQL interface data (with source="nl2sql")
          - complete: Analysis complete
          - error: Error information
        
        Args:
            request: DataAnalysisRequest dict with question and optional config
            *opts: Optional call configuration options
        
        Returns:
            DataAnalysisStream object for reading SSE events
        
        Example:
            stream = client.analyze_data_stream({
                "question": "2024年收入下降的原因是什么？",
                "session_id": "session_123",
                "config": {
                    "data_category": "admin",
                    "data_source": {
                        "type": "all"
                    }
                }
            }, with_stream_buffer_size(1024 * 1024))  # Optional: set buffer size for large data lines
            try:
                while True:
                    event = stream.read_event()
                    if event is None:
                        break
                    print(f"Event type: {event.type}")
            finally:
                stream.close()
        """
        if request is None:
            raise ErrNilRequest("analyze_data_stream requires a request payload")
        
        question = request.get("question", "").strip() if isinstance(request, dict) else ""
        if not question:
            raise ValueError("question cannot be empty")
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build URL
        path = "/byoa/api/v1/data_asking/analyze"
        url = self._build_url(path, call_opts.query_params)
        
        # Serialize body
        payload = self._prepare_body(request)
        json_body = json.dumps(payload, default=str)
        
        # Build headers
        headers = self._build_headers(call_opts, "application/json")
        # Override Accept header for SSE
        headers["Accept"] = "text/event-stream"
        
        # Make request with stream=True
        response = self._http_client.request(
            method="POST",
            url=url,
            headers=headers,
            data=json_body,
            timeout=self._timeout,
            stream=True
        )
        
        # Check for HTTP errors
        if not (200 <= response.status_code < 300):
            body = response.content
            response.close()
            raise HTTPError(response.status_code, body)
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if "text/event-stream" not in content_type and "text/plain" not in content_type:
            # Not a streaming response, try to parse as error
            body = response.content
            response.close()
            raise ValueError(f"unexpected content type: {content_type}, body: {body.decode('utf-8', errors='ignore')}")
        
        return DataAnalysisStream(response, initial_buffer_size=call_opts.stream_buffer_size)

    def cancel_analyze(self, request: Optional[Dict[str, Any]], *opts: CallOption) -> Any:
        """
        Cancel an ongoing data analysis request.
        
        This method sends a POST request to /byoa/api/v1/data_asking/cancel to cancel
        a data analysis request that is currently in progress.
        
        The request_id parameter identifies the analysis request to cancel. Only the
        user who initiated the request can cancel it.
        
        Args:
            request: CancelAnalyzeRequest dict with request_id
            *opts: Optional call configuration options
        
        Returns:
            CancelAnalyzeResponse dict with request_id, status, user_id, and user_name
        
        Example:
            resp = client.cancel_analyze({
                "request_id": "request-123"
            })
            print(f"Cancelled request: {resp['request_id']}, Status: {resp['status']}, User: {resp.get('user_name', '')}")
        """
        if request is None:
            raise ErrNilRequest("cancel_analyze requires a request payload")
        
        request_id = request.get("request_id", "").strip() if isinstance(request, dict) else ""
        if not request_id:
            raise ValueError("request_id cannot be empty")
        
        # Add request_id as query parameter
        from .options import with_query_param
        opts = list(opts) + [with_query_param("request_id", request_id)]
        
        # Build call options
        call_opts = CallOptions()
        for opt in opts:
            if opt is not None:
                opt(call_opts)
        
        # Build URL
        path = "/byoa/api/v1/data_asking/cancel"
        url = self._build_url(path, call_opts.query_params)
        
        # Build headers
        headers = self._build_headers(call_opts)
        
        # Make POST request with empty body (request_id is in query params)
        response = self._http_client.request(
            method="POST",
            url=url,
            headers=headers,
            data=None,
            timeout=self._timeout
        )
        
        # Parse response
        return self._parse_response(response)

