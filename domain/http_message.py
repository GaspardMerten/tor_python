import re

import requests

from models.http_message import RawHttpRequest, RawHttpResponse

# A fat regex coded by hand to parse HTTP messages (requests)
http_message_request_compiled_regex = re.compile(
    r"([A-Z]+)\s(/.*)\sHTTP/([1-2](?:.[0-2])?)\sHost:\s(.*)\n((?:[\S ]*:[\S ]*\s?)*)(?:\s\s([\s\S]*))?",
    re.MULTILINE)

# Another fat regex coded by hand to parse HTTP messages (responses)
http_message_response_compiled_regex = re.compile(
    r"([0-9]{3}) ([a-zA-Z]*)\s(\S*)(?:\n((?:[\S ]*:[\S ]*\s?)*))(?:\s([\s\S]*))?",
    re.MULTILINE)


def extract_data_from_http_raw_request(raw_message: str) -> RawHttpRequest:
    """
    Extracts data from a raw HTTP request message
    :param raw_message: The raw HTTP request message
    :return: A RawHttpRequest object
    """

    match = http_message_request_compiled_regex.match(raw_message, )
    method = match.group(1)
    path = match.group(2)
    http_version = match.group(3)
    host = match.group(4)
    raw_headers = match.group(5)
    body = match.group(6)

    return RawHttpRequest(host, http_version, path, method, raw_headers, body)


def extract_data_from_http_raw_response(raw_message: str) -> RawHttpResponse:
    """
    Extracts data from a raw HTTP response message
    :param raw_message: The raw HTTP response message
    :return: A RawHttpResponse object
    """
    match = http_message_response_compiled_regex.match(raw_message, )
    status_code = match.group(1)
    status = match.group(2)
    url = match.group(3)
    raw_headers = match.group(4)
    body = match.group(5)

    return RawHttpResponse(status_code, status, url, raw_headers, body)


def response_object_to_raw_http_message(response):
    """
    Converts a requests.Response object to a raw HTTP message
    :param response: The requests.Response object
    :return: A raw HTTP message
    """

    def format_headers(d):
        return '\n'.join(f'{k}: {v}' for k, v in d.items())

    return f"""{response.status_code} {response.reason} {response.url}\n{format_headers(response.headers)}\n\n{response.text}"""


def send_http_request_from_raw_http_message(raw_http_message: str) -> str:
    """
    Sends an HTTP request from a raw HTTP message
    :param raw_http_message: The raw HTTP message
    :return: A raw HTTP response message using the response_object_to_raw_http_message function
    """
    raw_message: RawHttpRequest = extract_data_from_http_raw_request(raw_http_message)

    if ":443" in raw_message.host:
        protocol = "HTTPS"
    elif raw_message.http_version[0] == "2" and ":80" not in raw_message.host:
        protocol = "HTTPS"
    else:
        protocol = "HTTP"

    if raw_message.method == "POST":
        request_func = requests.post
    elif raw_message.method == "PUT":
        request_func = requests.put
    elif raw_message.method == "DELETE":
        request_func = requests.delete
    elif raw_message.method == "OPTIONS":
        request_func = requests.options
    elif raw_message.method == "HEAD":
        request_func = requests.head
    elif raw_message.method == "PATCH":
        request_func = requests.patch
    else:
        request_func = requests.get

    headers = {}

    for header_line in raw_message.headers.splitlines():
        if ": " in header_line:
            header_name, header_value = header_line.split(": ")
            headers[header_name] = header_value
    print("HERE")
    response = request_func(
        f"{protocol}://{raw_message.host}{raw_message.path}",
        headers=headers,
        data=raw_message.body,
        timeout=10
    )

    return response_object_to_raw_http_message(response)
