import ntpath
import os
import pathlib
import shutil
from pathlib import Path

from termcolor import colored


def path_list(path):
    folders = []

    while 1:
        path, folder = os.path.split(path)

        if folder != "":
            folders.append(folder)
        elif path != "":
            folders.append(path)
            break

    folders.reverse()
    return folders


def mkdir(path, server, client):
    path = server.encrypt_path(path)

    path = path_list(os.path.abspath(path))
    reverse_path = []
    for index in range(len(path)):
        if index == len(path) - 1:
            reverse_path.append(path[index])
            continue
        if path[index] in path[index + 1 :]:
            continue
        reverse_path.append(path[index])
    path = os.path.join(*reverse_path)
    if os.path.exists(path):
        return
    os.makedirs(path)
    server.access_control.allow(client.username, "R", [str(path)])
    server.access_control.allow(client.username, "W", [str(path)])

    return


def touch(path, server, client):
    path = server.encrypt_path(path)
    directories, _ = os.path.split(path)
    mkdir(directories, server, client)
    Path(path).touch()
    server.access_control.allow(client.username, "R", [str(path)])
    server.access_control.allow(client.username, "W", [str(path)])
    return


def cd(path, client, server):
    path = server.encrypt_path(path)
    if not server.access_control.is_allowed(client.username, "R", path):
        return
    path = path_list(os.path.abspath(path))
    reverse_path = []
    for index in range(len(path)):
        if index == len(path) - 1:
            reverse_path.append(path[index])
            continue
        if path[index] in path[index + 1 :]:
            continue
        reverse_path.append(path[index])
    path = os.path.join(*reverse_path)
    os.chdir(path)
    client.pwd = os.path.abspath(server.decrypt_path(os.getcwd()))
    return


def ls(path, client, server):
    files = os.listdir(path)
    index = 0
    files.sort()
    for file in files:
        if index == 3:
            index = 0
            print("")
        x = pathlib.Path(file).absolute()
        if not server.access_control.is_allowed(client.username, "R", x):
            continue
        x = ntpath.basename(server.decrypt_path(x))
        if x is None:
            continue
        if pathlib.Path(os.path.join(path, file)).is_dir():
            print(colored(x, "blue"), end="\t")
        else:
            print(x, end="\t")
        index += 1
    print()
    return


def mv(src_path, dest_path, server, client, recursive=False):
    src_path = server.encrypt_path(src_path)
    dest_path = server.encrypt_path(dest_path)
    if not server.access_control.is_allowed(client.username, "R", src_path):
        return
    if not server.access_control.is_allowed(client.username, "R", dest_path):
        return
    if os.path.isdir(src_path) and not recursive:
        return "Use -r to remove a directory!"

    shutil.move(src_path, dest_path)
    return


def rm(path, server, client, recursive=False):
    path = server.encrypt_path(path)
    if not server.access_control.is_allowed(client.username, "R", str(path)):
        return
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path) and not recursive:
        return "Use -r to remove a directory!"
    else:
        if recursive:
            for entry in os.scandir(path):
                if entry.is_dir(follow_symlinks=False):
                    rm(entry.path, True)
                else:
                    os.unlink(entry.path)

            os.rmdir(path)


def save_file(content, path, server, client):
    mkdir(pathlib.Path(path).parent, server, client)
    with open(path, "w") as file:
        file.write(content)

    server.access_control.allow(client.username, "R", [str(path)])
    server.access_control.allow(client.username, "W", [str(path)])
    return True


def retrieve_file(path, server, client):
    if not server.access_control.is_allowed(client.username, "R", str(path)):
        return
    if os.path.exists(path):
        with open(path, "r") as file:
            content = file.read()
            return content
