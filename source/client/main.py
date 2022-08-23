import getpass
import hashlib
import os
import pathlib
import re
import sys
from pathlib import Path

from termcolor import colored

path = Path(os.path.dirname(__file__))
path = path.parent.absolute()
sys.path.append(f"{path}/server")
sys.path.append(f"{path}")
sys.path.append(f"{path}/server/main")
sys.path.append(f"{path}/client")
sys.path.append(f"{path}/client/utils")

from server.main import KeyEchange, ServerRun
from server.utiles.aes import encryption
from server.utiles.filesystem_commands import cd, ls, mkdir, mv, rm, touch
from utils.client import Client
from utils.text_editor import text_editor


def client_DH_key_exchange(server):
    client_DH = KeyEchange()
    client_pub_key = client_DH.get_pub_key()

    server_public_key, nonce, tag, cipher_text = server.server_DH_key_exchange(client_pub_key=client_pub_key)
    client_DH.calculate_share_key(server_public_key)
    session_key = client_DH.decrypt(cipher_text, tag, nonce)
    return session_key


def client_sign_up(server, session_key):
    first_name = input("Enter your user first name: ")
    last_name = input("Enter your user last name: ")
    username = input("Enter your user username: ")
    password = getpass.getpass("Enter your user password: ")
    client = Client(username, password)

    message = f"{first_name} {last_name} {username} {password}"
    cipher_text = encryption(message, session_key)
    is_signup = server.sign_up(cipher_text)
    server.access_control.add_role(username, ["R", "W", "D"])
    server.access_control.add_user(username, [username])
    client.role.append(username)
    return is_signup, client


def client_login(server, session_key):
    username = input("Enter your user username: ")
    password = getpass.getpass("Enter your user password: ")
    client = Client(username, password)

    message = f"{username} {hashlib.sha256(password.encode()).hexdigest()}"
    cipher_text = encryption(message, session_key)
    is_login = server.login(cipher_text)
    return is_login, client


def output_formatter(message, client):
    if not client:
        print(colored(f"SecureFileSystem > {message}", "green"))
    else:
        print(
            colored(f"{client.username}@{client.role[0]}:", "green"),
            colored(f"{client.pwd}$ {message}", "blue"),
        )


base_path = os.path.join(os.getcwd(), "filesystem")


def filesystem_command(command: str, client, server):
    try:
        command_args = command.split(" ")
        path = None
        if len(command_args) == 1 and command_args[0] == "ls":
            path = os.getcwd()
        elif command_args[0] in ["rm", "mv"]:
            if command_args[1] == "-r" and len(command_args) == 3 and command_args[0] == "rm":
                path = os.path.abspath(command_args[2])
            elif len(command_args) == 2:
                path = os.path.abspath(command_args[1])
            elif command_args[1] == "-r" and len(command_args) == 4:
                path = [os.path.abspath(command_args[2]), os.path.abspath(command_args[3])]
            elif len(command_args) == 3:
                path = [os.path.abspath(command_args[1]), os.path.abspath(command_args[2])]
            else:
                path = re.findall('"([^"]*)"', command)
                path = [os.path.abspath(i) for i in path]

        elif command_args[0] in ["mkdir", "touch", "cd", "setup", "ls", "edit"] and len(command_args) == 2:
            if command_args[1] == "..":
                path = pathlib.Path(os.getcwd()).parent
            else:
                path = os.path.abspath(command_args[1])
        else:
            path = re.findall('"([^"]*)"', command)
            path = [os.path.abspath(i) for i in path]

        if command_args[0] == "setup":
            mkdir(os.path.abspath(path), server, client)
            server.access_control.allow(client.username, "R", [base_path])
            cd(os.path.abspath(path), client, server)

        elif command_args[0] == "mkdir":
            if not path:
                print("mkdir command only gets a path: ex, mkdir directory")
                return
            else:
                return mkdir(path, server, client)

        elif command_args[0] == "touch":
            if not path:
                print("touch command only gets a path: ex, touch file")
                return
            else:
                return touch(path, server, client)

        elif command_args[0] == "cd":
            if not path:
                print("cd command only gets a path: ex, cd directory")
                return
            else:
                return cd(path, client, server)

        elif command_args[0] == "ls":
            if not path:
                print("ls command gets a path or None: ex, cd directory")
                return
            else:
                return ls(path, client, server)

        elif command_args[0] == "edit":
            if not path:
                print("edit command gets a path: ex, edit file")
                return
            else:
                return text_editor(path, client, server)

        elif command_args[0] == "rm":
            if command_args[1] == "-r":
                if not path:
                    print("rm command gets a path and a flag: ex, rm -r directory")
                    return
                else:
                    rm(path, server, client, True)
            else:
                if not path:
                    print("rm command gets a path and a flag: ex, rm -r directory")
                    return
                else:
                    rm(path, server, client, False)

        elif command_args[0] == "mv":
            if command_args[1] == "-r":
                if len(path) == 2:
                    return mv(path[0], path[1], server, client, True)
                else:
                    print(
                        "mv command gets a src path and a dest path and a flag: ex, mv -r src_directory dest_directory"
                    )
                    return
            else:
                if len(path) == 2:
                    return mv(path[0], path[1], server, client, False)
                else:
                    print("mv command gets a src path and a dest path and a flag: ex, mv src_file dest_file")
                    return

    except Exception as e:
        print(e)
        return


def run():
    server = ServerRun()
    session_key = client_DH_key_exchange(server)
    input_message = None
    phase = "login"
    client = None

    while True:
        if phase == "login":
            input_message = "SecureFileSystem > [1] SignUp [2] Login: "
        elif phase == "authenticated":
            input_message = f"{client.username}@{client.role[0]}: {client.pwd}$ "

        command = input(input_message)
        if command == "exit":
            if client:
                client.dump()
                client.dump_dict()
            phase = "login"
            client = None

        if phase == "login":
            try:
                command = int(command)
            except:
                continue
            if command == 1:
                is_signup, client = client_sign_up(server, session_key)
                if not is_signup:
                    output_formatter("The username already existed!", client)
                    client = None
                    continue
                else:
                    client.create_master_key()
                    phase = "authenticated"
                    filesystem_command(f"setup {client.pwd}", client, server)

            elif command == 2:
                is_login, client = client_login(server, session_key)
                if not is_login:
                    output_formatter("The username or password is wrong!", client)
                    client = None
                    continue
                else:
                    client.load()
                    client.load_dict()
                    phase = "authenticated"
                    filesystem_command(f"setup {client.pwd}", client, server)

            continue

        if phase == "authenticated":
            filesystem_command(command, client, server)


while True:
    run()
