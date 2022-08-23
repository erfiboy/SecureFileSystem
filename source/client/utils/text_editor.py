import os
import pathlib
import subprocess
from sys import platform


def text_editor(path, client, server):
    temp_path = os.path.join(os.getcwd(), "temp")
    temp = open(temp_path, "w")
    path = server.encrypt_path(path)
    if pathlib.Path(path).is_file():
        temp.write(client.decrypt_file(path, server))

    try:
        editor = os.environ["EDITOR"]
    except KeyError:
        if platform == "linux" or platform == "linux2":
            editor = "nano"
        elif platform == "win32":
            editor == "notepad"
        elif platform == "darwin":
            editor = "nano"

    temp.close()
    subprocess.call([editor, temp_path])
    temp = open(temp_path, "r")
    content = temp.read()
    client.encrypt_file(content, path, server)
    os.remove(temp_path)
