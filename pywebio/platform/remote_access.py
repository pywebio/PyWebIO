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

Remote access address: https://{address} 

The remote access service is provided by localhost.run (https://localhost.run/).
The remote access address will be reset in every 6 hours and only one 
application can enable remote access at the same time, if you use the free tier.

To set up and manage custom domains go to https://admin.localhost.run/

================================================================================
"""

ssh_key_gen_msg = """
===============================================================================
PyWebIO Application Remote Access Error

You need an SSH key to access the remote access service.
Please follow Gitlab's most excellent howto to generate an SSH key pair: 
https://docs.gitlab.com/ee/ssh/
Note that only rsa and ed25519 keys are supported.
===============================================================================
"""

_ssh_process = None  # type: Popen


def remote_access_process(local_port=8080, setup_timeout=60, key_path=None, custom_domain=None):
    global _ssh_process
    ppid = os.getppid()
    assert ppid != 1
    domain_part = '%s:' % custom_domain if custom_domain is not None else ''
    key_path_arg = '-i %s' % key_path if key_path is not None else ''
    cmd = "ssh %s -oStrictHostKeyChecking=no -R %s80:localhost:%s localhost.run -- --output json" % (
        key_path_arg, domain_part, local_port)
    args = shlex.split(cmd)
    logger.debug('remote access service command: %s', cmd)

    _ssh_process = proc = Popen(args, stdout=PIPE, stderr=PIPE)
    logger.debug('remote access process pid: %s', proc.pid)
    success = False

    def timeout_killer(wait_sec):
        time.sleep(wait_sec)
        if not success and proc.poll() is None:
            proc.kill()

    threading.Thread(target=timeout_killer, kwargs=dict(wait_sec=setup_timeout), daemon=True).start()

    stdout = proc.stdout.readline().decode('utf8')
    connection_info = {}
    try:
        connection_info = json.loads(stdout)
        success = True
    except json.decoder.JSONDecodeError:
        if not success and proc.poll() is None:
            proc.kill()

    if success:
        if connection_info.get('status', 'fail') != 'success':
            print("Failed to establish remote access, this is the error message from service provider:",
                  connection_info.get('message', ''))
        else:
            print(success_msg.format(address=connection_info['address']))

    # wait ssh or parent process exit
    while os.getppid() == ppid and proc.poll() is None:
        time.sleep(1)

    if proc.poll() is None:  # parent process exit, kill ssh process
        logger.debug('App process exit, killing ssh process')
        proc.kill()
    else:  # ssh process exit by itself or by timeout killer
        stderr = proc.stderr.read().decode('utf8')
        conn_id = re.search(r'connection id is (.*?),', stderr)
        logger.debug('Remote access connection id: %s', conn_id.group(1) if conn_id else '')
        ssh_error_msg = stderr.rsplit('**', 1)[-1].rsplit('===', 1)[-1].lower().strip()
        if 'permission denied' in ssh_error_msg:
            print(ssh_key_gen_msg)
        elif ssh_error_msg:
            print(ssh_error_msg)
        else:
            print('PyWebIO application remote access service exit.')


def start_remote_access_service(local_port=8080, setup_timeout=60, ssh_key_path=None, custom_domain=None):
    pid = os.fork()
    if pid == 0:  # in child process
        try:
            remote_access_process(local_port=local_port, setup_timeout=setup_timeout,
                                  key_path=ssh_key_path, custom_domain=custom_domain)
        except KeyboardInterrupt:  # ignore KeyboardInterrupt
            pass
        finally:
            if _ssh_process:
                logger.debug('Exception occurred, killing ssh process')
                _ssh_process.kill()
            raise SystemExit

    else:
        return pid


if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="localhost.run Remote Access service")
    parser.add_argument("--local-port", help="the local port to connect the tunnel to", type=int, default=8080)
    parser.add_argument("--custom-domain", help="optionally connect a tunnel to a custom domain", default=None)
    parser.add_argument("--key-path", help="custom SSH key path", default=None)
    args = parser.parse_args()

    start_remote_access_service(local_port=args.local_port, ssh_key_path=args.key_path, custom_domain=args.custom_domain)
    os.wait()  # Wait for completion of a child process
