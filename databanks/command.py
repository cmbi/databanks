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

class _LogThread(Thread):
    def __init__(self, p, log, tag):
        Thread.__init__(self)
        self._p = p
        self._log = log
        self._tag = tag


class _LogStdoutThread(_LogThread):
    def run(self):
        while self._p.poll() is None:
            line = self._p.stdout.readline()
            if len(line) <= 0:
                break
            self._log.debug("[%s] %s" % (self._tag, line.strip()))
        self._p.stdout.close()


class _LogStderrThread(_LogThread):
    def run(self):
        while self._p.poll() is None:
            line = self._p.stderr.readline()
            if len(line) <= 0:
                break
            self._log.error("[%s] %s" % (self._tag, line.strip()))
        self._p.stderr.close()


def log_command(log, tag, cmdstr,
                cwd=None, timeout=None, strin=None):
    """Returns False if the command times out, True otherwise."""

    if strin is not None:
        p = Popen(cmdstr, shell=True,
                  stdout=PIPE, stderr=PIPE, stdin=PIPE,
                  close_fds=True,
                  cwd=cwd)
        p.stdin.write(strin)
        p.stdin.close()
    else:
        p = Popen(cmdstr, shell=True,
                  stdout=PIPE, stderr=PIPE,
                  close_fds=True,
                  cwd=cwd)
    log.info("[%s] %s" % (tag, cmdstr))

    _LogStdoutThread(p, log, tag).start()
    _LogStderrThread(p, log, tag).start()

    t0 = time()
    if timeout is not None:
        while (time() - t0) < timeout:
            sleep(1)
            if p.poll() is not None:
                return True

        kill_process_tree(p.pid)
        return False
    else:
        p.wait()
        return True
