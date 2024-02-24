import socket
from datetime import datetime


def welcome(client):
    welcome_message = """
    Welcome! 
    The list of commands you can use:
    - ECHO <message>: returns "message";
    - TIME: returns the current server time;
    - QUIT: closes the connection.\n\n"""

    client.sendall(welcome_message.encode('utf-8'))


def echo(message):
    # split a message into parts by spaces
    parts = message.decode('utf-8').split(' ', 1)

    return parts[1].encode('utf-8')


def time():
    current_time = datetime.now().strftime("%H:%M:%S\n")
    return current_time.encode('utf-8')


# IPv4 addresses, TCP-protocol
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = '127.0.0.1'
port = 12345
server_address = (host, port)

server_socket.bind(server_address)

# max queue length - 5
server_socket.listen(5)

print(f"Server is listening on {host}:{port}")

while True:
    print("Waiting for connection...")
    client_socket, client_address = server_socket.accept()
    print(f"Connection accepted from {client_address}")

    welcome(client_socket)

    while True:
        data = client_socket.recv(1024)
        print(f"Data received: {data.decode('utf-8')}")

        if data.startswith(b'ECHO'):
            response = echo(data)
            client_socket.sendall(response)

        elif data.startswith(b'TIME'):
            response = time()
            client_socket.sendall(response)

        elif data.startswith(b'QUIT'):
            print("Closing connection")
            client_socket.close()
            break

        else:
            client_socket.sendall(b'Invalid command.\n')

# nmap -p 12345 127.0.0.1
# netstat -an | grep 12345
