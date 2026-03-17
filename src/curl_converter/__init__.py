"""
curl_converter - Parse and manipulate curl command strings.
"""

from .converter import (
    Curl,
    Headers,
    Cookies,
    Data,
    Params,
    parse_method,
    parse_url,
    parse_params,
    parse_curl_headers,
    parse_curl_cookies,
    parse_curl_data,
    parse_curl_part,
    read_str,
    bisect,
)

__version__ = "0.1.0"

__all__ = [
    "Curl",
    "Headers",
    "Cookies",
    "Data",
    "Params",
    "parse_method",
    "parse_url",
    "parse_params",
    "parse_curl_headers",
    "parse_curl_cookies",
    "parse_curl_data",
    "parse_curl_part",
    "read_str",
    "bisect",
]
