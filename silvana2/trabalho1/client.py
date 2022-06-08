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



class Client:
	def __init__(self):
		self.username = None
		self.host = None
		self.port = None
		
		self.declareWidgets()
		self.packWidgets()
		
		self.root.mainloop()
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# declare username, host, and port from their entries
	def declareUsernameHostPort(self):
		self.username = self.usernameEntryStringVar.get()
		self.host = self.hostEntryStringVar.get()
		self.port = int(self.portEntryStringVar.get())
	
	
	
	# try to log in
	def login(self):
		request = {
			"operacao": "login",
			"username": self.username,
			"porta": self.port
		}
		
		data = jsonToData(request)
		print(data)
		
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((self.host, self.port))
			s.sendall(data)
			
			# get size and text
			size = int.from_bytes(s.recv(1), byteorder = "little")
			text = s.recv(size - 1).decode("utf-8")
		
		print(text)
	
	
	
	# test function
	def testMessage(self):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((self.host, self.port))
			s.sendall("bacalhau".encode("utf-8"))
			data = s.recv(1024)
		
		print(data.decode("utf-8"))
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	# display users button event
	def displayUsersButtonEvent(self):
		self.userListboxStringVar.set([f"random {i + 1}" for i in range(100)])
	
	
	
	def loginLogoffRadiobuttonEvent(self):
		b1 = self.loginLogoffBoolean
		b2 = self.loginLogoffBooleanVar.get()
		
		if ((not b1) and b2) or (b1 and (not b2)):
			if b2:
				try:
					self.declareUsernameHostPort()
					self.login()
					messagebox.showinfo("Message", f"Logging in as {self.usernameEntryStringVar.get()}!")
				except BaseException as e:
					messagebox.showinfo("Message", f"Fail to log in!\n{self.usernameEntryStringVar.get()}")
					self.loginLogoffBooleanVar.set(False)
				#self.testMessage()
			else:
				messagebox.showinfo("Message", "Logging off!")
		
		self.loginLogoffBoolean = b2
	
	
	
	# chat button event
	def chatButtonEvent(self):
		#print("Chatting!")
		messagebox.showinfo("Message", f"Chatting with {self.userListbox.get(tk.ANCHOR)}!")
	
	
	
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
		#root.resizable(False, False)
		
		# frames
		self.leftFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.rightFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.usersFrame = ttk.Frame(self.leftFrame, padding = 8)
		self.usernameHostPortFrame = ttk.Frame(self.rightFrame, padding = 8, borderwidth = 2, relief = "groove")
		self.loginLogoffFrame = ttk.Frame(self.rightFrame, padding = 8, borderwidth = 2, relief = "groove")
		
		# list of users
		self.userListboxStringVar = tk.StringVar(self.usersFrame)
		self.userListbox = tk.Listbox(self.usersFrame, listvariable = self.userListboxStringVar)
		
		# scrollbar of the list of users
		self.userScrollbar = ttk.Scrollbar(self.usersFrame, command = self.userListbox.yview)
		self.userListbox.config(yscrollcommand = self.userScrollbar.set)
		
		# display users button
		self.displayUsersButton = ttk.Button(self.leftFrame, text = "Display Users", command = self.displayUsersButtonEvent)
		
		# username label
		self.usernameLabel = ttk.Label(self.usernameHostPortFrame, text = "Username:")
		
		# username entry
		self.usernameEntryStringVar = tk.StringVar(self.usernameHostPortFrame, value = "Nata da Nata")
		self.usernameEntry = ttk.Entry(self.usernameHostPortFrame, textvariable = self.usernameEntryStringVar)
		
		# host label
		self.hostLabel = ttk.Label(self.usernameHostPortFrame, text = "Host IP:")

		# host entry
		self.hostEntryStringVar = tk.StringVar(self.rightFrame, value = "192.168.0.1")
		self.hostEntry = ttk.Entry(self.usernameHostPortFrame, textvariable = self.hostEntryStringVar)

		# port label
		self.portLabel = ttk.Label(self.usernameHostPortFrame, text = "Port:")

		# port entry
		self.portEntryStringVar = tk.StringVar(self.rightFrame, value = "32768")
		self.portEntry = ttk.Entry(self.usernameHostPortFrame, textvariable = self.portEntryStringVar)
		
		# separators
		#self.rightSeparator = ttk.Separator(self.usernameHostPortFrame, orient = tk.HORIZONTAL)
		
		# login logoff Radiobuttons
		self.loginLogoffBoolean = False
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
			background = "#c04040",
			borderwidth = 2,
			relief = "groove",
			command = self.loginLogoffRadiobuttonEvent
		)
		
		# chat button
		self.chatButton = ttk.Button(self.rightFrame, text = "Chat!", command = self.chatButtonEvent)
		
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
		self.usernameHostPortFrame.pack(side = tk.TOP, fill = tk.BOTH)
		self.usernameLabel.grid(row = 0, column = 0, sticky = tk.W)
		self.usernameEntry.grid(row = 0, column = 1, sticky = tk.E)
		self.hostLabel.grid(row = 1, column = 0, sticky = tk.W)
		self.hostEntry.grid(row = 1, column = 1, sticky = tk.E)
		self.portLabel.grid(row = 2, column = 0, sticky = tk.W)
		self.portEntry.grid(row = 2, column = 1, sticky = tk.E)
		#self.rightSeparator.grid(row = 3, column = 0, columnspan = 2, pady = 8, sticky = tk.EW)
		
		self.loginLogoffFrame.pack(side = tk.TOP, fill = tk.X)
		self.loginRadiobutton.pack(side = tk.LEFT, fill = tk.X, expand = True)
		self.logoffRadiobutton.pack(side = tk.RIGHT, fill = tk.X, expand = True)
		
		self.chatButton.pack(side = tk.TOP, fill = tk.X, expand = True)
		
		self.exitButton.pack(side = tk.BOTTOM, fill = tk.X)



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	client = Client()
