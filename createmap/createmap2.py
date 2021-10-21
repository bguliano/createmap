import os


class Manager:
    def __init__(self):
        self._files = []
        self._folders = []
        self._ext = {}
        self.print = True

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
    def ext(self):
        if self.print:
            masterList = []
            for key, value in self._ext.items():
                if key != 'UNKNOWN':
                    masterList.append(f'\n-----.{key}-----')
                    masterList += value
            if 'UNKNOWN' in self._ext.keys():
                masterList.append('\n-----UNKNOWN-----')
                masterList += self._ext['UNKNOWN']
            print('\n'.join(masterList))
        else:
            return self._ext

    def add_files(self, files):
        self._files.extend(files)

    def add_folders(self, folders):
        self._folders.extend(folders)

    def add_exts(self, exts):
        for key, value in exts.items():
            if key in self._ext.keys():
                self._ext[key] += value
            else:
                self._ext[key] = value


class Directory:
    def __init__(self, path, manager, autoScan=True):
        if path[-1] == '/':  # Remove any leading slash
            self.path = path[:-1]
        else:
            self.path = path
        self.folders = []
        self.files = []
        self.ext = {}
        self.manager = manager
        if autoScan:
            self.scan()

    def __str__(self):
        return self.path

    def addFolder(self, item):
        self.folders.append(Directory(item, self.manager))

    def addFile(self, item):
        self.files.append(item)

    def printFull(self):
        print('-----Folders-----', '\n'.join(self.folderConvert()), '-----Files-----', '\n'.join(self.files), sep='\n')

    def printFolders(self):
        print('\n'.join([str(item) for item in self.folders]))

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
        for item in self.files:  # Organize files by their extensions in self.ext
            item_ext = item.split('.')[-1] if '.' in item else 'UNKNOWN'
            if item_ext in self.ext.keys():
                self.ext[item_ext].append(item)
            else:
                self.ext[item_ext] = [item]
        self.manager.add_files(self.files)
        self.manager.add_folders([str(item) for item in self.folders])
        self.manager.add_exts(self.ext)
