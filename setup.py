"""Setup configuration for the MOI Python SDK."""

from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

setup(
    name="moi-python-sdk",
    version="0.1.0",
    description="Python client SDK for the MOI Catalog Service",
    long_description=README,
    long_description_content_type="text/markdown",
    author="MatrixOrigin",
    url="https://github.com/matrixorigin/moi-python-sdk",
    packages=find_packages(include=("moi", "moi.*")),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
    ],
    include_package_data=True,
    license="Apache-2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)

