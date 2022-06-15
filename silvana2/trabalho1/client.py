import socket
from threading import Thread, Lock
import json

import traceback

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox



'''
+---------------
| Functions
+---------------
'''
# --| jsonToData |-- function
# Description: convert JSON response to data
# Input: a response dictionary
# Output: a data composed by 1 byte representing the size of the whole data, concatenated with the remaining bytes
def jsonToData(response):
	# get message size
	text = json.dumps(response, separators = (',', ':'))
	size = min(len(text), 65535 - 2)
	
	# limit the message size
	text = text[:size]
	
	# concatenate the first byte(size) with the message, and return
	size += 2
	arr = [size.to_bytes(2, byteorder = "big"), text.encode("utf-8")]
	return b''.join(arr)



def recvAll(conn):
	# get size and text
	size = int.from_bytes(conn.recv(2), byteorder = "big")
	arr = []
	
	x = size
	while 0 < x:
		s = min(x, 1024)
		arr.append(conn.recv(s))
		x -= 1024
	
	return b''.join(arr)



def sendRequest(data, ip, port):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((ip, port))
		s.sendall(data)
		response = recvAll(s)
	
	return response



# ----------------



'''
+---------------
| Classes
+---------------
'''
# --| RequestThread |-- class
# Description: do the request-response comunication
class RequestThread:
	# RequestThread constructor
	# Description: declare the class's atributes
	# Input: a Client object
	def __init__(self, client):
		self.client = client
	
	
	
	'''
	+---------------
	| Class Functions
	+---------------
	'''
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	
	
	
	# --| run |-- method
	# Description: do a single request-response comunication talk
	# Input: empty
	# Output: empty
	def run(self):
		try:
			self.doRequest()
		except BaseException as e:
			print(f"Request accepting error: {str(e)}")
			traceback.print_exc()
	
	
	
	# --| doRequest |-- method
	# Description: receive and process the request, but do not send a response
	# Input: empty
	# Output: empty
	def doRequest(self):
		# do connection
		conn, address = self.client.clientSocket.accept()
		
		# get data
		data = recvAll(conn)

		conn.close()

		print(data.decode("utf-8"))
		
		# convert data into JSON and write the message on the chat
		try:
			request = json.loads(data.decode("utf-8"))	# load the JSON request
			
			username = request["username"]
			message = request["mensagem"]
			
			self.client.getList()
			
			with self.client.sharedMemoryLock:
				chats = self.client.sharedMemory['C']
				user = self.client.sharedMemory['U'][username]
				
				if username not in chats:
					chats[username] = Chat(self.client, username, user["Endereco"], user["Porta"])
				
				chat = chats[username]
			
			with chat.textLock:
				chat.writeOnText(f'{username} diz:\n{message}')	
		except BaseException as e:
			print(f"JSON loading error: {e}")			# show error
			traceback.print_exc()



# ----------------



