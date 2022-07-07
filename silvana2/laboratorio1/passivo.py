import socket

HOST = '10.11.0.10'
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

conn, addr = server.accept()

while True:
    data = conn.recv(1024)
    if not data:
        break

    conn.sendall(data)

conn.close()
