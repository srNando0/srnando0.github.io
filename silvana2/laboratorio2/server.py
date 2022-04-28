import socket



# Criação do socket
HOST = 'localhost'
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(4)



'''
+---------------
| Camada de dados
+---------------
'''
# input: nome do arquivo em bytes
# output: uma dupla (T, E) onde T é o texto completo do arquivo e E é verdadeiro sse o arquivo existe
def dados(nomeDoArquivo):
	name = bytes(nomeDoArquivo).decode("utf-8")	# pega o nome do arquivo em formato str
	
	# tenta abrir o arquivo
	try:
		# arquivo encontrado
		with open(name, mode = 'r') as file:
			# retorna o texto inteiro do arquivo e um sinal de que o arquivo foi encontrado
			return (file.read(), True)
	except FileNotFoundError:
		# arquivo não encontrado, então retorna um sinal falso
		return ("", False)



'''
+---------------
| Camada de processamento
+---------------
'''
# input: um texto
# output: as 5 palavras mais frequentes
def contadorDePalavra(text):
	wordList = text.split()	# cria uma lista de palavras
	wordDict = {}	# dict para contar a ocorrência de cada palavra
	
	# conta as ocorrências
	for w in wordList:
		if w in wordDict:
			wordDict[w] += 1
		else:
			wordDict[w] = 1
	
	# ordena as palavras da mais frequente para a menos frequente
	frequencyList = sorted(wordDict.items(), key = lambda item: item[1], reverse = True)
	fiveWordsList = ""
	
	# pega as 5 primeiras palavras
	for i in range(min(len(frequencyList), 5)):
		fiveWordsList += frequencyList[i][0] + " "
	
	# retorna as 5 palavras mais frequentes
	return fiveWordsList
	

	
# input: nome do arquivo em bytes
# output: as 5 palavras mais frequentes, ou uma mensagem de erro de arquivo não encontrado
def processamento(nomeDoArquivo):
	# pega o texto inteiro e se o arquivo existe
	text, fileFound = dados(nomeDoArquivo)
	
	if fileFound:
		# se o arquivo existe, retorna as 5 palavras mais frequentes
		return contadorDePalavra(text).encode("utf-8")
	else:
		# se o arquivo não existe, retorna uma mensagem de erro de arquivo não encontrado
		return "Arquivo não encontrado".encode("utf-8")



# looping do servidor
loop = True
while loop:
	# aceita a conexão
	conn, addr = server.accept()
	
	# envia as 5 palavras mais frequentes
	conn.sendall(processamento(conn.recv(1024)))
	
	# fecha a conexão
	conn.close()
