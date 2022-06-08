import socket
from threading import Thread, Lock
from queue import Queue
import json

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox



'''
+---------------
| Functions
+---------------
'''
# convert JSON response to data
def jsonToData(response):
	# get message size
	text = json.dumps(response)
	size = min(len(text), 255)
	
	# limit the message size
	text = text[:size]
	
	# concatenate the first byte(size) with the message, and return
	arr = [size.to_bytes(1, byteorder = "little"), text.encode("utf-8")]
	return b''.join(arr)



'''
+---------------
| Classes
+---------------
'''
class RequestThread:
	def __init__(self, server):
		self.server = server
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	def run(self):
		try:
			self.doRequest()
		except BaseException as e:
			print(f"Request accepting error: {str(e)}")
	
	
	
	# receive, process the request, and send a response
	def doRequest(self):
		# do connection
		conn, address = self.server.serverSocket.accept()
		
		# get size and text
		size = int.from_bytes(conn.recv(1), byteorder = "little")
		text = conn.recv(size).decode("utf-8")
		
		print(text)
		
		# convert into JSON and produce a JSON response
		try:
			request = json.loads(text)				# load the JSON request
			response = self.doResponse(request)		# produce a JSON response
			data = jsonToData(response)	# convert it into bytes
		except BaseException as e:
			print(f"JSON loading error: {e}")				# show error
			data = (1).to_bytes(1, byteorder = "little")	# data is x00
		
		# send the response data and close conection
		conn.sendall(data)
		conn.close()
		
	
	
	
	# write a response based on the given request
	def doResponse(self, request):
		with self.server.sharedMemoryLock:
			userToPort = self.server.sharedMemory['U']
			requestsQueue = self.server.sharedMemory['R']
			
			response = None
			
			if request["operacao"] == "login":
				response = RequestThread.login(request, userToPort)
			elif request["operacao"] == "logoff":
				response = RequestThread.logoff(request, userToPort)
			elif request["operacao"] == "get_lista":
				response = RequestThread.getList(userToPort)
			
			requestsQueue.put(response)
			return response
	
	
	
	def login(request, userToPort):
		response = {"operacao": "login"}
		
		user = request["username"]
		port = request["porta"]
		
		if user in userToPort:
			response["status"] = 400
			response["mensagem"] = "Username em Uso"
		else:
			response["status"] = 200
			response["mensagem"] = "Login com sucesso"
			
			userToPort[user] = port
		
		return response
			
			
	
	def logoff(request, userToPort):
		try:
			user = request["username"]
			del userToPort[user]
			
			return {"operacao": "logoff", "status": 200, "mensagem": "Logoff com sucesso"}
		except:
			return {"operacao": "get_lista", "status": 400, "mensagem": "Erro no Logoff"}
	
	
	
	def getList(userToPort):
		try:
			return {"operacao": "get_lista", "status": 200, "clientes": userToPort}
		except:
			return {"operacao": "get_lista", "status": 400, "mensagem": "Erro ao obter a lista"}



class Server:
	def __init__(self):
		self.host = None
		self.port = None
		self.serverSocket = None
		
		self.declareRequestThreads()
		
		self.declareWidgets()
		self.packWidgets()
		
		self.test()
		
		self.root.mainloop()
	
	
	
	# initiate variables for request handling
	def declareRequestThreads(self):
		self.sharedMemory = {
			'U': {},
			'R': Queue()
		}
		self.sharedMemoryLock = Lock()
	
	
	
	'''
	+---------------
	| Functions
	+---------------
	'''
	# requestThread main function
	def requestThreadMain(server):
		request = RequestThread(server)
		
		while server.runStopBooleanVar.get():
			request.run()
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# binding the server
	def bind(self):
		self.host = self.hostEntryStringVar.get()
		self.port = int(self.portEntryStringVar.get())
		
		self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		self.serverSocket.bind((self.host, self.port))
		self.serverSocket.listen(5)
		self.serverSocket.setblocking(True)
	
	# run the server and the GUI polling
	def run(self):
		requestThread = Thread(target = Server.requestThreadMain, args = (self,))
		requestThread.daemon = True
		requestThread.start()
		
		self.requestText.after(1000, self.requestTextAfter)
	
	# stop the server
	def stop(self):
		self.runStopBooleanVar.set(False)
		if self.serverSocket is not None:
			self.serverSocket.close()
	
	
	
	# GUI polling
	def requestTextAfter(self):
		self.gui()
		if self.runStopBooleanVar.get():
			self.root.after(1000, self.requestTextAfter)
	
	# update the GUI
	def gui(self):
		self.writeOnText("text by server class")
	
	
	
	# write on text
	def writeOnText(self, string):
		self.requestText.config(state = tk.NORMAL)
		if 1 < len(self.requestText.get(1.0, tk.END)):
			self.requestText.insert(tk.END, "\n")
		self.requestText.insert(tk.END, string)
		self.requestText.config(state = tk.DISABLED)
	
	
	
	# test
	def test(self):
		req = RequestThread(self)
		
		request1 = {"operacao": "login", "username": "luanzinho32", "porta": 5000}
		request2 = {"operacao": "logoff", "username": "luanzinho32"}
		request3 = {"operacao": "get_lista"}
		
		req.doResponse(request1)
		req.doResponse(request2)
		req.doResponse(request3)
		
		with self.sharedMemoryLock:
			users = self.sharedMemory['U']
			queue = self.sharedMemory['R']
			
			while not queue.empty():
				print(f"response: {queue.get()}")
			
			print(f"usuários: {users}")
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	# run and stop radiobuttons event
	def runStopRadiobuttonEvent(self):
		b1 = self.runStopBoolean
		b2 = self.runStopBooleanVar.get()
		
		if ((not b1) and b2) or (b1 and (not b2)):
			if b2:
				try:
					self.bind()
					self.run()
					messagebox.showinfo("Message", "Server running!")
				except BaseException as e:
					messagebox.showinfo("Message", f"Error during server running!\n{str(e)}")
					self.runStopBooleanVar.set(False)
					return
			else:
				try:
					self.stop()
					messagebox.showinfo("Message", "Server stopped!")
				except BaseException as e:
					messagebox.showinfo("Message", f"Error during server stopping!\n{str(e)}")
					self.runStopBooleanVar.set(True)
		
		self.runStopBoolean = b2
	
	
	
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
		self.root.geometry("850x510")
		self.root.protocol("WM_DELETE_WINDOW", self.exitButtonEvent)
		#root.resizable(False, False)
		
		# frames
		self.topFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.leftFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.rightFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.hostPortFrame = ttk.Frame(self.topFrame)
		self.runStopFrame = ttk.Frame(self.topFrame)
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
			background = "#c04040",
			borderwidth = 2,
			relief = "groove",
			command = self.runStopRadiobuttonEvent
		)
		
		# list of users
		self.userListStringVar = tk.StringVar(self.leftFrame)
		self.userListBox = tk.Listbox(self.leftFrame, listvariable = self.userListStringVar)
		
		# scrollbar of the list of users
		self.userScrollbar = ttk.Scrollbar(self.leftFrame, command = self.userListBox.yview)
		self.userListBox.config(yscrollcommand = self.userScrollbar.set)
		
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
		self.userListBox.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.userScrollbar.pack(side = tk.RIGHT, fill = tk.Y)
		
		# right frame
		self.requestFrame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)
		self.requestText.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
		self.requestScrollbar.pack(side = tk.RIGHT, fill = tk.Y)
		
		#testButton.pack(side = tk.TOP, fill = tk.X)
		self.exitButton.pack(side = tk.BOTTOM, fill = tk.X)



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	server = Server()