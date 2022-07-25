import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

#from enum import Enum
from threading import Thread, Lock
import socket
import json



'''
+---------------
| Functions
+---------------
'''
# --| recvJson |-- function
# Description: receive JSON data
# Input: a socket
# Output: a dictionary
def recvJson(conn):
	# get size and text
	size = int.from_bytes(conn.recv(2), byteorder = "little")
	arr = []
	
	x = size
	while 0 < x:
		s = min(x, 1024)
		arr.append(conn.recv(s))
		x -= 1024
	
	return json.loads(b''.join(arr))



# --| sendJson |-- function
# Description: send JSON data
# Input: a socket and a dictionary
# Output: None
def sendJson(conn, response):
	# get message size
	text = json.dumps(response, separators = (',', ':'))
	size = min(len(text), 65535)
	
	# limit the message size
	text = text[:size]
	
	# concatenate the first byte(size) with the message, and return
	arr = [size.to_bytes(2, byteorder = "little"), text.encode("utf-8")]
	conn.sendall(b''.join(arr))



'''
+---------------
| Classes
+---------------
'''
# --| CardValue |-- Enum
# Description: enumerates the card values
class CardValue:
	_4 = 0
	_5 = 1
	_6 = 2
	_7 = 3
	QUEEN = 4
	JACK = 5
	KING = 6
	ACE = 7
	_2 = 8
	_3 = 9



# --| CardSuit |-- Enum
# Description: enumerates the card suits
class CardSuit:
	DIAMONDS = 0
	SPADES = 1
	HEARTS = 2
	CLUBS = 3



# --| CardSpecial |-- Enum
# Description: enumerates the special card images
class CardSpecial:
	BACK = 0
	EMPTY = 1



# ----------------



# --| CommunicationThread |-- class
# Description: deal with the player communication
class CommunicationThread:
	# CommunicationThread constructor
	# Description: declare the class's atributes
	# Input: a Client object
	def __init__(self, client, conn):
		self.client = client
		self.conn = conn
	
	
	
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
		while(True):
			message = recvJson(self.conn)
			
			
			
			if message["type"] == "status":
				self.client.status(message)
			
			
			
			elif message["type"] == "input":
				if self.client.truco:
					Truco(self.client)
				else:
					with self.client.sharedMemoryLock:
						self.client.sharedMemory['I'] = True
			
			
			
			elif message["type"] == "vazaWinner":
				winner = message["winner"]
				teamPointName = {
					0: "Red",
					1: "Blue",
					2: "No one"
				}
				messagebox.showinfo("Game info", f'{teamPointName[winner]} won the vaza')
			
			
			
			elif message["type"] == "maoWinner":
				winner = message["winner"]
				teamPointName = {
					0: "Red",
					1: "Blue",
					2: "No one"
				}
				messagebox.showinfo("Game info", f'{teamPointName[winner]} won the mao')
			
			
			
			elif message["type"] == "error":
				messagebox.showerror("Game error", message["message"])
			
			
			
			else:
				print(message)



# ----------------



