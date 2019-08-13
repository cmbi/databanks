import os
import signal
import psutil
from threading import Thread
from time import time, sleep

from subprocess import run, PIPE, TimeoutExpired
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
    try:
        if strin is not None:
            p = run(cmdstr, input=strin.encode('ascii'), shell=True,
                    stdout=PIPE, stderr=PIPE,
                    cwd=cwd, timeout=timeout)
        else:
            p = run(cmdstr, shell=True,
                    stdout=PIPE, stderr=PIPE,
                    cwd=cwd, timeout=timeout)
    except TimeoutExpired:
        return False

    for line in p.stdout.decode('ascii').split('\n'):
        log.debug("[%s] %s" % (tag, line))

    for line in p.stderr.decode('ascii').split('\n'):
        log.error("[%s] %s" % (tag, line))

    return True
