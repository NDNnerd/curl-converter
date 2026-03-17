# Curl Converter

Python class for for parsing and manipulating curl strings.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)

Curl Converter is my favorite VS Code extension, but lately it has stopped working. This is a quick substitute. The module has not been tested extensively, but it works on curl strings I commonly use. Good luck!

## Installation

To install Curl Converter run the following command:

```
pip install curl-converter
```


## Usage:

Curl Converter accepts:
- curl string
- list of curl parameters
- path to a text file containing a curl string

### A Curl String Example:

``` python
from curl_converter import Curl

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
    # Note: No curl string actually looks like this as data parameters are typically for POST requests.

curl = Curl(curl_str)
print(curl.data)  
# Output: Data={'session-data': 'abcdefg'}

```

_Please Note:_
To properly parse, the curl string needs to have line breaks after each parameter.  
If curl string lines end with the backslash symbol ('\'), you need to put it in a text file and read it in as a path.

``` curl
curl 'https://pypi.org/search/?q=curl'  \ <-- This is a 'ignore line-break' symbol in python
[... more curl commands ...]
```


### A Text File Example:

``` python
from curl_converter import Curl, read_curl_str

curl = Curl('path/to/curl/string.txt')

# - or -
curl_str = read_curl_str('path/to/curl/string.txt')
curl = Curl(curl_str)

```

### Parse a curl component individually:

``` python
from curl_converter import parse_curl_method, parse_curl_url, parse_curl_params

print(parse_curl_method(curl_str))
# Output: GET

print(parse_curl_url(curl_str, remove_params = True))
# Output: https://pypi.org/search/

print(parse_curl_params(curl_str))
# Output: {'q': 'curl'}

```

### 2. Parse individual components indo a class with dictionary-like methods:

``` python
from curl_converter import Headers

headers = Headers(curl_str)

print(headers['accept-language'])
# Output: en-US,en;q=0.8

print(headers.get('aCCepT-laNguaGe', 'en-UK')) # A header that doesn't exist
# Output: en-UK

headers.update(_user_agents['windows']['chrome']) # Update a header
print(headers['user-agent'])
# Output: user-agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36

```

