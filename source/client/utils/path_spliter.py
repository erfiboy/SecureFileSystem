import os


def directory_splitter(path, full=False):
    folders = []
    while 1:
        path, folder = os.path.split(path)

        if folder != "":
            folders.append(folder)
        elif path != "":
            folders.append(path)

            break

    if full:
        folders.reverse()
        return folders

    relative_path = folders[: folders.index("filesystem")]

    relative_path.reverse()
    return relative_path
