import os
import socket


def main():
    # IPv4 addresses, TCP-protocol
    global parts
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # ! CHANGE to make it possible to connect from a different device
    host = '127.0.0.1'
    port = 12345
    server_address = (host, port)

    client_socket.connect(server_address)
    print(f"Connected to the server {host}:{port}")

    try:
        welcome_message = client_socket.recv(1024)
        print(welcome_message.decode('utf-8'))

        while True:
            command = input("Enter a command: ").strip()

            if command.startswith('ECHO') or command.startswith('UPLOAD'):
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
                parts = command.split(' ', 1)
                if len(parts) != 2:
                    print(f"Invalid command format. Usage: {parts[0]} <filename>")
                    continue
                filename = parts[1]
                with open(filename, "wb") as file:
                    file_size = int(client_socket.recv(1024).decode('utf-8'))
                    if file_size == -1:
                        print(f"File '{filename}' not found on the server.")
                        continue
                    client_socket.sendall(b"READY")  # Notify server to start sending
                    received_size = 0
                    while received_size < file_size:
                        file_data = client_socket.recv(1024)
                        if not file_data:
                            print("\nDownloading was interrupted.")
                            os.remove(filename)
                            break
                        file.write(file_data)
                        received_size += len(file_data)
                    print(f"File '{filename}' downloaded successfully.")

            else:
                response = client_socket.recv(1024)
                print(response.decode('utf-8'))

    except Exception as e:
        print(f"\nConnection lost: {e}")
        print("Attempting to reconnect...")
        client_socket.close()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(server_address)
        print("Connection restored successfully.")
        main()      

    finally:
        print("\nClosing the connection")
        client_socket.close()


if __name__ == "__main__":
    main()
