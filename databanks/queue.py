import traceback
from threading import Lock, Thread
from time import sleep
from threading import current_thread

import logging
_log = logging.getLogger(__name__)


class Job(object):
    def __init__(self, name, dependent_jobs=[]):
        self._done = False
        self._lock = Lock()
        self._name = name  # printed to logs
        self._dependent_jobs = dependent_jobs

    def run(self):
        pass

    def set_done(self):
        with self._lock:
            self._done = True

    def is_done(self):
        with self._lock:
            return self._done

    def get_name(self):
        with self._lock:
            return self._name

    def is_ready(self):
        with self._lock:
            for dep in self._dependent_jobs:
                if not dep.is_done():
                    return False

            return True


class _QueueThread(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self._queue = queue
        self._lock = Lock()
        self._current_job_name = "none"

    def run(self):
        while True:
            job = self._queue.pop()
            if job is None:
                return

            with self._lock:
                self._current_job_name = job.get_name()

            _log.debug("running job with name {}".format(self._current_job_name))
            try:
                job.run()

                _log.debug("finished job with name {}".format(self._current_job_name))
            except Exception as e:
                _log.error(traceback.format_exc())
            finally:
                job.set_done()

    def get_job_name(self):
        with self._lock:
            return self._current_job_name


class Queue(object):
    def __init__(self, max_threads):
        self._max_threads = max_threads
        self._queue_lock = Lock()
        self._jobs_by_priority = {}

    def put(self, job, priority=0):
        """
        The higher priority value jobs will go first.
        """

        with self._queue_lock:
            if priority not in self._jobs_by_priority:
                self._jobs_by_priority[priority] = []
            self._jobs_by_priority[priority].append(job)

    def pop(self):
        with self._queue_lock:
            for priority in reversed(sorted(self._jobs_by_priority.keys())):
                for i in range(len(self._jobs_by_priority[priority])):
                    if self._jobs_by_priority[priority][i].is_ready():
                        job = self._jobs_by_priority[priority][i]
                        self._jobs_by_priority[priority] = \
                                self._jobs_by_priority[priority][:i] + \
                                self._jobs_by_priority[priority][i + 1:]
                        return job

            return None

    def count_waiting(self):
        with self._queue_lock:
            n_waiting = 0
            for priority in self._jobs_by_priority:
                for job in self._jobs_by_priority[priority]:
                    if job.is_ready() and not job.is_done():
                        n_waiting += 1
            return n_waiting

    def run(self):
        threads = []
        while True:
            if self.count_waiting() > 0:
                while len(threads) < self._max_threads:
                    t = _QueueThread(self)
                    t.start()
                    threads.append(t)

            alive_threads = [t for t in threads if t.is_alive()]
            n_waiting = self.count_waiting()
            if len(alive_threads) <= 0 and n_waiting <= 0:
                _log.debug("terminating jobless queue")
                break
            threads = alive_threads

            _log.debug("queue in thread %d: %d waiting jobs, %d threads alive" %
                       (current_thread().ident,
                        n_waiting, len(alive_threads)))
            _log.info(" ".join([t.get_job_name() for t in alive_threads]))
            sleep(5)
