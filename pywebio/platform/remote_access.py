"""
* Implementation of remote access
Use localhost.run ssh remote port forwarding service by running a ssh subprocess in PyWebIO application.

The stdout of ssh process is the connection info. 

* Strategy
Wait at most one minute to get stdout, if it gets a normal out, the connection is successfully established. 
Otherwise report error.

* One Issue
When the PyWebIO application process exits, the ssh process becomes an orphan process and does not exit.

* Solution.
Use a child process to create the ssh process, the child process monitors the PyWebIO application process
to see if it alive, and when the PyWebIO application exit, the child process kills the ssh process and exit.
"""

import json
import logging
import multiprocessing
import os
import re
import shlex
import threading
import time
from subprocess import Popen, PIPE

logger = logging.getLogger(__name__)

success_msg = """
================================================================================
PyWebIO Application Remote Access

Remote access address: {address} 
================================================================================
"""

_ssh_process = None  # type: Popen


def remote_access_service(local_port=8080, server='app.pywebio.online', server_port=1022, setup_timeout=60,
                          need_exit=None):
    """
    :param local_port: ssh local listen port
    :param server: ssh server domain
    :param server_port: ssh server port
    :param setup_timeout: If the service can't setup successfully in `setup_timeout` seconds, then exit.
    :param callable need_exit: The service will call this function periodicity, when it return True, then exit the service.
    """

    global _ssh_process

    cmd = "ssh -oStrictHostKeyChecking=no -R 80:localhost:%s -p %s %s -- --output json" % (
        local_port, server_port, server)
    args = shlex.split(cmd)
    logger.debug('remote access service command: %s', cmd)

    _ssh_process = Popen(args, stdout=PIPE, stderr=PIPE)
    logger.debug('remote access process pid: %s', _ssh_process.pid)
    success = False

    def timeout_killer(wait_sec):
        time.sleep(wait_sec)
        if not success and _ssh_process.poll() is None:
            _ssh_process.kill()

    threading.Thread(target=timeout_killer, kwargs=dict(wait_sec=setup_timeout), daemon=True).start()

    stdout = _ssh_process.stdout.readline().decode('utf8')
    logger.debug('ssh server stdout: %s', stdout)
    connection_info = {}
    try:
        connection_info = json.loads(stdout)
        success = True
    except json.decoder.JSONDecodeError:
        if not success and _ssh_process.poll() is None:
            _ssh_process.kill()

    if success:
        if connection_info.get('status', 'fail') != 'success':
            print("Failed to establish remote access, this is the error message from service provider:",
                  connection_info.get('message', ''))
        else:
            print(success_msg.format(address=connection_info['address']))

    # wait ssh or parent process exit
    while not need_exit() and _ssh_process.poll() is None:
        time.sleep(1)

    if _ssh_process.poll() is None:  # parent process exit, kill ssh process
        logger.debug('App process exit, killing ssh process')
        _ssh_process.kill()
    else:  # ssh process exit by itself or by timeout killer
        stderr = _ssh_process.stderr.read().decode('utf8')
        logger.debug("Stderr from ssh process: %s", stderr)
        if stderr:
            print(stderr)
        else:
            print('PyWebIO application remote access service exit.')


def start_remote_access_service_(**kwargs):
    ppid = os.getppid()

    def need_exit():
        # only for unix
        return os.getppid() != ppid

    try:
        remote_access_service(**kwargs, need_exit=need_exit)
    except KeyboardInterrupt:  # ignore KeyboardInterrupt
        pass
    finally:
        if _ssh_process:
            logger.debug('Exception occurred, killing ssh process')
            _ssh_process.kill()
        raise SystemExit


def start_remote_access_service(**kwargs):
    server = os.environ.get('PYWEBIO_REMOTE_ACCESS', 'app.pywebio.online:1022')
    if ':' not in server:
        server_port = 22
    else:
        server, server_port = server.split(':', 1)
    kwargs.setdefault('server', server)
    kwargs.setdefault('server_port', server_port)
    multiprocessing.Process(target=start_remote_access_service_, kwargs=kwargs).start()


if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="localhost.run Remote Access service")
    parser.add_argument("--local-port", help="the local port to connect the tunnel to", type=int, default=8080)
    parser.add_argument("--server", help="the local port to connect the tunnel to", type=str,
                        default='app.pywebio.online')
    parser.add_argument("--server-port", help="the local port to connect the tunnel to", type=int, default=1022)
    args = parser.parse_args()

    start_remote_access_service(local_port=args.local_port, server=args.server, server_port=args.server_port)
    os.wait()  # Wait for completion of a child process
