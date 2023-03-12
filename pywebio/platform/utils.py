import fnmatch
import json
import os
import socket
import urllib.parse
from collections import defaultdict

from ..__version__ import __version__ as version
from ..exceptions import PyWebIOWarning


def cdn_validation(cdn, level='warn', stacklevel=3):
    """CDN availability check

    :param bool/str cdn: cdn parameter
    :param level: warn or error
    :param stacklevel: stacklevel=3 to makes the warning refer to cdn_validation() caller’s caller
    """
    assert level in ('warn', 'error')

    if cdn is True and 'dev' in version:
        if level == 'warn':
            import warnings
            warnings.warn("Default CDN is not supported in dev version. Ignore the CDN setting", PyWebIOWarning,
                          stacklevel=stacklevel)
            return False
        else:
            raise ValueError("Default CDN is not supported in dev version. Please host static files by yourself.")

    return cdn


class OriginChecker:

    @classmethod
    def check_origin(cls, origin, allowed_origins, host):
        if cls.is_same_site(origin, host):
            return True

        return any(
            fnmatch.fnmatch(origin, pattern)
            for pattern in allowed_origins
        )

    @staticmethod
    def is_same_site(origin, host):
        """判断 origin 和 host 是否一致。origin 和 host 都为http协议请求头"""
        parsed_origin = urllib.parse.urlparse(origin)
        origin = parsed_origin.netloc
        origin = origin.lower()

        # Check to see that origin matches host directly, including ports
        return origin == host


def deserialize_binary_event(data: bytes):
    """
    Binary event message is used to submit data with files upload to server.

    Data message format:
    | event | file_header | file_data | file_header | file_data | ...

    The 8 bytes at the beginning of each segment indicate the number of bytes remaining in the segment.

    event: {
        ...
        data: {
            input_name => input_data,
            ...
        }
    }

    file_header: {
        'filename': file name,
        'size': file size,
        'mime_type': file type,
        'last_modified': last_modified timestamp,
        'input_name': name of input field
    }

    file_data is the file content in bytes.

     - When a form field is not a file input, the `event['data'][input_name]` will be the value of the form field.
     - When a form field is a single file, the `event['data'][input_name]` is None,
        and there will only be one file_header+file_data at most.
     - When a form field is a multiple files, the `event['data'][input_name]` is [],
        and there may be multiple file_header+file_data.

    Example:
        b'\x00\x00\x00\x00\x00\x00\x00E{"event":"from_submit","task_id":"main-4788341456","data":{"data":1}}\x00\x00\x00\x00\x00\x00\x00Y{"filename":"hello.txt","size":2,"mime_type":"text/plain","last_modified":1617119937.276}\x00\x00\x00\x00\x00\x00\x00\x02ss'
    """
    # split data into segments
    parts = []
    start_idx = 0
    while start_idx < len(data):
        size = int.from_bytes(data[start_idx:start_idx + 8], "big")
        start_idx += 8
        content = data[start_idx:start_idx + size]
        parts.append(content)
        start_idx += size

    event = json.loads(parts[0])

    # deserialize file data
    files = defaultdict(list)
    for idx in range(1, len(parts), 2):
        f = json.loads(parts[idx])
        f['content'] = parts[idx + 1]

        # Security fix: to avoid interpreting file name as path
        f['filename'] = os.path.basename(f['filename'])

        input_name = f.pop('input_name')
        files[input_name].append(f)

    # fill file data to event
    for input_name in list(event['data'].keys()):
        if input_name in files:
            init = event['data'][input_name]
            event['data'][input_name] = files[input_name]
            if init is None:  # the file is not multiple
                event['data'][input_name] = files[input_name][0] if len(files[input_name]) else None
    return event


def get_interface_ip(family: socket.AddressFamily) -> str:
    """Get the IP address of an external interface. Used when binding to
    0.0.0.0 or :: to show a more useful URL.

    Copy from https://github.com/pallets/werkzeug/blob/df7492ab66aaced5eea964a58309caaadb1e8903/src/werkzeug/serving.py
    Under BSD-3-Clause License
    """
    # arbitrary private address
    host = "fd31:f903:5ab5:1::1" if family == socket.AF_INET6 else "10.253.155.219"

    with socket.socket(family, socket.SOCK_DGRAM) as s:
        try:
            s.connect((host, 58162))
        except OSError:
            return "::1" if family == socket.AF_INET6 else "127.0.0.1"

        return s.getsockname()[0]  # type: ignore


def print_listen_address(host, port):
    if not host:
        host = '0.0.0.0'

    all_address = False
    if host == "0.0.0.0":
        all_address = True
        host = get_interface_ip(socket.AF_INET)
    elif host == "::":
        all_address = True
        host = get_interface_ip(socket.AF_INET6)

    if ':' in host:  # ipv6
        host = '[%s]' % host

    if all_address:
        print('Running on all addresses.')
        print('Use http://%s:%s/ to access the application' % (host, port))
    else:
        print('Running on http://%s:%s/' % (host, port))