# --| Chat |-- class
# Description: deal with a chat window
class Chat:
	# Chat constructor
	# Description: declare the class's atributes, initiates the widgets, and run the window
	# Input: a Client object
	def __init__(self, client, username, ip, port):
		self.client = client
		self.username = username
		self.ip = ip
		self.port = port
		self.textLock = Lock()
		
		self.declareWidgets()
		self.packWidgets()
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# --| writeOnText |-- method
	# Description: write on the window text similar to python's built-in print function
	# Input: a string
	# Output: empty
	def writeOnText(self, string):
		self.messageText.config(state = tk.NORMAL)
		
		if 1 < len(self.messageText.get(1.0, tk.END)):
			self.messageText.insert(tk.END, "\n\n")
		self.messageText.insert(tk.END, string)
		self.messageText.see(tk.END)
		
		self.messageText.config(state = tk.DISABLED)
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	def sendButtonEvent(self):
		# get message written on entry
		message = self.sendEntryStringVar.get()
		
		# create the request data
		request = {
			"username": self.client.username,
			"mensagem": message
		}
		
		data = jsonToData(request)
		
		# test
		# print(self.ip, self.port)
		
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.connect((self.ip, self.port))
				s.sendall(data)
		except BaseException as e:
			traceback.print_exc()
			messagebox.showerror("Chat error", f"The application could not send the message!\n{e}")
		
		with self.textLock:
			self.writeOnText(f'Você diz:\n{message}')
	
	
	
	def closeWindowEvent(self):
		with self.client.sharedMemoryLock:
			chats = self.client.sharedMemory['C']
			
			if self.username in chats:
				del chats[self.username]
		
		self.root.destroy()
	
	
	
	'''
	+---------------
	| Widgets
	+---------------
	'''
	def declareWidgets(self):
		# root
		self.root = tk.Toplevel(self.client.root)
		self.root.title(self.username)
		self.root.geometry("770x510")
		self.root.protocol("WM_DELETE_WINDOW", self.closeWindowEvent)
		
		# frames
		self.messageFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.sendFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		
		# messages shown on a text widget
		# FONT
		self.messageText = tk.Text(self.messageFrame, state = tk.DISABLED, font = ('Arial', 12, 'normal'))
		
		# scrollbar of the messages' text
		self.messageScrollbar = ttk.Scrollbar(self.messageFrame, command = self.messageText.yview)
		self.messageText.config(yscrollcommand = self.messageScrollbar.set)
		
		# send entry
		self.sendEntryStringVar = tk.StringVar(self.sendFrame, value = "")
		self.sendEntry = ttk.Entry(self.sendFrame, textvariable = self.sendEntryStringVar)
		
		# send button
		self.sendButton = ttk.Button(self.sendFrame, text = "Send", command = self.sendButtonEvent)
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# main frames
		self.messageFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		self.sendFrame.pack(side = tk.TOP, fill = tk.X)
		
		# message frame
		self.messageText.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.messageScrollbar.pack(side = tk.RIGHT, fill = tk.Y)
		
		# send frame
		self.sendEntry.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.sendButton.pack(side = tk.RIGHT, fill = tk.Y)



# ----------------



