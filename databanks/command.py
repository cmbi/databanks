import os
import signal
import psutil
from threading import Thread
from time import time, sleep

from subprocess import Popen, PIPE, TimeoutExpired
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
        try:
            if strin is not None:
                input_= strin.encode('ascii')
            else:
                input_ = None

            p = Popen(cmdstr, shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE)

            stderr, stdout = p.communicate(input=strin, timeout=timeout)
        except OSError:
            continue
        except TimeoutExpired:
            return False

    for line in stdout.decode('utf-8').split('\n'):
        log.debug("[%s] %s" % (tag, line))

    for line in stderr.decode('utf-8').split('\n'):
        log.error("[%s] %s" % (tag, line))

    return True
