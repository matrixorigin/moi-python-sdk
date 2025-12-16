"""Setup configuration for the MOI Python SDK.

The actual project metadata lives in pyproject.toml so uv can be the single
source of truth. This file simply mirrors that metadata for tooling that still
invokes setup.py directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

try:  # Python 3.11+ ships tomllib in the standard library.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for <=3.10.
    import tomli as tomllib  # type: ignore[import]

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
PROJECT = PYPROJECT.get("project", {})


def _join_field(items: Iterable[dict], field: str) -> str | None:
    """Return a comma separated string of the requested field."""
    values = [item.get(field) for item in items if item.get(field)]
    return ", ".join(values) if values else None


setup(
    name=PROJECT.get("name"),
    version=PROJECT.get("version"),
    description=PROJECT.get("description"),
    long_description=README,
    long_description_content_type="text/markdown",
    author=_join_field(PROJECT.get("authors", []), "name"),
    license=(PROJECT.get("license") or {}).get("text"),
    url=(PROJECT.get("urls") or {}).get("Homepage"),
    project_urls=PROJECT.get("urls"),
    packages=find_packages(include=("moi", "moi.*")),
    python_requires=PROJECT.get("requires-python"),
    install_requires=PROJECT.get("dependencies", []),
    classifiers=PROJECT.get("classifiers", []),
    include_package_data=True,
)
