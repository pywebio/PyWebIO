"""
* Implementation of remote access
Use https://github.com/wang0618/localshare service by running a ssh subprocess in PyWebIO application.

The stdout of ssh process is the connection info.
"""

import json
import logging
import os
import threading
import time
import shlex
from subprocess import Popen, PIPE
import shutil

logger = logging.getLogger(__name__)

success_msg = """
================================================================================
PyWebIO Application Remote Access

Remote access address: {address} 
================================================================================
"""

_ssh_process = None  # type: Popen


def am_i_the_only_thread():
    """Whether the current thread is the only non-Daemon threads in the process"""
    alive_none_daemonic_thread_cnt = sum(
        1 for t in threading.enumerate()
        if t.is_alive() and not t.isDaemon()
    )
    return alive_none_daemonic_thread_cnt == 1


def remote_access_service(local_port=8080, server='app.pywebio.online', server_port=1022, setup_timeout=60):
    """
    Wait at most one minute to get the ssh output, if it gets a normal out, the connection is successfully established.
    Otherwise report error and kill ssh process.

    :param local_port: ssh local listen port
    :param server: ssh server domain
    :param server_port: ssh server port
    :param setup_timeout: If the service can't setup successfully in `setup_timeout` seconds, then exit.
    """

    global _ssh_process

    cmd = "ssh -oStrictHostKeyChecking=no -R 80:127.0.0.1:%s -p %s %s -- --output json" % (
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

    # wait ssh or main thread exit
    while not am_i_the_only_thread() and _ssh_process.poll() is None:
        time.sleep(1)

    if _ssh_process.poll() is None:  # main thread exit, kill ssh process
        logger.debug('App process exit, killing ssh process')
        _ssh_process.kill()
    else:  # ssh process exit by itself or by timeout killer
        stderr = _ssh_process.stderr.read().decode('utf8')
        if stderr:
            logger.error('PyWebIO application remote access service error: %s', stderr)
        else:
            logger.info('PyWebIO application remote access service exit.')


def start_remote_access_service_(**kwargs):
    try:
        remote_access_service(**kwargs)
    except KeyboardInterrupt:  # ignore KeyboardInterrupt
        pass
    finally:
        if _ssh_process:
            logger.debug('Exception occurred, killing ssh process')
            _ssh_process.kill()
        raise SystemExit


def start_remote_access_service(**kwargs):
    if not shutil.which("ssh"):
        logging.error("No ssh client found, remote access service can't start.")
        return

    server = os.environ.get('PYWEBIO_REMOTE_ACCESS', 'app.pywebio.online:1022')
    if ':' not in server:
        server_port = 22
    else:
        server, server_port = server.split(':', 1)
    kwargs.setdefault('server', server)
    kwargs.setdefault('server_port', server_port)
    thread = threading.Thread(target=start_remote_access_service_, kwargs=kwargs)
    thread.start()
    return thread


if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Remote Access service")
    parser.add_argument("--local-port", help="the local port to connect the tunnel to", type=int, default=8080)
    parser.add_argument("--server", help="the local port to connect the tunnel to", type=str,
                        default='app.pywebio.online')
    parser.add_argument("--server-port", help="the local port to connect the tunnel to", type=int, default=1022)
    args = parser.parse_args()

    t = start_remote_access_service(local_port=args.local_port, server=args.server, server_port=args.server_port)
    t.join()
