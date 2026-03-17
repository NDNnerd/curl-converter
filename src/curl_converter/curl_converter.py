#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A Class for parsing and manipulating curl strings.
"""

import shlex
import re
import json                                                     
import requests
from pathlib import Path                                        
from functools import partial
from urllib.parse import urlparse, parse_qs, unquote_plus
from typing import  Any, Callable, Dict, List, Optional, Union

def _strip(s:str):
    """Strip quotes and backslashes (common curl ending chars) from a string."""
    return re.sub(r"\s+", ' ', s).strip("\\ '")

PREFIX_PATTERN = re.compile(r'^--?[a-zA-Z\-]+\s?')
CURL_METHOD_PREFIXES = ['-X', '--request']
CURL_URL_PREFIXES = ['curl', 'http']
CURL_PARAM_PREFIXES = ['-G', '--get', '--post', '--put', '--delete', '--request']
CURL_HEADER_PREFIXES = ['-H', '--headers']
CURL_COOKIE_PREFIXES = ['-b', '--cookie']
CURL_DATA_PREFIXES = ['-d', '--data', '--data-raw', '--data-urlencode', '--data-binary']


_user_agents = {
    'windows': {
        'chrome': {
            'sec-ch-ua': '"Not A;Brand";v="99", "Chromium";v="145", "Google Chrome";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            }
        },
    'android': {
        'firefox': {
            'user-agent': 'Mozilla/5.0 (Android 4.4; Tablet; rv:70.0) Gecko/70.0 Firefox/70.0'
            }
        }
}

__doc__ = r"""
Curl Converter is a Python class for converting curl strings into Python dictionaries.

