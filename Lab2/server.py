import os
import socket
import uuid
from datetime import datetime


def welcome(client):
    welcome_message = """
    Welcome!
    The list of commands you can use:
    - ECHO <message>: returns "message";
    - TIME: returns the current server time;
    - UPLOAD <filename>: uploads a file to the server;
    - DOWNLOAD <filename>: downloads a file from the server;
    - QUIT: closes the connection.\n"""

    client.sendall(welcome_message.encode('utf-8'))


def echo(message):
    # split a message into parts by spaces
    command_parts = message.decode('utf-8').split(' ', 1)
    return command_parts[1].encode('utf-8')


def time():
    current_time = datetime.now().strftime("%H:%M:%S")
    return current_time.encode('utf-8')


def upload(client, message):
    parts = message.decode('utf-8').split(' ', 1)
    filename = parts[1]
    file_size = int(client.recv(1024).decode('utf-8'))
    received_size = 0

    if os.path.exists(filename + '.temp'):
        print(f"The client has continued to upload {filename}.")
        os.rename(filename + '.temp', filename)
        received_size = os.path.getsize(filename)
        client.sendall(str(received_size).encode('utf-8'))
    else:
        client.sendall(str(received_size).encode('utf-8'))

    with open(filename, "ab" if received_size > 0 else "wb") as file:
        while received_size < file_size:
            file_data = client.recv(1024)
            if not file_data:
                print("\nUploading was interrupted.")
                os.rename(filename, filename + '.temp')
                return "File wasn't uploaded.".encode('utf-8')
            file.write(file_data)
            received_size += len(file_data)

    print(f"File '{filename}' received")
    print(f"File '{filename}' saved")

    return "File uploaded successfully".encode('utf-8')


def download(client, message):
    parts = message.decode('utf-8').split(' ', 1)
    filename = parts[1]

    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        client.sendall(str(file_size).encode('utf-8'))
        client.recv(1024)  # Wait for client readiness
        with open(filename, 'rb') as file:
            while True:
                file_data = file.read(1024)
                if not file_data:
                    break
                client.sendall(file_data)
        print(f"File '{filename}' sent to the client")
    else:
        client.sendall("-1".encode('utf-8'))  # File not found


def handle_connection_loss(client_socket, filename):
    try_count = 0
    max_attempts = 3
    delay = 5  # seconds
    while try_count < max_attempts:
        try_count += 1
        print(f"Connection lost. Trying to resume transmission (Attempt {try_count} of {max_attempts})...")
        time.sleep(delay)
        try:
            with open(filename, "rb") as file:
                file.seek(client_socket.recv(1024))  # Seek to the last successfully received position
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    client_socket.sendall(data)
                print("File transmission resumed successfully.")
                return True
        except Exception as e:
            print(f"Failed to resume transmission: {e}")
    print("Failed to resume transmission after multiple attempts.")
    return False


def remove_temp_files():
    for filename in os.listdir():
        if filename.endswith('.temp'):
            os.remove(filename)


# IPv4 addresses, TCP-protocol
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# ! CHANGE to make it possible to connect from a different device
host = '127.0.0.1'
port = 12345
server_address = (host, port)

session_ids = {}

server_socket.bind(server_address)

# max queue length - 5
server_socket.listen(5)

print(f"Server is listening on {host}:{port}")

while True:
    print("\nWaiting for connection...")
    client_socket, client_address = server_socket.accept()
    print(f"\nConnection accepted from {client_address}")

    try:
        if client_address[0] not in session_ids:
            remove_temp_files()
            print("Temporary files removed for a new client")

# OTHER POSSIBLE VARIANTS: 1) structure, storing client addresses, 2) adding client address to the filename
        session_id = str(uuid.uuid4())
        session_ids[client_address[0]] = session_id

        welcome(client_socket)

        while True:
            data = client_socket.recv(1024)
            print(f"Data received: {data.decode('utf-8')}")

            if not data:
                print("\nConnection is lost.\n")
                client_socket.close()
                break

            if data.startswith(b'ECHO'):
                response = echo(data)
                client_socket.sendall(response)

            elif data.startswith(b'TIME'):
                response = time()
                client_socket.sendall(response)

            elif data.startswith(b'UPLOAD'):
                response = upload(client_socket, data)
                if response == "File wasn't uploaded.".encode('utf-8'):
                    client_socket.close()
                    break
                client_socket.sendall(response)

            elif data.startswith(b'DOWNLOAD'):
                responce = download(client_socket, data)
                parts = data.decode('utf-8').split(' ', 1)
                filename = parts[1]
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    client_socket.sendall(str(file_size).encode('utf-8'))
                    client_socket.recv(1024)  # Wait for client readiness
                    with open(filename, 'rb') as file:
                        while True:
                            file_data = file.read(1024)
                            if not file_data:
                                break
                            client_socket.sendall(file_data)
                    print(f"File '{filename}' sent to the client")
                else:
                    client_socket.sendall("-1".encode('utf-8'))  # File not found    

            elif data.startswith(b'QUIT'):
                print("Closing the connection")
                client_socket.close()
                break

            else:
                client_socket.sendall(b'Invalid command.\n')

# in case an exception occurs, the server shuts down
    except Exception as e:
        print(f"\nException occurred: {e}.")
        client_socket.close()

        if handle_connection_loss(client_socket, filename):
            print("Connection resumed successfully.")
        else:
            print("Failed to resume connection.")

        print("Shutting down the server")
        remove_temp_files()
        server_socket.close()
        break
