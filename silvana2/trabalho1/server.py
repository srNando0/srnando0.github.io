import socket
from threading import Thread, Lock
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
	# Input: a Server object
	def __init__(self, server):
		self.server = server
	
	
	
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
			
			users[user] = {"Endereco": address[0], "Porta": port}
		
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
		conn, address = self.server.serverSocket.accept()
		
		# get size and text
		size = int.from_bytes(conn.recv(1), byteorder = "little")
		text = conn.recv(size - 1).decode("utf-8")
		
		# convert into JSON and produce a JSON response
		try:
			request = json.loads(text)						# load the JSON request
			response = self.doResponse(request, address)	# produce a JSON response
			data = jsonToData(response)						# convert it into bytes
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
	def doResponse(self, request, address):
		with self.server.sharedMemoryLock:
			users = self.server.sharedMemory['U']
			requests = self.server.sharedMemory['R']
			
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



# --| Server |-- class
# Description: deal with window, its widgets, and the requestThreads
class Server:
	# Server constructor
	# Description: declare the class's atributes, initiates the widgets, and run the window
	# Input: empty
	def __init__(self):
		# declare atributes
		self.host = None			# server ip
		self.port = None			# server port
		self.serverSocket = None	# server socket
		
		# create widgets, put them on the window, and run the window
		self.declareWidgets()
		self.packWidgets()
		
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
	def requestThreadMain(server):
		request = RequestThread(server)
		
		while server.runStopBooleanVar.get():
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
			'R': []
		}
		self.sharedMemoryLock = Lock()
		
		self.users = {}
	
	
	
	# --| bind |-- method
	# Description: bind the server's socket
	# Input: empty
	# Output: empty
	def bind(self):
		self.host = self.hostEntryStringVar.get()
		self.port = int(self.portEntryStringVar.get())
		
		self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		self.serverSocket.bind((self.host, self.port))
		self.serverSocket.listen(5)
		self.serverSocket.setblocking(True)
	
	
	
	# --| run |-- method
	# Description: run the server and the GUI polling through runRadiobutton
	# Input: empty
	# Output: empty
	def run(self):
		self.declareRequestThreads()
		self.clearText()
		self.userListboxStringVar.set([])
		
		requestThread = Thread(target = Server.requestThreadMain, args = (self,))
		requestThread.daemon = True
		requestThread.start()
		
		self.requestText.after(1000, self.requestTextAfter)
	
	
	
	# --| stop |-- method
	# Description: stop the server through stopRadiobutton
	# Input: empty
	# Output: empty
	def stop(self):
		self.runStopBooleanVar.set(False)
		if self.serverSocket is not None:
			self.serverSocket.close()
	
	
	
	# --| requestTextAfter |-- method
	# Description: window GUI polling
	# Input: empty
	# Output: empty
	def requestTextAfter(self):
		self.gui()
		if self.runStopBooleanVar.get():
			self.root.after(1000, self.requestTextAfter)
	
	
	
	# --| gui |-- method
	# Description: update the GUI
	# Input: empty
	# Output: empty
	def gui(self):
		# get data
		with self.sharedMemoryLock:
			self.users = self.sharedMemory['U'].copy()
			
			requests = self.sharedMemory['R'].copy()
			self.sharedMemory['R'] = []
		
		# exhibit logged users
		self.userListboxStringVar.set(list(self.users.keys()))
		
		for r in requests:
			address, request, response = r
			
			self.writeOnText(f"----{address}----\nRequest: {request}\nResponse: {response}")
	
	
	
	# --| clearText |-- method
	# Description: clear the window text
	# Input: empty
	# Output: empty
	def clearText(self):
		self.requestText.config(state = tk.NORMAL)
		
		self.requestText.delete('1.0', tk.END)
		self.requestText.see(tk.END)
		
		self.requestText.config(state = tk.DISABLED)
	
	
	
	# --| writeOnText |-- method
	# Description: write on the window text similar to python's built-in print function
	# Input: a string
	# Output: empty
	def writeOnText(self, string):
		self.requestText.config(state = tk.NORMAL)
		
		if 1 < len(self.requestText.get(1.0, tk.END)):
			self.requestText.insert(tk.END, "\n")
		self.requestText.insert(tk.END, string)
		self.requestText.see(tk.END)
		
		self.requestText.config(state = tk.DISABLED)
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	# run and stop radiobuttons event
	def runStopRadiobuttonEvent(self):
		# run and stop the server based on radiobuttons
		if self.runStopBooleanVar.get():
			# run the server
			try:
				self.bind()
				self.run()
				messagebox.showinfo("Server status", "Server running!")
			except BaseException as e:
				self.runStopBooleanVar.set(False)
				messagebox.showerror("Server error", f"Error during server running!\n{str(e)}")
				return
		else:
			# stop the server
			try:
				self.stop()
				messagebox.showinfo("Server status", "Server stopped!")
			except BaseException as e:
				self.runStopBooleanVar.set(True)
				messagebox.showerror("Server error", f"Error during server stopping!\n{str(e)}")
		
		# toggle states of entries and display whenever logging in or logging off
		runState = tk.NORMAL
		stopState = tk.DISABLED
		if self.runStopBooleanVar.get():
			runState = tk.DISABLED
			stopState = tk.NORMAL
		
		self.runRadiobutton.config(state = runState)
		for child in self.hostPortFrame.winfo_children():
			child.config(state = runState)
			
		self.stopRadiobutton.config(state = stopState)
		self.userListbox.config(state = stopState)
		self.userButton.config(state = stopState)
	
	
	
	# get user's IP and Port
	def userButtonEvent(self):
		username = self.userListbox.get(tk.ANCHOR)
		
		if username in self.users:
			userInfo = self.users[username]
			messagebox.showinfo(f"{username} info", f'IP: {userInfo["Endereco"]}\nPort: {userInfo["Porta"]}')
		else:
			messagebox.showerror("Username error", f"The application could not get username details\n Username selected: {username}")
	
	
	
	# test button event
	'''
	def testButtonEvent(requestText):
		writeOnText(requestText, "test")
	'''
	
	
	
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
		self.root.title("Server")
		self.root.geometry("860x510")
		self.root.protocol("WM_DELETE_WINDOW", self.exitButtonEvent)
		#root.resizable(False, False)
		
		# frames
		self.topFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.leftFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.rightFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.hostPortFrame = ttk.Frame(self.topFrame)
		self.runStopFrame = ttk.Frame(self.topFrame)
		self.usersFrame = ttk.Frame(self.leftFrame, padding = 8)
		self.requestFrame = ttk.Frame(self.rightFrame)
		
		# separators
		self.topSeparator = ttk.Separator(self.topFrame, orient = tk.VERTICAL)
		
		# host label
		self.hostLabel = ttk.Label(self.hostPortFrame, text = "Host IP:")
		
		# host entry
		self.hostEntryStringVar = tk.StringVar(self.rightFrame, value = "192.168.0.1")
		self.hostEntry = ttk.Entry(self.hostPortFrame, textvariable = self.hostEntryStringVar)
		
		# port label
		self.portLabel = ttk.Label(self.hostPortFrame, text = "Port:")
		
		# port entry
		self.portEntryStringVar = tk.StringVar(self.rightFrame, value = "32768")
		self.portEntry = ttk.Entry(self.hostPortFrame, textvariable = self.portEntryStringVar)
		
		# run stop Radiobuttons
		self.runStopBoolean = False
		self.runStopBooleanVar = tk.BooleanVar(self.runStopFrame, False)
		self.runRadiobutton = tk.Radiobutton(
			self.runStopFrame,
			text = "Run",
			variable = self.runStopBooleanVar,
			value = True,
			background = "#40c040",
			borderwidth = 2,
			relief = "groove",
			command = self.runStopRadiobuttonEvent
		)
		self.stopRadiobutton = tk.Radiobutton(
			self.runStopFrame,
			text = "Stop",
			variable = self.runStopBooleanVar,
			value = False,
			state = tk.DISABLED,
			background = "#c04040",
			borderwidth = 2,
			relief = "groove",
			command = self.runStopRadiobuttonEvent
		)
		
		# list of users
		self.userListboxStringVar = tk.StringVar(self.usersFrame)
		self.userListbox = tk.Listbox(self.usersFrame, state = tk.DISABLED, listvariable = self.userListboxStringVar)
		
		# scrollbar of the list of users
		self.userScrollbar = ttk.Scrollbar(self.usersFrame, command = self.userListbox.yview)
		self.userListbox.config(yscrollcommand = self.userScrollbar.set)
		
		# user button
		self.userButton = ttk.Button(self.leftFrame, text = "Get User's\nIP and Port", state = tk.DISABLED, command = self.userButtonEvent)
		
		# requests shown on a text widget
		self.requestText = tk.Text(self.requestFrame, state = tk.DISABLED)
		
		# scrollbar of the requests' text
		self.requestScrollbar = ttk.Scrollbar(self.requestFrame, command = self.requestText.yview)
		self.requestText.config(yscrollcommand = self.requestScrollbar.set)
		
		# test button
		'''
		testButton = ttk.Button(rightFrame, text = "Test", command = lambda: testButtonEvent(requestText))
		testButton.after(1000, lambda: writeOnText(requestText, "test"))
		'''
		
		# exit button
		self.exitButton = ttk.Button(self.rightFrame, text = "Exit", command = self.exitButtonEvent)
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# main frames
		self.topFrame.pack(side = tk.TOP, fill = tk.X)
		self.leftFrame.pack(side = tk.LEFT, fill = tk.Y)#, expand = True)
		self.rightFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		
		# top frame
		self.hostPortFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.hostLabel.grid(row = 0, column = 0, sticky = tk.W)
		self.hostEntry.grid(row = 0, column = 1, sticky = tk.E)
		self.portLabel.grid(row = 1, column = 0, sticky = tk.W)
		self.portEntry.grid(row = 1, column = 1, sticky = tk.E)
		
		self.topSeparator.pack(side = tk.LEFT, padx = 8, fill = tk.Y)
		
		self.runStopFrame.pack(side = tk.RIGHT, fill = tk.BOTH, expand = True)
		self.runRadiobutton.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		self.stopRadiobutton.pack(side = tk.BOTTOM, fill = tk.BOTH, expand = True)
		
		
		# left frame
		self.usersFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		self.userListbox.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.userScrollbar.pack(side = tk.RIGHT, fill = tk.Y)
		
		self.userButton.pack(side = tk.BOTTOM, fill = tk.X)
		
		# right frame
		self.requestFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		self.requestText.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.requestScrollbar.pack(side = tk.RIGHT, fill = tk.Y)
		
		#testButton.pack(side = tk.TOP, fill = tk.X)
		self.exitButton.pack(side = tk.BOTTOM, fill = tk.X)



# ----------------



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	server = Server()
