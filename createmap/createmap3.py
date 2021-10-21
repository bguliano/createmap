import os
import threading
from queue import Queue
from time import sleep


# import concurrent.futures

class PathManager:
    def __init__(self):
        self.path = None
        self.child = None
        self._files = []
        self._folders = []
        self._exts = {}
        self._queue = Queue(maxsize=0)
        self.directories = []
        self._directories_lock = threading.Lock()
        self._files_lock = threading.Lock()
        self._folders_lock = threading.Lock()
        self._exts_lock = threading.Lock()
        self.print = False

    def createmap(self, path):
        self.reset()
        self.path = path
        self.child = Directory(self.path, self)
        self.add_queue(self.child)
        self.worker = threading.Thread(target=self.work)
        self.worker.daemon = True
        self.worker.start()
        self.wait()

    def work(self):
        while True:
            task = self._queue.get()
            thread = threading.Thread(target=task.scan)
            thread.start()
            self._queue.task_done()

    @property
    def files(self):
        if self.print:
            print('\n'.join(self._files))
        else:
            return self._files

    @property
    def folders(self):
        if self.print:
            print('\n'.join(self._folders))
        else:
            return self._folders

    @property
    def exts(self):
        if self.print:
            masterList = []
            for key, value in self._exts.items():
                if key != 'UNKNOWN':
                    masterList.append(f'\n-----.{key}-----')
                    masterList += value
            if 'UNKNOWN' in self._exts.keys():
                masterList.append('\n-----UNKNOWN-----')
                masterList += self._exts['UNKNOWN']
            print('\n'.join(masterList))
        else:
            return self._exts

    def add_files(self, files):
        with self._files_lock:
            local = self._files  # Read
            local += files  # Write
            self._files = local  # Update

    def add_folders(self, folders):
        with self._folders_lock:
            local = self._folders
            local += folders
            self._folders = local

    def add_exts(self, exts):
        with self._exts_lock:
            local = self._exts
            for key, value in exts.items():
                if key in local.keys():
                    local[key].extend(value)
                else:
                    local[key] = value
            self._exts = local

    def add_self(self, obj):
        with self._directories_lock:
            self.directories.append(obj)

    def add_queue(self, obj):
        self._queue.put(obj)

    def wait(self):
        '''Wait until the manager is done processing'''
        sleep(.01)
        self._queue.join()

    def reset(self):
        self._files.clear()
        self._folders.clear()
        self._exts.clear()
        self.directories.clear()
        self.path = None
        self.child = None

    def find(self, path):
        for item in self.directories:
            if item.path == path:
                return item


class Directory:
    def __init__(self, path, manager):
        if path[-1] == '/':  # Remove any leading slash
            self.path = path[:-1]
        else:
            self.path = path
        self.folders = []
        self.files = []
        self.exts = {}
        self.manager = manager

    def addFolder(self, item):
        self.folders.append(item)
        self.manager.add_queue(Directory(item, self.manager))

    def addFile(self, item):
        self.files.append(item)

    def printFull(self):
        print('-----Folders-----', '\n'.join(self.folders), '-----Files-----', '\n'.join(self.files), sep='\n')

    def printFolders(self):
        print('\n'.join(self.folders))

    def printFiles(self):
        print('\n'.join(self.files))

    def scan(self):
        full = [self.path + '\\' + item for item in os.listdir(self.path)]
        for item in full:
            if os.path.isfile(item):
                self.addFile(item)
            elif os.path.isdir(item):
                self.addFolder(item)
            else:
                print(f'File skipped: "{item}" is neither file nor directory')
        for item in self.files:  # Add files to extension dict
            item_ext = os.path.splitext(item)[1]
            if item_ext == '':
                if 'UNKNOWN' in self.exts.keys():
                    self.exts['UNKNOWN'].append(item)
                else:
                    self.exts['UNKNOWN'] = [item]
            else:
                if item_ext in self.exts.keys():
                    self.exts[item_ext].append(item)
                else:
                    self.exts[item_ext] = [item]
        self.manager.add_files(self.files)
        self.manager.add_folders(self.folders)
        self.manager.add_exts(self.exts)
        self.manager.add_self(self)
