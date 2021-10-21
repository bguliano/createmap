import os
from queue import Queue
from threading import Thread
from time import time


class PathManager:
    def __init__(self, path):
        self.path = path
        self.queue = Queue()
        self.resultQueue = Queue()

    def createmap(self, threads=16):
        ts = time()
        # Extract all paths in parent path
        self.paths = list(map(lambda x: x[0], os.walk(self.path)))
        self.folders = self.paths
        for i in range(threads):
            worker = PathWorker(self.queue, self.resultQueue)
            worker.daemon = True
            worker.start()
        for path in self.paths:
            self.queue.put(path)
        self.queue.join()
        self.files = []
        for i in range(self.resultQueue.qsize()):
            self.files.extend(self.resultQueue.get())
        print(f'Took {time() - ts} seconds')
        print(f'Found {len(self.folders)-1} folders and {len(self.files)} files')


class PathWorker(Thread):
    def __init__(self, queue, results):
        Thread.__init__(self)
        self.queue = queue
        self.results = results

    def run(self):
        while True:
            directory = self.queue.get()
            onlyfiles = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            self.results.put(onlyfiles)
            self.queue.task_done()
