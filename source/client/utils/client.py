import hashlib
import json
import os
import pathlib
import pickle
import sys

from Crypto.Random import get_random_bytes
from cryptography.fernet import Fernet
from path_spliter import directory_splitter
from server.utiles.aes import decryption, encryption
from server.utiles.filesystem_commands import retrieve_file, save_file


class Client:
    def __init__(self, username=None, password=None) -> None:
        self.username = username
        self.password = hashlib.sha256(password.encode()).hexdigest()
        self.role = [username]
        self.master_key = None
        self.map_keys = dict()
        self.pwd = os.path.join(pathlib.Path(os.path.dirname(__file__)).parent.parent.parent, "filesystem")
        self.base_path = os.path.join(
            pathlib.Path(os.path.dirname(__file__)).parent.parent.parent, "users_data"
        )
        self.create_folder()
        os.chdir(pathlib.Path(self.pwd).parent)

    def dump_dict(self):
        with open(os.path.join(self.base_path, f"{self.username}_keys.json"), "w") as outfile:
            json.dump(self.map_keys, outfile)

    def load_dict(self):
        with open(os.path.join(self.base_path, f"{self.username}_keys.json"), "r") as outfile:
            self.map_keys = json.load(outfile)

    def dump(self):
        pickle.dump(
            encryption("", self.password[0:32].encode(), byte=self.master_key),
            open(f"{self.base_path}//{self.username}.txt", "wb"),
        )

    def load(self):
        if os.path.exists(self.base_path + f"//{self.username}.txt"):
            self.master_key = pickle.load(open(f"{self.base_path}//{self.username}.txt", "rb"))
            self.master_key = decryption(self.master_key, self.password[0:32].encode(), True)
        else:
            self.master_key = self.create_master_key()

    def create_folder(self):
        if os.path.exists(self.base_path):
            return
        os.makedirs(self.base_path)

    def create_master_key(self):
        self.master_key = get_random_bytes(32)

    def decrypt_file(self, path, server):
        try:
            encrypted_content = retrieve_file(path, server, self)
            key = self.map_keys[path].encode()
            fernet = Fernet(key)
            content = fernet.decrypt(encrypted_content.encode()).decode()
            return content

        except Exception as e:
            print(e)
            return

    def encrypt_file(self, content, path, server):
        path = os.path.abspath(path)

        if path in self.map_keys.keys():
            key = self.map_keys[path].encode()
            fernet = Fernet(key)
            encrypted_content = fernet.encrypt(content.encode()).decode()
            save_file(encrypted_content, path, server, self)

        else:
            key = Fernet.generate_key()
            fernet = Fernet(key)
            self.map_keys[path] = key.decode()
            encrypted_content = fernet.encrypt(content.encode()).decode()

        save_file(encrypted_content, path, server, self)