# --| Connect |-- class
# Description: deal with the player connection
class Connect:
	# Connect constructor
	# Description: declare the class's atributes, initiates the widgets, and run the window
	# Input: a Client object
	def __init__(self, client):
		self.client = client
		
		self.declareWidgets()
		self.packWidgets()
		
		client.root.withdraw()
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	def connectButtonEvent(self):
		# connect to the server
		host = self.serverEntryStringVar.get()
		port = int(self.portEntryStringVar.get())
		conn = self.client.clientSocket
		conn.connect((host, port))
		
		# send name
		message = {
			"type": "name",
			"name": self.nameEntryStringVar.get()
		}
		sendJson(conn, message)
		
		# create the communication handler
		self.client.run()
		
		# enable root and destroy this toplevel
		self.client.root.deiconify()
		self.root.destroy()
		
	
	
	
	def exitEvent(self):
		self.client.exitEvent()
	
	
	
	'''
	+---------------
	| Widgets
	+---------------
	'''
	def declareWidgets(self):
		# root
		self.root = tk.Toplevel(self.client.root)
		self.root.title("Connecting")
		self.root.iconbitmap("images/icon.ico")
		self.root.geometry("260x120")
		self.root.protocol("WM_DELETE_WINDOW", self.exitEvent)
		
		# styles
		self.style = ttk.Style()
		self.style.configure("connectButton.TButton", font = ("Arial", 12, "bold"))
		
		# frames
		self.entriesFrame = ttk.Frame(self.root)
		
		# labels
		self.nameLabel = ttk.Label(self.entriesFrame, text = "Name:", font = ("Arial", 12, "bold"), padding = 2)
		self.serverLabel = ttk.Label(self.entriesFrame, text = "Server:", font = ("Arial", 12, "bold"), padding = 2)
		self.portLabel = ttk.Label(self.entriesFrame, text = "Port:", font = ("Arial", 12, "bold"), padding = 2)
		
		# entries
		self.nameEntryStringVar = tk.StringVar(self.entriesFrame, value = "Your name here")
		self.serverEntryStringVar = tk.StringVar(self.entriesFrame, value = "26.29.6.85")
		self.portEntryStringVar = tk.StringVar(self.entriesFrame, value = "30000")
		self.nameEntry = ttk.Entry(self.entriesFrame, textvariable = self.nameEntryStringVar, font = ("Arial", 12))
		self.serverEntry = ttk.Entry(self.entriesFrame, textvariable = self.serverEntryStringVar, font = ("Arial", 12))
		self.portEntry = ttk.Entry(self.entriesFrame, textvariable = self.portEntryStringVar, font = ("Arial", 12))
		
		# connect button
		self.connectButton = ttk.Button(self.root, text = "Connect", style = "connectButton.TButton", command = self.connectButtonEvent)
		
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# main frames
		self.entriesFrame.pack(side = tk.TOP, expand = True)
		
		# labels
		self.nameLabel.grid(column = 0, row = 0, sticky = tk.W)
		self.serverLabel.grid(column = 0, row = 1, sticky = tk.W)
		self.portLabel.grid(column = 0, row = 2, sticky = tk.W)
		
		# entries
		self.nameEntry.grid(column = 1, row = 0, sticky = tk.W)
		self.serverEntry.grid(column = 1, row = 1, sticky = tk.W)
		self.portEntry.grid(column = 1, row = 2, sticky = tk.W)
		
		# buttons
		self.connectButton.pack(side = tk.TOP, fill = tk.X)



# ----------------



# --| Truco |-- class
# Description: deal with truco response
class Truco:
	# Truco constructor
	# Description: declare the class's atributes, initiates the widgets, and run the window
	# Input: a Client object
	def __init__(self, client):
		self.client = client
		
		self.declareWidgets()
		self.packWidgets()
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	def rejectButtonEvent(self):
		# send name
		message = {
			"type": "truco",
			"response": 0
		}
		sendJson(self.client.clientSocket, message)
		
		# close the window
		self.root.destroy()
	
	
	
	def acceptButtonEvent(self):
		# send name
		message = {
			"type": "truco",
			"response": 1
		}
		sendJson(self.client.clientSocket, message)
		
		# close the window
		self.root.destroy()
	
	
	
	def trucoButtonEvent(self):
		# send name
		message = {
			"type": "truco",
			"response": 2
		}
		sendJson(self.client.clientSocket, message)
		
		# close the window
		self.root.destroy()
	
	
	
	'''
	+---------------
	| Widgets
	+---------------
	'''
	def declareWidgets(self):
		# root
		self.root = tk.Toplevel(self.client.root)
		self.root.title(f'{self.client.trucoName(False)}')
		self.root.iconbitmap("images/icon.ico")
		self.root.geometry("360x150")
		
		# styles
		self.style = ttk.Style(self.root)
		self.style.configure("trucoButtons.TButton", font = ("Arial", 12, "bold"))
		
		# frames
		self.buttonsFrame = ttk.Frame(self.root)
		
		# labels
		self.trucoLabel = ttk.Label(self.root, text = f'{self.client.trucoName(False)}', font = ("Arial", 72, "bold"))
		
		# buttons
		self.rejectButton = ttk.Button(self.buttonsFrame, text = "Reject", style = "trucoButtons.TButton", command = self.rejectButtonEvent)
		self.acceptButton = ttk.Button(self.buttonsFrame, text = "Accept", style = "trucoButtons.TButton", command = self.acceptButtonEvent)
		if self.client.maoValue < 9:
			self.trucoButton = ttk.Button(
				self.buttonsFrame,
				text = f'{self.client.trucoName(True)}',
				style = "trucoButtons.TButton",
				command = self.trucoButtonEvent
			)
		
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# labels
		self.trucoLabel.pack(side = tk.TOP, expand = True)
		
		# buttons
		self.rejectButton.grid(column = 0, row = 0, sticky = tk.EW)
		self.acceptButton.grid(column = 1, row = 0, sticky = tk.EW)
		if self.client.maoValue < 9:
			self.trucoButton.grid(column = 2, row = 0, sticky = tk.EW)
		
		# main frames
		self.buttonsFrame.pack(side = tk.TOP, expand = True)



