import os
import signal
import psutil
from threading import Thread
from time import time, sleep

from subprocess import Popen, PIPE
import logging

_log = logging.getLogger(__name__)

def kill_process_tree(parent_pid):
    try:
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            try:
                child.send_signal(signal.SIGKILL)
            except psutil.NoSuchProcess:
                continue
        parent.send_signal(signal.SIGKILL)
    except psutil.NoSuchProcess:
        pass

def process_tree_cpu_time(pid):
    try:
        parent = psutil.Process(pid)
        t = parent.cpu_times()
        total = t.user + t.system
        for child in parent.children(recursive=True):
            try:
                t = child.cpu_times()
                total += t.user + t.system
            except psutil.NoSuchProcess:
                continue
        return total
    except psutil.NoSuchProcess:
        return 0.0


def log_command(log, tag, cmdstr,
                cwd=None, timeout=None, strin=None):
    """Returns False if the command times out, True otherwise."""

    log.info("[%s] %s" % (tag, cmdstr))
    p = None
    while p is None:
        t0 = time()
        p = Popen(cmdstr, shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE)

        if strin is not None:
            input_= strin.encode('ascii')
            p.stdin.write(input_)
            p.stdin.close()

        while p.poll() is None:
            if timeout is not None and (time() - t0) >= timeout:
                break

            for line in p.stdout:
                log.debug("[%s] %s" % (tag, line.decode()))

            for line in p.stderr:
                log.error("[%s] %s" % (tag, p.stderr.readline().decode()))

    if p.returncode is None:
        return False

    if p.returncode != 0:
        raise RuntimeError("{} ended with exit code {}".format(cmdstr, p.returncode))

    return True
