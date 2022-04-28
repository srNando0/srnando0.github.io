import socket



# Criação do socket
HOST = 'localhost'
PORT = 5000



'''
+---------------
| Camada de interface
+---------------
'''
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	# conecta com o servidor
	s.connect((HOST, PORT))
	
	# envia o nome do arquivo lido no terminal
	s.sendall(input().encode("utf-8"))
	
	# recebe as 5 palavras mais frequentes em forma de bytes
	data = s.recv(1024)

# exibe as 5 palavras mais frequentes
print(data.decode("utf-8"))
