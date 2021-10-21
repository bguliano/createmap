import pathlib
import time
from queue import Queue, Empty
from threading import Thread, Lock


class PathManager:
    def __init__(self, path: str):
        self.path = pathlib.Path(path)

        self.folders = []
        self.files = []
        self.extensions = {}

        # to threads
        self.dir_queue = Queue()

        # to manager
        self.extensions_queue = Queue()

        self.folders_lock = Lock()
        self.files_lock = Lock()

    def createmap(self, threads: int = 8, output: bool = True):
        start_time = time.time()

        self.dir_queue.put(self.path)

        workers = []
        for _ in range(threads):
            w = Worker(self.dir_queue, self.extensions_queue, self)
            w.daemon = True
            w.start()
            workers.append(w)

        while not self.dir_queue.empty() or not self.extensions_queue.empty():
            try:
                file: pathlib.Path = self.extensions_queue.get_nowait()
                suffix = file.suffix
                if suffix in self.extensions:
                    self.extensions[suffix].append(file)
                else:
                    self.extensions[suffix] = [file]
            except Empty:
                pass

        if output:
            print(f'Took {time.time() - start_time} seconds')
            print(f'Found {len(self.folders)} folders, {len(self.files)} files, '
                  f'and {len(self.extensions.keys())} extensions')

        for w in workers:
            w.stop()

    def get_files(self, *exts):
        # use glob example from https://realpython.com/python-pathlib/#examples
        pass

    def add_file(self, file: pathlib.Path):
        with self.files_lock:
            self.files.append(file)

    def add_folder(self, folder: pathlib.Path):
        with self.folders_lock:
            self.folders.append(folder)


class Worker(Thread):
    def __init__(self, dir_queue: Queue,
                 extensions_queue: Queue,
                 manager: PathManager):
        Thread.__init__(self)
        self.dir_queue = dir_queue
        self.extensions_queue = extensions_queue
        self.manager = manager
        self.running = True

    def stop(self):
        self.running = False

    def run(self) -> None:
        while self.running:
            try:
                directory: pathlib.Path = self.dir_queue.get_nowait()
                for path in directory.iterdir():
                    if path.is_dir():
                        self.dir_queue.put(path)
                        self.manager.add_folder(path)
                    else:
                        self.extensions_queue.put(path)
                        self.manager.add_file(path)
            except Empty:
                pass
