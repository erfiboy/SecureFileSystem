import getpass
import hashlib

from client import Client
from server.main import KeyEchange
from server.utiles.aes import encryption


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
    return is_signup, client


def client_login(server, session_key):
    username = input("Enter your user username: ")
    password = getpass.getpass("Enter your user password: ")
    client = Client(username, password)

    message = f"{username} {hashlib.sha256(password.encode()).hexdigest()}"
    cipher_text = encryption(message, session_key)
    is_login = server.login(cipher_text)
    return is_login, client
