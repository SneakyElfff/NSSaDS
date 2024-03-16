import os
import socket


def main():
    # IPv4 addresses, TCP-protocol
    global parts
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = input("Enter server IP address: ")
    port = int(input("Enter server port: "))
    server_address = (host, port)

    client_socket.connect(server_address)
    print(f"Connected to the server {host}:{port}")

    try:
        welcome_message = client_socket.recv(1024)
        print(welcome_message.decode('utf-8'))

        while True:
            command = input("Enter a command: ").strip()

            if command.startswith('ECHO') or command.startswith('UPLOAD') or command.startswith('DOWNLOAD'):
                parts = command.split(' ', 1)
                if len(parts) != 2:
                    print(f"Invalid command format. Usage: {parts[0]} <message>")
                    continue

            client_socket.sendall(command.encode('utf-8'))

            if command.upper() == 'QUIT':
                break

            elif command.startswith('UPLOAD'):
                filename = parts[1]
                if os.path.exists(filename):
                    with open(filename, "rb") as file:
                        file_size = os.path.getsize(filename)
                        client_socket.sendall(str(file_size).encode('utf-8'))

                        sent_size = int(client_socket.recv(1024).decode('utf-8'))
                        if sent_size != 0:
                            print("The upload continues")
                        file.seek(sent_size)

                        while True:
                            data = file.read(1024)
                            if not data:
                                break
                            client_socket.sendall(data)

                        response = client_socket.recv(1024)
                        print(response.decode('utf-8'))
                else:
                    print("File not found.")

            elif command.startswith('DOWNLOAD'):
                filename = parts[1]
                file_size = int(client_socket.recv(1024).decode('utf-8'))
                if file_size == 0:
                    print("File not found on the server.")
                    continue

                received_size = 0

                if os.path.exists(filename):
                    print(f"The server has continued to send {filename}.")
                    received_size = os.path.getsize(filename)
                    client_socket.sendall(str(received_size).encode('utf-8'))
                else:
                    client_socket.sendall(str(received_size).encode('utf-8'))

                with open(filename, "ab" if received_size > 0 else "wb") as file:
                    while received_size < file_size:
                        file_data = client_socket.recv(1024)
                        file.write(file_data)
                        received_size += len(file_data)

                client_socket.sendall("File received".encode('utf-8'))

                response = client_socket.recv(1024)
                print(response.decode('utf-8'))

            else:
                response = client_socket.recv(1024)
                print(response.decode('utf-8'))

    finally:
        print("\nClosing the connection")
        client_socket.close()


if __name__ == "__main__":
    main()