Accepts:
    - curl string or file path to a curl string
    - list of curl parameters

    curl_str = '''
        curl 'https://pypi.org/search/?q=curl' 
        -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8' 
        -H 'accept-language: en-US,en;q=0.8' 
        -H 'cache-control: no-cache' 
        -b 'session_id=123456789' 
        -H 'pragma: no-cache' 
        -H 'priority: u=0, i' 
        -H 'sec-fetch-dest: document' 
        -H 'sec-fetch-mode: navigate' 
        -H 'sec-fetch-site: none' 
        -H 'sec-fetch-user: ?1' 
        -H 'sec-gpc: 1' 
        -H 'upgrade-insecure-requests: 1' 
        -H 'user-agent: Mozilla/5.0 (Android 4.4; Tablet; rv:70.0) Gecko/70.0 Firefox/70.0'
        --data-raw '{"session-data":"abcdefg"}'
        '''

    _Please Note:_
    To properly parse, the curl string needs to have line breaks after each parameter.  
    If curl string lines end with the backslash symbol ('\'), you need to put it in a text file and read it in using the `read_curl_str` function.
    
    ``` curl
    curl 'https://pypi.org/search/?q=curl'  \ <-- This is a 'ignore line-break' symbol in python
    [...]

    ```

Usage:

1. Parse a curl component individually:

    >>> print(parse_curl_method(curl_str))
    GET

    >>> print(parse_curl_url(curl_str, remove_params = True))
    https://pypi.org/search/

    >>> print(parse_curl_params(curl_str))
    {'q': 'curl'}

2. Parse individual components indo a class with dictionary-like methods:

    >>> headers = Headers(curl_str)
    >>> for k, v in headers.items():
    >>>     print(f"{k}: {v}")

        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8
        accept-language: en-US,en;q=0.8
        cache-control: no-cache
        pragma: no-cache
        priority: u=0, i
        sec-fetch-dest: document
        sec-fetch-mode: navigate
        sec-fetch-site: none
        sec-fetch-user: ?1
        sec-gpc: 1
        upgrade-insecure-requests: 1
        user-agent: Mozilla/5.0 (Android 4.4; Tablet; rv:70.0) Gecko/70.0 Firefox/70.0
    
    >>> print(headers['accept-language'])
    en-US,en;q=0.8

    >>> print(headers.get('aCCepT-laNguaGe', 'en-UK')) # A header that doesn't exist
    en-UK

    >>> headers.update(_user_agents['windows']['chrome']) # Update a header
    >>> print(headers['user-agent'])
    user-agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36

3. Full Curl Class:

    >>> curl = Curl(curl_str)
    >>> print(curl.data)
    Data={'session-data': 'abcdefg'}
"""

# Helper Functions

def read_curl_str(string: Union[str, Path]):
    """Read a string or Path-like object and return its contents as a string."""
    if isinstance(string, Path):
        return string.read_text()

    elif isinstance(string, str):
        try:
            return Path(string).read_text()
        except:
            return string
    
    else:
        raise ValueError(f'Invalid string type: {type(string)}. Must be str, Path, or Path-like string object.')

def bisect(p:str, sep:str):
    """Split a string by a separator and return exactly two parts."""

    if sep not in p:
        raise ValueError(f'Invalid parse: {p}')                # BUG 4: was `parts_str` (undefined)
    
    p = [_strip(q) for q in p.split(sep) if _strip(q)]
    
    if len(p) > 2:
        p = [p[0], sep.join(p[1:])]
    
    return p

def parse_curl_part(parts: Union[str, List[str]], prefixes: List[str] = None, sep: str = None):
    """Parse a list of strings into a dictionary of key-value pairs."""
    
    if isinstance(parts, str):
        if '\n' in parts:
            parts = [p for p in parts.split('\n')]
        else:
            parts = [parts]

    parts = [_strip(p) for p in parts if _strip(p)]

    if len(parts) == 0:
        return None

    if prefixes:
        # Filter by prefixes
        parts = [p for p in parts if any(p.startswith(x) for x in prefixes) and _strip(p)]

    if not parts:
        return None

    # Remove prefixes (even if prefixes were not specified)
    parts = [_strip(re.sub(PREFIX_PATTERN, '', p)) for p in parts if _strip(p)]

    # Split by separator
    if not sep:
        return parts
    
    parts = [bisect(p, sep) for p in parts]
    return {p[0]: p[1] for p in parts}


# Part Specific Functions

def parse_curl_method(curl, prefixes = CURL_METHOD_PREFIXES):
    """Parse the first method from a curl string."""
    method = parse_curl_part(curl, prefixes)
    return method[0] if method else 'GET'

def parse_curl_url(curl, prefixes = CURL_URL_PREFIXES, remove_params = False):
    """Parse the URL from a curl string."""
    url = parse_curl_part(curl, prefixes)
    url = ''.join([_strip(re.sub(r'^curl\s?', '', c)) for c in url])
    url = _strip(url)
    
    if remove_params:
        return url.split('?')[0]
    return url

def parse_curl_params(curl):
    url = parse_curl_url(curl, remove_params = False)

    if '?' not in url:
        return None
    
    params = _strip(url.split('?')[1])
    return parse_curl_part(params.split('&'), sep = '=')
    
def parse_curl_headers(curl, prefixes = CURL_HEADER_PREFIXES):
    return parse_curl_part(curl, prefixes, sep = ':')

def parse_curl_cookies(curl, prefixes = CURL_COOKIE_PREFIXES):
    return parse_curl_part(curl, prefixes, sep = '=')

def parse_curl_data(curl, prefixes = CURL_DATA_PREFIXES):
    data = [c for c in curl if any(c.startswith(x) for x in prefixes) and _strip(c)]

    if not data:
        return None

    raw = _strip(re.sub(PREFIX_PATTERN, '', data[0]))
    return json.loads(raw)

# Template Class

class TemplateClass(dict):                                      
    def __init__(self, curl: Union[str, List[str]], parse_func: Callable = lambda curl: curl):
        
        if isinstance(curl, str):
            curl = [_strip(c) for c in curl.split('\n') if _strip(c)]
        
        parsed = parse_func(curl)
        if parsed is None:
            parsed = {}
        super().__init__(parsed)                                
        self.parse_func = parse_func

    def __repr__(self):
        return (f"{self.__class__.__name__}={dict.__repr__(self)}")  
    
    def __str__(self):
        return dict.__str__(self)                               
    
    def _set(self, new_curl: Union[str, List[str]]):
        return TemplateClass(new_curl, parse_func = self.parse_func)

    def update(self, new_curl: Union[str, List[str]]):
        if isinstance(new_curl, dict):
            super().update(new_curl)
            
        else:
            new = self._set(new_curl)                           
            super().update(new)
    
    def drop(self, keys: Union[str, List[str]]):
        for key in keys:
            super().pop(key)
    
    def omit(self, keys: Union[str, List[str]]):
        return {k: v for k, v in self.items() if k not in keys}

class Headers(TemplateClass):
    def __init__(self, curl: Union[str, List[str]], **kwargs):  # BUG 6: added **kwargs to accept prefixes
        prefixes = kwargs.get('prefixes', CURL_HEADER_PREFIXES)
        super().__init__(curl, parse_func = lambda c: parse_curl_headers(c, prefixes))

class Cookies(TemplateClass):
    def __init__(self, curl: Union[str, List[str]], **kwargs):  # BUG 6: added **kwargs to accept prefixes
        prefixes = kwargs.get('prefixes', CURL_COOKIE_PREFIXES)
        super().__init__(curl, parse_func = lambda c: parse_curl_cookies(c, prefixes))

    def update(self, cookies):
        if isinstance(cookies, requests.cookies.RequestsCookieJar):
            cookies = cookies.get_dict()
        elif isinstance(cookies, requests.models.Response):
            cookies = cookies.cookies.get_dict()
        if isinstance(cookies, dict):
            for key, value in cookies.items():
                self[key] = value
        else:
            super().update(cookies)

class Data(TemplateClass):
    def __init__(self, curl: Union[str, List[str]], **kwargs):  # BUG 6: added **kwargs to accept prefixes
        prefixes = kwargs.get('prefixes', CURL_DATA_PREFIXES)
        super().__init__(curl, parse_func = lambda c: parse_curl_data(c, prefixes))

class Params(TemplateClass):
    def __init__(self, curl: Union[str, List[str]]):
        super().__init__(curl, parse_func = parse_params)


class Curl:
    def __init__(self, curl: Union[str, Path, List[str]], **kwargs):
        
        if isinstance(curl, str) or isinstance(curl, Path):
            self.curl_str = read_curl_str(curl)                      
            self.curl = [_strip(c) for c in self.curl_str.split('\n') if _strip(c)] # Split by newline
        
        elif isinstance(curl, list):
            self.curl = curl
            self.curl_str = '\n'.join(curl)                     

        # Parse the curl string
        self.method = parse_curl_method(self.curl, prefixes = kwargs.get('method_prefixes', CURL_METHOD_PREFIXES))
        if 'method' in kwargs:
            self.method = kwargs['method']

        self.url = parse_curl_url(self.curl, prefixes = kwargs.get('url_prefixes', CURL_URL_PREFIXES))  # BUG 5: was `self.parse_url(...)`
        if 'url' in kwargs:
            self.url = kwargs['url']

        self.params = Params(self.curl)
        if 'params' in kwargs:
            self.params.update(kwargs['params'])

        self.headers = Headers(self.curl, prefixes = kwargs.get('header_prefixes', CURL_HEADER_PREFIXES))
        if 'headers' in kwargs:
            self.headers.update(kwargs['headers'])

        self.cookies = Cookies(self.curl, prefixes = kwargs.get('cookie_prefixes', CURL_COOKIE_PREFIXES))
        if 'cookies' in kwargs:
            self.cookies.update(kwargs['cookies'])

        self.data = Data(self.curl, prefixes = kwargs.get('data_prefixes', CURL_DATA_PREFIXES))
        if 'data' in kwargs:
            self.data.update(kwargs['data'])
    
        self.__doc__ = __doc__
    
    def __repr__(self):
        return (f"Curl(method={self.method!r}, url={self.url!r}, params={self.params!r})")
    
    def __str__(self):
        out_string = ["Curl("]
        if self.method:
            out_string.append(f"  Method={self.method!r}, ")
        if self.url:
            out_string.append(f"  URL={self.url!r}, ")
        if self.params:
            out_string.append(f"  {self.params!r}, ")
        if self.headers:
            out_string.append(f"  {self.headers!r}, ")
        if self.cookies:
            out_string.append(f"  {self.cookies!r}, ")
        if self.data:
            out_string.append(f"  {self.data!r}, ")
        
        out_string.append(")")
        return ('\n'.join(out_string))
    
    def _set(self, new_curl: Union[str, List[str]], **kwargs):
        return Curl(new_curl, **kwargs)                         # BUG 11: was referencing `self.parse_func` which doesn't exist
    
    def update(self, new_curl: Union[str, List[str]], **kwargs):  # BUG 10: added **kwargs (was referencing __init__'s kwargs)
        new_method = parse_method(new_curl, prefixes = kwargs.get('method_prefixes', CURL_METHOD_PREFIXES))
        self.method = new_method if new_method else self.method

        new_url = parse_url(new_curl, prefixes = kwargs.get('url_prefixes', CURL_URL_PREFIXES))
        self.url = new_url if new_url else self.url

        new_headers = Headers(new_curl, prefixes = kwargs.get('header_prefixes', CURL_HEADER_PREFIXES))
        self.headers = new_headers if new_headers else self.headers

        new_cookies = Cookies(new_curl, prefixes = kwargs.get('cookie_prefixes', CURL_COOKIE_PREFIXES))
        self.cookies = new_cookies if new_cookies else self.cookies

        new_data = Data(new_curl, prefixes = kwargs.get('data_prefixes', CURL_DATA_PREFIXES))
        self.data = new_data if new_data else self.data

        new_params = Params(new_curl)
        self.params = new_params if new_params else self.params

    def request(self, method = 'GET'):
        req_kwargs = {}
        for attr in ['headers', 'cookies', 'params', 'data']:
            if getattr(self, attr):
                req_kwargs[attr] = getattr(self, attr)
        
        if method.upper() == 'GET':
            return requests.get(self.url, **req_kwargs)
        
        elif method.upper() == 'POST':
            return requests.post(self.url, **req_kwargs)
    
    def get(self):
        return self.request('GET')
    
    def post(self):
        return self.request('POST')



if __name__ == "__main__":


    


    print(parse_curl_cookies(curl))
    print(parse_curl_data(curl))

    headers = Headers(curl)
    print(headers)
    print(headers['accept-language'])
    print(headers.get('aCCepT-laNguaGe', 'en-UK'))
    headers.update({'accept-language': 'en-UK'})
    print(headers['accept-language'])
    headers.update(_user_agents['windows']['chrome'])
    print(headers['user-agent'])

    cookies = Cookies(curl_str)
    print(cookies)

    data = Data(curl)
    print(data)

    params = Params(curl)
    print(params)

    curl = Curl(curl_str)
    print(curl.__doc__)
    print(curl)
    print(curl.headers)
    curl.headers.update({'accept-language': 'en-UK'})
    print(curl.headers['accept-language'])