# --| Client |-- class
# Description: deal with window, its widgets, and the comunication with the server
class Client:
	# Client constructor
	# Description: declare the class's atributes, initiates the widgets, and run the window
	# Input: empty
	def __init__(self):
		# declare atributes
		self.username = None		# client username
		self.usernameIP = None		# client IP
		self.usernamePort = None	# client port
		
		self.host = None		# server ip
		self.hostPort = None	# server port
		
		self.clientSocket = None
		
		# create widgets, put them on the window, and run the window
		self.declareWidgets()
		self.packWidgets()
		
		#self.testChat = Chat(self, "lixão", "", 0)
		
		self.root.mainloop()
	
	

	'''
	+---------------
	| Functions
	+---------------
	'''
	# --| requestThreadMain |-- class method
	# Description: requestThread main function
	# Input: the Server object
	# Output: empty
	def requestThreadMain(client):
		request = RequestThread(client)
		
		while client.loginLogoffBooleanVar.get():
			request.run()


	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# --| declareRequestThreads |-- method
	# Description: initiate variables for request handling
	# Input: empty
	# Output: empty
	def declareRequestThreads(self):
		self.sharedMemory = {
			'U': {},
			'C': {}
		}
		self.sharedMemoryLock = Lock()
		
		self.users = {}
	


	# --| bind |-- method
	# Description: bind the server's socket
	# Input: empty
	# Output: empty
	def bind(self):
		self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		self.clientSocket.bind((self.usernameIP, self.usernamePort))
		self.clientSocket.listen(5)
		self.clientSocket.setblocking(True)
	
	
	
	# --| run |-- method
	# Description: run the server and the GUI polling through runRadiobutton
	# Input: empty
	# Output: empty
	def run(self):
		self.declareRequestThreads()
		
		requestThread = Thread(target = Client.requestThreadMain, args = (self,))
		requestThread.daemon = True
		requestThread.start()
	
	
	
	# --| stop |-- method
	# Description: stop the server through stopRadiobutton
	# Input: empty
	# Output: empty
	def stop(self):
		self.loginLogoffBooleanVar.set(False)
		if self.clientSocket is not None:
			self.clientSocket.close()
	
	
	
	# --| declareUsernameHostPort |-- method
	# Description: declare username, host, and port from their correspondent widget entries
	# Input: empty
	# Output: empty
	def declareUsernameHostPort(self):
		self.username = self.usernameEntryStringVar.get()
		self.usernameIP = self.usernameIPEntryStringVar.get()
		self.usernamePort = int(self.usernamePortEntryStringVar.get())
		
		self.host = self.hostEntryStringVar.get()
		self.hostPort = int(self.hostPortEntryStringVar.get())
	
	
	
	# --| login |-- method
	# Description: send a request to log in
	# Input: empty
	# Output: empty
	def login(self):
		# create the request data
		request = {
			"operacao": "login",
			"username": self.username,
			"porta": self.usernamePort
		}
		
		data = jsonToData(request)
		
		# test
		# print(socket.gethostbyname(socket.gethostname()))
		
		# send request and receive response
		data = sendRequest(data, self.host, self.hostPort)
		
		# process response
		response = json.loads(data.decode("utf-8"))
		
		# test
		print(response)
		
		status = response["status"]
		message = response["mensagem"]
		
		if status == 200:
			pass
		elif status == 400:
			raise Exception(message)
		else:
			raise Exception(f"Invalid status: {status}\n")
	
	
	
	# --| logoff |-- method
	# Description: send a request to log off
	# Input: empty
	# Output: empty
	def logoff(self):
		# create the request data
		request = {
			"operacao": "logoff",
			"username": self.username
		}
		
		data = jsonToData(request)
		
		# send request and receive response
		data = sendRequest(data, self.host, self.hostPort)
		
		# process response
		response = json.loads(data.decode("utf-8"))
		
		# test
		print(response)
		
		status = response["status"]
		
		if status == 200:
			pass
		elif status == 400:
			message = response["mensagem"]
			raise Exception(message)
		else:
			raise Exception(f"Invalid status: {status}\n")
	
	
	
	# --| getList |-- method
	# Description: send a request to get the list of logged in users
	# Input: empty
	# Output: empty
	def getList(self):
		# create the request data
		request = {
			"operacao": "get_lista",
		}
		
		data = jsonToData(request)
		
		# send request and receive response
		data = sendRequest(data, self.host, self.hostPort)
		
		# process response
		response = json.loads(data.decode("utf-8"))
		
		# test
		print(response)
		
		status = response["status"]
		
		if status == 200:
			users = response["clientes"]
			
			with self.sharedMemoryLock:
				self.sharedMemory['U'] = users
			
			self.userListboxStringVar.set(list(users.keys()))
		elif status == 400:
			message = response["mensagem"]
			raise Exception(message)
		else:
			raise Exception(f"Invalid status: {status}\n")
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	# display users button event
	def displayUsersButtonEvent(self):
		try:
			self.getList()
		except BaseException as e:
			traceback.print_exc()
			messagebox.showerror("Client error", f"Fail to display users!\n{e}")
	
	
	
	# log in and log off radiobuttons event
	def loginLogoffRadiobuttonEvent(self):
		if self.loginLogoffBooleanVar.get():
			try:
				self.declareUsernameHostPort()
				self.login()
				self.bind()
				self.run()
				messagebox.showinfo("Client status", f"Logging in as {self.usernameEntryStringVar.get()}!")
			except BaseException as e:
				traceback.print_exc()
				self.loginLogoffBooleanVar.set(False)
				messagebox.showerror("Client error", f"Fail to log in!\n{e}")
		else:
			try:
				self.logoff()
				self.stop()
				messagebox.showinfo("Client status", f"Logging off!")
			except BaseException as e:
				traceback.print_exc()
				self.loginLogoffBooleanVar.set(True)
				messagebox.showerror("Client error", f"Fail to log off!\n{e}")
		
		# toggle states of entries and display whenever logging in or logging off
		loginState = tk.NORMAL
		logoffState = tk.DISABLED
		if self.loginLogoffBooleanVar.get():
			loginState = tk.DISABLED
			logoffState = tk.NORMAL
		
		self.loginRadiobutton.config(state = loginState)
		for child in self.usernamePortFrame.winfo_children():
			child.config(state = loginState)
		for child in self.hostPortFrame.winfo_children():
			child.config(state = loginState)
		
		self.logoffRadiobutton.config(state = logoffState)
		self.chatButton.config(state = logoffState)
		self.userListbox.config(state = logoffState)
		self.displayUsersButton.config(state = logoffState)
	
	
	
	# chat button event
	def chatButtonEvent(self):
		try:
			username = self.userListbox.get(tk.ANCHOR)
			self.getList()
			with self.sharedMemoryLock:
				chats = self.sharedMemory['C']
				user = self.sharedMemory['U'][username]
				
				if username not in chats:
					chats[username] = Chat(self, username, user["Endereco"], user["Porta"])
		except BaseException as e:
			traceback.print_exc()
			messagebox.showerror("Client error", f"Fail to chat!\n{e}")
	
	
	
	# exit button event
	def exitButtonEvent(self):
		self.stop()
		self.root.quit()
	
	
	
	'''
	+---------------
	| Widgets
	+---------------
	'''
	def declareWidgets(self):
		# root
		self.root = tk.Tk()
		self.root.title("Client")
		self.root.geometry("420x260")
		self.root.protocol("WM_DELETE_WINDOW", self.exitButtonEvent)
		#root.resizable(False, False
		
		# frames
		self.leftFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.rightFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.usersFrame = ttk.Frame(self.leftFrame, padding = 8)
		self.usernamePortFrame = ttk.Frame(self.rightFrame, padding = 8, borderwidth = 2, relief = "groove")
		self.hostPortFrame = ttk.Frame(self.rightFrame, padding = 8, borderwidth = 2, relief = "groove")
		self.loginLogoffFrame = ttk.Frame(self.rightFrame, padding = 8, borderwidth = 2, relief = "groove")
		
		# list of users
		self.userListboxStringVar = tk.StringVar(self.usersFrame)
		self.userListbox = tk.Listbox(self.usersFrame, state = tk.DISABLED, listvariable = self.userListboxStringVar)
		
		# scrollbar of the list of users
		self.userScrollbar = ttk.Scrollbar(self.usersFrame, command = self.userListbox.yview)
		self.userListbox.config(yscrollcommand = self.userScrollbar.set)
		
		# display users button
		self.displayUsersButton = ttk.Button(self.leftFrame, text = "Display Users", state = tk.DISABLED, command = self.displayUsersButtonEvent)
		
		# username label
		self.usernameLabel = ttk.Label(self.usernamePortFrame, text = "Username:")
		
		# username entry
		self.usernameEntryStringVar = tk.StringVar(self.usernamePortFrame, value = "Nata da Nata")
		self.usernameEntry = ttk.Entry(self.usernamePortFrame, textvariable = self.usernameEntryStringVar)
		
		# username label
		self.usernameIPLabel = ttk.Label(self.usernamePortFrame, text = "Username IP:")
		
		# username entry
		self.usernameIPEntryStringVar = tk.StringVar(self.usernamePortFrame, value = "192.168.0.1")
		self.usernameIPEntry = ttk.Entry(self.usernamePortFrame, textvariable = self.usernameIPEntryStringVar)
		
		# username port label
		self.usernamePortLabel = ttk.Label(self.usernamePortFrame, text = "Your Port:")
		
		# username port entry
		self.usernamePortEntryStringVar = tk.StringVar(self.usernamePortFrame, value = "30001")
		self.usernamePortEntry = ttk.Entry(self.usernamePortFrame, textvariable = self.usernamePortEntryStringVar)
		
		# host label
		self.hostLabel = ttk.Label(self.hostPortFrame, text = "Host IP:")

		# host entry
		self.hostEntryStringVar = tk.StringVar(self.hostPortFrame, value = "192.168.0.1")
		self.hostEntry = ttk.Entry(self.hostPortFrame, textvariable = self.hostEntryStringVar)

		# host port label
		self.hostPortLabel = ttk.Label(self.hostPortFrame, text = "Host Port:")

		# host port entry
		self.hostPortEntryStringVar = tk.StringVar(self.hostPortFrame, value = "30000")
		self.hostPortEntry = ttk.Entry(self.hostPortFrame, textvariable = self.hostPortEntryStringVar)
		
		# separators
		#self.rightSeparator = ttk.Separator(self.usernameHostPortFrame, orient = tk.HORIZONTAL)
		
		# login logoff Radiobuttons
		self.loginLogoffBooleanVar = tk.BooleanVar(self.loginLogoffFrame, False)
		self.loginRadiobutton = tk.Radiobutton(
			self.loginLogoffFrame,
			text = "Log In",
			variable = self.loginLogoffBooleanVar,
			value = True,
			background = "#40c040",
			borderwidth = 2,
			relief = "groove",
			command = self.loginLogoffRadiobuttonEvent
		)
		self.logoffRadiobutton = tk.Radiobutton(
			self.loginLogoffFrame,
			text = "Log Off",
			variable = self.loginLogoffBooleanVar,
			value = False,
			state = tk.DISABLED,
			background = "#c04040",
			borderwidth = 2,
			relief = "groove",
			command = self.loginLogoffRadiobuttonEvent
		)
		
		# chat button
		self.chatButton = ttk.Button(self.rightFrame, text = "Chat!", state = tk.DISABLED, command = self.chatButtonEvent)
		
		# exit button
		self.exitButton = ttk.Button(self.rightFrame, text = "Exit", command = self.exitButtonEvent)
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# main frames
		self.leftFrame.pack(side = tk.LEFT, fill = tk.Y)#, expand = True)
		self.rightFrame.pack(side = tk.RIGHT, fill = tk.BOTH, expand = True)
		
		# left frame
		self.usersFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		
		self.userListbox.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.userScrollbar.pack(side = tk.RIGHT, fill = tk.Y)
		
		self.displayUsersButton.pack(side = tk.BOTTOM, fill = tk.X)
		
		# right frame
		self.usernamePortFrame.pack(side = tk.TOP, fill = tk.BOTH)
		self.usernameLabel.grid(row = 0, column = 0, sticky = tk.W)
		self.usernameEntry.grid(row = 0, column = 1, sticky = tk.E)
		self.usernameIPLabel.grid(row = 1, column = 0, sticky = tk.W)
		self.usernameIPEntry.grid(row = 1, column = 1, sticky = tk.E)
		self.usernamePortLabel.grid(row = 2, column = 0, sticky = tk.W)
		self.usernamePortEntry.grid(row = 2, column = 1, sticky = tk.E)
		
		self.hostPortFrame.pack(side = tk.TOP, fill = tk.BOTH)
		self.hostLabel.grid(row = 0, column = 0, sticky = tk.W)
		self.hostEntry.grid(row = 0, column = 1, sticky = tk.E)
		self.hostPortLabel.grid(row = 1, column = 0, sticky = tk.W)
		self.hostPortEntry.grid(row = 1, column = 1, sticky = tk.E)
		#self.rightSeparator.grid(row = 3, column = 0, columnspan = 2, pady = 8, sticky = tk.EW)
		
		self.loginLogoffFrame.pack(side = tk.TOP, fill = tk.X)
		self.loginRadiobutton.pack(side = tk.LEFT, fill = tk.X, expand = True)
		self.logoffRadiobutton.pack(side = tk.RIGHT, fill = tk.X, expand = True)
		
		self.chatButton.pack(side = tk.TOP, fill = tk.X, expand = True)
		
		self.exitButton.pack(side = tk.BOTTOM, fill = tk.X)



# ----------------



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	client = Client()
