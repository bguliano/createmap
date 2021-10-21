import subprocess
from subprocess import PIPE, DEVNULL
import pickle
import platform
import os

linux = True if 'linux' in platform.system().lower() else False
s = '/' if linux else '\\'

allFiles = []
allFolders = []
allExt = {}

timer = 0


def command(cmd):
    return subprocess.run(cmd, shell=True, universal_newlines=True, stdout=PIPE)


def pcmd(cmd):
    print(command(cmd).stdout.strip())


def findExt(*exts, outputList=False):
    result = []
    for ext in exts:
        if ext.lower() in allExt.keys():
            if outputList:
                result.extend(allExt[ext.lower()])
            else:
                print('\n'.join(allExt[ext.lower()]))
        elif ext.upper() in allExt.keys():
            if outputList:
                result.extend(allExt[ext.upper()])
            else:
                print('\n'.join(allExt[ext.upper()]))
        else:
            if not outputList:
                print(f'The extension "{ext}" was not found')
    return result


def lenExt(*exts):
    return len(findExt(*exts, outputList=True))


def copyAll(destination, *exts, verbose=False):
    if not os.path.isdir(destination):
        os.makedirs(destination)
    i = ''
    while i not in ('y', 'n'):
        i = input(f'Copying will result in {lenExt(*exts)} files being copied. Continue? (Y/N) ').lower()
    if i == 'y':
        for item in findExt(*exts, outputList=True):
            if verbose:
                pcmd(fr'{"cp" if linux else "copy"} "{item}" "{destination}"')
            else:
                command(fr'{"cp" if linux else "copy"} "{item}" "{destination}"')


def rename(file, name):
    def checkSep():
        return '/' if linux else '\\'

    split = file.split('/' if linux else '\\')
    ext = file.split('.')[-1]
    src = checkSep().join(split[:-1])
    new = f'{src}{checkSep()}{name}.{ext}'
    os.rename(file, new)


def printAllExt(file=allExt):
    if not isinstance(file, dict):
        raise TypeError('Invalid parameter: "file" expects a dict object')
    masterList = []
    for key, value in file.items():
        if key != 'UNKNOWN':
            masterList.append(f'\n-----.{key}-----')
            masterList += value
    if 'UNKNOWN' in file.keys():
        masterList.append('\n-----UNKNOWN-----')
        masterList += file['UNKNOWN']
    print('\n'.join(masterList))


def exportMap(path):
    with open(path, 'wb') as f:
        pickle.dump([allFiles, allFolders, allExt], f)


def importMap(path, warning=True):
    if warning:
        inpt = ''
        while inpt not in ('y', 'n'):
            # print(f'{inpt} is invalid.')
            inpt = input(f'Are you sure you want to import {path}? (Y/N) ').lower()
    else:
        inpt = 'y'
    if inpt == 'y':
        with open(path, 'rb') as f:
            allFiles, allFolders, allExt = pickle.load(f)


class directory:
    def __init__(self, path, autoScan=True):
        if path[-1] == '/':
            self.path = path[:-1]
        else:
            self.path = path
        global allFolders
        allFolders.append(self.path)
        self.folders = []
        self.files = []
        self.ext = {}
        if autoScan:
            self.scan()

    def __repr__(self):
        return self.path

    def addFolder(self, item):
        self.folders.append(directory(f'{self.path}{s}{item}'))

    def addFile(self, item):
        self.files.append(f'{self.path}{s}{item}')

    def folderConvert(self):
        folder_paths = []
        for item in self.folders:
            folder_paths.append(item.path)
        return folder_paths

    def printFull(self):
        print('-----Folders-----', '\n'.join(self.folderConvert()), '-----Files-----', '\n'.join(self.files), sep='\n')

    def printFolders(self):
        print('\n'.join(self.folderConvert()))

    def printFiles(self):
        print('\n'.join(self.files))

    # def printExt(self):
    #     printExt(self.ext)

    def checkIfFolder(self, path):
        return not subprocess.run(f'cd "{path}"', shell=True, stderr=DEVNULL).returncode

    def scan(self):  # Scan for all items and folders in path (but not subfolders)
        if linux:
            scan_cmd = command(f'cd "{self.path}" && ls')
        else:
            if self.path[0] != os.getcwd()[0]:
                scan_cmd = command(f'cd /D "{self.path}" && dir /B')
            else:
                scan_cmd = command(f'cd "{self.path}" && dir /B')
        if 'Permission Denied' in scan_cmd.stdout:
            print(self.path)
        else:
            full = scan_cmd.stdout.split('\n')[:-1]
            for item in full:
                if not '.' in item:
                    if self.checkIfFolder(f'{self.path}{s}{item}'):
                        self.addFolder(item)
                    else:
                        self.addFile(item)
                else:
                    self.addFile(item)
            for item in self.files:  # Organize files by their extensions in self.ext
                item_ext = item.split('.')[-1] if '.' in item else 'UNKNOWN'
                if item_ext[0] != ' ':
                    if item_ext in self.ext.keys():
                        self.ext[item_ext].append(item)
                    else:
                        self.ext[item_ext] = [item]
            global allFiles, allExt
            allFiles += self.files
            for key, value in self.ext.items():
                if key in allExt.keys():
                    allExt[key] += value
                else:
                    allExt[key] = value
