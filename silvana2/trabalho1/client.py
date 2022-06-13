from ipaddress import ip_address
import socket
import json

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
	size = min(len(text), 254)
	
	# limit the message size
	text = text[:size]
	
	# concatenate the first byte(size) with the message, and return
	size += 1
	arr = [size.to_bytes(1, byteorder = "little"), text.encode("utf-8")]
	return b''.join(arr)



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
	# --| login |-- class function
	# Description: process the login request
	# Input: the request dictionary, the user address, and the dictionary of users
	# Output: the response dictionary
	def login(request, address, users):
		response = {"operacao": "login"}
		
		user = request["username"]
		port = request["porta"]
		
		if user in users:
			response["status"] = 400
			response["mensagem"] = "Username em Uso"
		else:
			response["status"] = 200
			response["mensagem"] = "Login com sucesso"
			
			users[user] = {"Endereco": address[0], "Porta": str(port)}
		
		return response
			
			
	
	# --| logoff |-- class function
	# Description: process the logoff request
	# Input: the request dictionary and the dictionary of users
	# Output: the response dictionary
	def logoff(request, users):
		try:
			user = request["username"]
			del users[user]
			
			return {"operacao": "logoff", "status": 200, "mensagem": "Logoff com sucesso"}
		except:
			return {"operacao": "get_lista", "status": 400, "mensagem": "Erro no Logoff"}
	
	
	
	# --| getList |-- class function
	# Description: process the getList request
	# Input: the dictionary of users
	# Output: the response dictionary
	def getList(users):
		try:
			return {"operacao": "get_lista", "status": 200, "clientes": users}
		except:
			return {"operacao": "get_lista", "status": 400, "mensagem": "Erro ao obter a lista"}
	
	
	
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
	
	
	
	# --| doRequest |-- method
	# Description: receive, process the request, and send a response
	# Input: empty
	# Output: empty
	def doRequest(self):
		# do connection
		conn, address = self.client.clientSocket.accept()
		
		# get size and text
		size = int.from_bytes(conn.recv(1), byteorder = "little")
		text = conn.recv(size - 1).decode("utf-8")
		
		# convert into JSON and produce a JSON response
		try:
			request = json.loads(text)			# load the JSON request
			response = self.doResponse(request)	# produce a JSON response
			data = jsonToData(response)			# convert it into bytes
		except BaseException as e:
			print(f"JSON loading error: {e}")				# show error
			data = (1).to_bytes(1, byteorder = "little")	# data is x00
		
		# send the response data and close conection
		conn.sendall(data)
		conn.close()
		
	
	
	# --| doResponse |-- method
	# Description: process the request and write a response based on the given request
	# Input: a dictionary request and a tuple of the client's address and port
	# Output: a dictionary response
	def doResponse(self, request):
		username = request["username"]
		
		with self.client.sharedMemoryLock:
			messages = self.client.sharedMemory[username][0]
			requests = self.client.sharedMemory['R']
			
			response = None
			
			if request["operacao"] == "login":
				response = RequestThread.login(request, address, users)
			elif request["operacao"] == "logoff":
				response = RequestThread.logoff(request, users)
			elif request["operacao"] == "get_lista":
				response = RequestThread.getList(users)
			
			requests.append((address, request, response))
		
		return response



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
			self.messageText.insert(tk.END, "\n")
		self.messageText.insert(tk.END, string)
		self.messageText.see(tk.END)
		
		self.messageText.config(state = tk.DISABLED)
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	
	
	
	'''
	+---------------
	| Widgets
	+---------------
	'''
	def declareWidgets(self):
		# root
		self.root = tk.Toplevel(self.client.root)
		self.root.title(self.username)
		self.root.geometry("690x460")
		
		# frames
		self.messageFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.sendFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		
		# messages shown on a text widget
		self.messageText = tk.Text(self.messageFrame, state = tk.DISABLED)
		
		# scrollbar of the messages' text
		self.messageScrollbar = ttk.Scrollbar(self.messageFrame, command = self.messageText.yview)
		self.messageText.config(yscrollcommand = self.messageScrollbar.set)
		
		# send entry
		self.sendEntryStringVar = tk.StringVar(self.sendFrame, value = "Your message here!")
		self.sendEntry = ttk.Entry(self.sendFrame, textvariable = self.sendEntryStringVar)
		
		# send button
		self.sendButton = ttk.Button(self.sendFrame, text = "Send", command = None)
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# main frames
		self.messageFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		self.sendFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		
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
		self.usernamePort = None	# client port
		
		self.host = None		# server ip
		self.hostPort = None	# server port
		
		self.users = {}	# dictionary of ip and port of each logged in user
		
		# create widgets, put them on the window, and run the window
		self.declareWidgets()
		self.packWidgets()
		
		self.testChat = Chat(self, "lixão", "", 0)
		
		self.root.mainloop()
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# --| declareUsernameHostPort |-- method
	# Description: declare username, host, and port from their correspondent widget entries
	# Input: empty
	# Output: empty
	def declareUsernameHostPort(self):
		self.username = self.usernameEntryStringVar.get()
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
		
		# send request
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((self.host, self.hostPort))
			s.sendall(data)
			
			# get size and text
			size = int.from_bytes(s.recv(1), byteorder = "little")
			text = s.recv(size).decode("utf-8")
		
		# process response
		response = json.loads(text)
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
		
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((self.host, self.hostPort))
			s.sendall(data)
			
			# get size and text
			size = int.from_bytes(s.recv(1), byteorder = "little")
			text = s.recv(size).decode("utf-8")
		
		# process response
		response = json.loads(text)
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
		
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((self.host, self.hostPort))
			s.sendall(data)
			
			# get size and text
			size = int.from_bytes(s.recv(1), byteorder = "little")
			text = s.recv(size).decode("utf-8")
		
		# process response
		response = json.loads(text)
		print(response)
		
		status = response["status"]
		
		if status == 200:
			self.users = response["clientes"]
			self.userListboxStringVar.set(list(self.users.keys()))
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
			messagebox.showerror("Client error", f"Fail to display users!\n{e}")
	
	
	
	# log in and log off radiobuttons event
	def loginLogoffRadiobuttonEvent(self):
		if self.loginLogoffBooleanVar.get():
			try:
				self.declareUsernameHostPort()
				self.login()
				messagebox.showinfo("Client status", f"Logging in as {self.usernameEntryStringVar.get()}!")
			except BaseException as e:
				self.loginLogoffBooleanVar.set(False)
				messagebox.showerror("Client error", f"Fail to log in!\n{e}")
		else:
			try:
				self.logoff()
				messagebox.showinfo("Client status", f"Logging off!")
			except BaseException as e:
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
		#print("Chatting!")
		messagebox.showinfo("Message", f"Chatting with {self.userListbox.get(tk.ANCHOR)}!")
		print(self.testToplevel)
		self.testToplevel.destroy()
		self.testToplevel.update()
		print(self.testToplevel)
	
	
	
	# exit button event
	def exitButtonEvent(self):
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
		self.root.geometry("400x240")
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
		
		# username port label
		self.usernamePortLabel = ttk.Label(self.usernamePortFrame, text = "Your Port:")
		
		# username port entry
		self.usernamePortEntryStringVar = tk.StringVar(self.usernamePortFrame, value = "32769")
		self.usernamePortEntry = ttk.Entry(self.usernamePortFrame, textvariable = self.usernamePortEntryStringVar)
		
		# host label
		self.hostLabel = ttk.Label(self.hostPortFrame, text = "Host IP:")

		# host entry
		self.hostEntryStringVar = tk.StringVar(self.hostPortFrame, value = "192.168.0.1")
		self.hostEntry = ttk.Entry(self.hostPortFrame, textvariable = self.hostEntryStringVar)

		# host port label
		self.hostPortLabel = ttk.Label(self.hostPortFrame, text = "Host Port:")

		# host port entry
		self.hostPortEntryStringVar = tk.StringVar(self.hostPortFrame, value = "32768")
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
		self.usernamePortLabel.grid(row = 2, column = 0, sticky = tk.W)
		self.usernamePortEntry.grid(row = 2, column = 1, sticky = tk.E)
		
		self.hostPortFrame.pack(side = tk.TOP, fill = tk.BOTH)
		self.hostLabel.grid(row = 1, column = 0, sticky = tk.W)
		self.hostEntry.grid(row = 1, column = 1, sticky = tk.E)
		self.hostPortLabel.grid(row = 2, column = 0, sticky = tk.W)
		self.hostPortEntry.grid(row = 2, column = 1, sticky = tk.E)
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