# ----------------



# --| Client |-- class
# Description: deal with window, its widgets, and the comunication with the server
class Client:
	# Client constructor
	# Description: declare the class's atributes, initiates the widgets, and run the window
	# Input: empty
	def __init__(self):
		# declare atributes
		self.username = None	# client username
		self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.truco = True
		
		# create widgets, put them on the window, and run the window
		self.declareWidgets()
		self.packWidgets()
		
		Connect(self)
		
		self.root.mainloop()
	
	

	'''
	+---------------
	| Functions
	+---------------
	'''
	# --| communicationThreadMain |-- class method
	# Description: communicationThread main function
	# Input: the client object
	# Output: empty
	def communicationThreadMain(client, conn):
		communication = CommunicationThread(client, conn)
		communication.run()
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# --| declareRequestThreads |-- method
	# Description: initiate variables for communication with the server
	# Input: empty
	# Output: empty
	def declareRequestThreads(self):
		self.sharedMemory = {'I': False}
		self.sharedMemoryLock = Lock()
	
	
	
	# --| run |-- method
	# Description: create and run the communicationThread
	# Input: empty
	# Output: empty
	def run(self):
		self.declareRequestThreads()
		
		communicationThread = Thread(target = Client.communicationThreadMain, args = (self, self.clientSocket))
		communicationThread.daemon = True
		communicationThread.start()
	
	
	
	def status(self, message):
		# memorizing the message
		self.message = message
		
		self.playerList = message["game"]["playerList"]
		self.redTeamScore = message["game"]["redTeamScore"]
		self.blueTeamScore = message["game"]["blueTeamScore"]
		
		self.maoValue = message["mao"]["value"]
		self.maoPointList = message["mao"]["pointList"]
		self.vira = message["mao"]["vira"]
		self.truco = message["mao"]["truco"]
		self.refused = message["mao"]["refused"]
		
		self.vazaPlayerNumber = message["vaza"]["playerNumber"]
		self.vazaCardList = message["vaza"]["cardList"]
		
		self.playerPosition = message["player"]["position"]
		self.playerCardList = message["player"]["cardList"]
		self.canTruco = message["player"]["canTruco"]
		
		# update widgets
		self.updateScore()
		self.updateRounds()
		self.updateTurn()
		self.updateTable()
		self.updateCards()
	
	
	# widgets updating methods
	def updateScore(self):
		self.redScoreLabel.config(text = f'Red score: {self.redTeamScore}')
		self.blueScoreLabel.config(text = f'Blue score: {self.blueTeamScore}')
	
	
	
	def updateRounds(self):
		for i in range(3):
			color = "#000000"
			
			if i < len(self.maoPointList):
				point = self.maoPointList[i]
				
				if point == 0:
					color = "#FF0000"
				elif point == 1:
					color = "#0000FF"
				elif point == 2:
					color == "#FFFFFF"
			
			self.roundLabels[i].config(foreground = color)
	
	
	
	def updateTurn(self):
		# turn label
		if self.vazaPlayerNumber == self.playerPosition:
			turnName = "Your turn!"
		else:
			playerName = self.playerList[self.vazaPlayerNumber]
			if playerName[-1] == 's':
				turnName = f"{playerName}' turn"
			else:
				turnName = f"{playerName}'s turn"
		
		self.turnLabel.config(text = turnName)
		
		# mao value
		self.maoValueLabel.config(text = f'Mao value: {self.maoValue}')
	
	
	
	def updateTable(self):
		# players
		directionColors = ("#ff8080", "#8080ff", "#ff8080", "#8080ff")
		
		for i in range(4):
			# getting vaza information
			position = (self.playerPosition + i + 1)%4
			color = directionColors[position]
			name = self.playerList[position]
			card = self.vazaCardList[position]
			
			# getting card image
			if card is None:
				cardImage = self.specialCardImages[CardSpecial.EMPTY]
			else:
				if card["hidden"]:
					cardImage = self.specialCardImages[CardSpecial.BACK]
				else:
					cardImage = self.cardImages[card["value"]][card["suit"]]
				
			# updating table widgets
			cardLabel = self.directionWidgets[i]["cardLabel"]
			usernameLabel = self.directionWidgets[i]["usernameLabel"]
			
			cardLabel.config(image = cardImage)
			usernameLabel.config(text = name, foreground = color)
		
		# getting vira image
		if self.vira is None:
			cardImage = self.specialCardImages[CardSpecial.EMPTY]
		else:
			if self.vira["hidden"]:
				cardImage = self.specialCardImages[CardSpecial.BACK]
			else:
				cardImage = self.cardImages[self.vira["value"]][self.vira["suit"]]
		
		# updating vira
		self.viraCardLabel.config(image = cardImage)
	
	
	
	def updateCards(self):
		cards = len(self.playerCardList)
		
		for i in range(3):
			card = self.cardButtons[i]
			
			if i < cards:
				serial = self.playerCardList[i]
				cardImage = self.cardImages[serial["value"]][serial["suit"]]
				cmd = lambda x: lambda: self.cardButtonEvent(x)
				
				card.config(image = cardImage)
				card.config(command = cmd(i))
				card.pack(side = tk.LEFT, expand = True)
			else:
				card.pack_forget()
	
	
	
	def trucoName(self, next):
		if next:
			if self.maoValue == 1:
				return "SEIS"
			elif self.maoValue == 3:
				return "NOVE"
			elif self.maoValue == 6:
				return "DOZE"
			elif self.maoValue ==  9:
				return "ERROR"
		else:
			if self.maoValue == 1:
				return "TRUCO"
			elif self.maoValue == 3:
				return "SEIS"
			elif self.maoValue == 6:
				return "NOVE"
			elif self.maoValue ==  9:
				return "DOZE"
	
	
	
	def loadCardImages(self):
		with open("json/cards.json") as file:
			cards = json.load(file)
		
		self.cardImages = {}
		
		values = {
			"4": CardValue._4,
			"5": CardValue._5,
			"6": CardValue._6,
			"7": CardValue._7,
			"queen": CardValue.QUEEN,
			"jack": CardValue.JACK,
			"king": CardValue.KING,
			"ace": CardValue.ACE,
			"2": CardValue._2,
			"3": CardValue._3
		}
		
		suits = {
			"_of_diamonds": CardSuit.DIAMONDS,
			"_of_spades": CardSuit.SPADES,
			"_of_hearts": CardSuit.HEARTS,
			"_of_clubs": CardSuit.CLUBS
		}
		
		for value in cards["values"]:
			cardValue = values[value]
			cardImageSuits = {}
			
			for suit in cards["suits"]:
				cardSuit = suits[suit]
				cardImageSuits[cardSuit] = tk.PhotoImage(file = f'images/cards/{value}{suit}.png')
				
			self.cardImages[cardValue] = cardImageSuits
		
		self.specialCardImages = {
			CardSpecial.BACK: tk.PhotoImage(file = "images/cards/card_back.png"),
			CardSpecial.EMPTY: tk.PhotoImage(file = "images/cards/card_empty.png")
		}
	
	
	
	'''
	+---------------
	| Widget Events
	+---------------
	'''
	def cardButtonEvent(self, cardNumber):
		if not self.truco:
			# if did not get truco, then can draw card
			with self.sharedMemoryLock:
				# but only if input requested
				if self.sharedMemory['I']:
					# send message
					message = {
						"type": "draw",
						"card": cardNumber,
						"hide": self.hideBooleanVar.get()
					}
					sendJson(self.clientSocket, message)
					self.hideBooleanVar.set(False)
					
					# wait for other input request
					self.sharedMemory['I'] = False
				
	
	
	
	def trucoButtonEvent(self):
		if not self.truco:
			# if did not get truco, then can truco
			with self.sharedMemoryLock:
				# but only if input requested
				if self.sharedMemory['I']:
					# send message
					message = {"type": "truco"}
					sendJson(self.clientSocket, message)
					
					# wait for other input request
					self.sharedMemory['I'] = False
	
	
	
	# exit event
	def exitEvent(self):
		self.root.quit()
	
	
	
	'''
	+---------------
	| Widgets
	+---------------
	'''
	def declareWidgets(self):
		# root
		self.root = tk.Tk()
		self.root.title("Trucão")
		self.root.iconbitmap("images/icon.ico")
		self.root.geometry("480x650")
		self.root.protocol("WM_DELETE_WINDOW", self.exitEvent)
		
		
		
		# style
		self.style = ttk.Style(self.root)
		self.style.configure("tableFrame.TFrame", background = "#1b521b", borderwidth = 2, relief = "groove")
		self.style.configure("cardFrame.TFrame", background = "#1b521b", borderwidth = 2)
		self.style.configure("cardLabel.Label", background = "#1b521b")
		self.style.configure("hideCheckbutton.TCheckbutton", font = ("Arial", 16, "bold"))
		self.style.configure("trucoButton.TButton", font = ("Arial", 36, "bold"))
		
		
		
		# images
		self.loadCardImages()
		
		
		
		# frames
		self.scoreFrame = ttk.Frame(self.root, padding = 2, borderwidth = 2, relief = "groove")
		self.turnFrame = ttk.Frame(self.root, padding = 2, borderwidth = 2, relief = "groove")
		self.tableFrame = ttk.Frame(self.root, style = "tableFrame.TFrame", padding = 8)
		self.panelFrame = ttk.Frame(self.root)
		self.leftPanelFrame = ttk.Frame(self.panelFrame)
		self.rightPanelFrame = ttk.Frame(self.panelFrame, padding = 4, borderwidth = 2, relief = "groove")
		self.cardsPanelFrame = ttk.Frame(self.leftPanelFrame, padding = 4, borderwidth = 2, relief = "groove")
		self.buttonPanelFrame = ttk.Frame(self.leftPanelFrame, padding = 4, borderwidth = 2, relief = "groove")
		
		
		
		# scores
		self.teamLabel = ttk.Label(self.scoreFrame, text = "Team", font = ("Arial", 12, "bold"))
		self.redTeamLabel = ttk.Label(self.scoreFrame, text = "Red", font = ("Arial", 12, "bold"), foreground = "#800000")
		self.blueTeamLabel = ttk.Label(self.scoreFrame, text = "Blue", font = ("Arial", 12, "bold"), foreground = "#000080")
		
		self.redScoreLabel = ttk.Label(self.scoreFrame, text = "", font = ("Arial", 12, "bold"), foreground = "#800000")
		self.blueScoreLabel = ttk.Label(self.scoreFrame, text = "", font = ("Arial", 12, "bold"), foreground = "#000080")
		
		self.roundLabels = []
		for _ in range(3):
			self.roundLabels.append(ttk.Label(self.scoreFrame, text = "██", font = ("Arial", 12, "bold"), foreground = "#000000"))
		
		
		
		# turn indicator and mao value
		self.turnLabel = ttk.Label(
			self.turnFrame,
			text = "",
			font = ("Arial", 16, "bold"),
			foreground = "#000000"
		)
		self.turnSeparator = ttk.Separator(self.turnFrame, orient = tk.VERTICAL)
		self.maoValueLabel = ttk.Label(
			self.turnFrame,
			text = "",
			font = ("Arial", 12, "bold"),
			foreground = "#000000",
			padding = 0
		)
		
		
		
		# cardinal directions
		#directionNames = ("East", "North", "West", "South")
		directionColors = ("#ff8080", "#8080ff", "#ff8080", "#8080ff")
		usernames = ("", "", "", "")
		
		self.directionWidgets = []
		for i in range(4):
			cardFrame = ttk.Frame(self.tableFrame, style = "cardFrame.TFrame", padding = 8)
			#directionName = directionNames[i]
			directionColor = directionColors[i]
			username = usernames[i]
			
			directionWidget = {
				"cardFrame": cardFrame,
				"cardLabel": ttk.Label(cardFrame, image = self.specialCardImages[CardSpecial.EMPTY], padding = -2),
				#"directionLabel": ttk.Label(cardFrame, style = "cardLabel.Label", text = directionName, font = ("Arial", 12, "bold"), foreground = directionColor),
				"usernameLabel": ttk.Label(cardFrame, style = "cardLabel.Label", text = username, font = ("Arial", 16), foreground = directionColor)
			}
			
			self.directionWidgets.append(directionWidget)
		
		
		
		# vira
		self.viraFrame = ttk.Frame(self.tableFrame, style = "cardFrame.TFrame", padding = 8)
		self.viraCardLabel = ttk.Label(self.viraFrame, image = self.specialCardImages[CardSpecial.EMPTY], padding = -2)
		self.viraLabel = ttk.Label(self.viraFrame, style = "cardLabel.Label", text = "Vira", font = ("Arial", 16, "bold"), foreground = "#ffffff")
		
		
		
		# panel cards
		self.cardButtons = []
		
		for i in range(3):
			cmd = lambda x: lambda: self.cardButtonEvent(x)
			self.cardButtons.append(ttk.Button(
				self.cardsPanelFrame,
				image = self.specialCardImages[CardSpecial.EMPTY],
				padding = 4,
				command = cmd(i)))
		
		
		
		# hide button
		self.hideBooleanVar = tk.BooleanVar(self.buttonPanelFrame, False)
		self.hideCheckbutton = ttk.Checkbutton(
			self.buttonPanelFrame,
			variable = self.hideBooleanVar,
			onvalue = True,
			offvalue = False,
			style = "hideCheckbutton.TCheckbutton",
			text = "Hide card",
			padding = 4
		)
		
		# truco button
		self.trucoButton = ttk.Button(
			self.rightPanelFrame,
			style = "trucoButton.TButton",
			text = "TRUCO",
			padding = 4,
			command = self.trucoButtonEvent
			)
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# frames
		self.scoreFrame.pack(side = tk.TOP, fill = tk.X)
		self.turnFrame.pack(side = tk.TOP, fill = tk.X)
		self.tableFrame.pack(side = tk.TOP, expand = True)
		self.panelFrame.pack(side = tk.BOTTOM, fill = tk.X)
		self.leftPanelFrame.pack(side = tk.LEFT)
		self.rightPanelFrame.pack(side = tk.RIGHT, fill = tk.BOTH, expand = True)
		self.cardsPanelFrame.pack(side = tk.TOP, fill = tk.X)
		self.buttonPanelFrame.pack(side = tk.BOTTOM, fill = tk.X)
		#self.canvas.pack()
		
		
		
		# scores
		self.redScoreLabel.pack(side = tk.LEFT, expand = True)
		
		for round in self.roundLabels:
			round.pack(side = tk.LEFT)
		self.blueScoreLabel.pack(side = tk.LEFT, expand = True)
		
		# turn indicator and mao value
		self.turnLabel.pack(side = tk.LEFT, expand = True)
		self.turnSeparator.pack(side = tk.LEFT, fill = tk.Y)
		self.maoValueLabel.pack(side = tk.RIGHT)
		
		
		
		# table
		directionGrid = ((2, 1, tk.E), (1, 0, tk.N), (0, 1, tk.W), (1, 2, tk.S))
		
		for i in range(4):
			column, row, direction = directionGrid[i]
			directionWidget = self.directionWidgets[i]
			directionWidget["cardFrame"].grid(column = column, row = row, sticky = direction)
			#directionWidget["directionLabel"].pack()
			directionWidget["usernameLabel"].pack()
			directionWidget["cardLabel"].pack()
		
		self.viraFrame.grid(column = 1, row = 1)
		self.viraLabel.pack()
		self.viraCardLabel.pack()
		
		
		
		# panel cards
		for cardButton in self.cardButtons:
			cardButton.pack(side = tk.LEFT, expand = True)
		#self.cardButtons[2].pack_forget()
		#self.cardButtons[1].pack_forget()
		
		self.hideCheckbutton.pack(side = tk.TOP, expand = True)
		self.trucoButton.pack(side = tk.TOP, fill = tk.BOTH, expand = True)



# ----------------



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	client = Client()
