import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from enum import Enum
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
class CardValue(Enum):
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
class CardSuit(Enum):
	DIAMONDS = 0
	SPADES = 1
	HEARTS = 2
	CLUBS = 3



# --| CardSpecial |-- Enum
# Description: enumerates the special card images
class CardSpecial(Enum):
	BACK = 0
	EMPTY = 1



# --| Client |-- class
# Description: deal with window, its widgets, and the comunication with the server
class Client:
	# Client constructor
	# Description: declare the class's atributes, initiates the widgets, and run the window
	# Input: empty
	def __init__(self):
		# declare atributes
		self.username = None	# client username
		
		self.host = None		# server ip
		self.hostPort = None	# server port
		
		self.clientSocket = None
		
		# create widgets, put them on the window, and run the window
		self.declareWidgets()
		self.packWidgets()
		
		self.root.mainloop()
	
	

	'''
	+---------------
	| Functions
	+---------------
	'''
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
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
		self.root.geometry("480x660")
		self.root.protocol("WM_DELETE_WINDOW", self.exitEvent)
		
		
		
		# style
		self.style = ttk.Style()
		self.style.configure("tableFrame.TFrame", background = "#1b521b", borderwidth = 2, relief = "groove")
		self.style.configure("cardFrame.TFrame", background = "#1b521b", borderwidth = 2)
		self.style.configure("cardLabel.Label", background = "#1b521b")
		self.style.configure("hideCheckbutton.TCheckbutton", font = ("Arial", 16, "bold"))
		self.style.configure("trucoButton.TButton", font = ("Arial", 36, "bold"))
		
		
		
		# images
		self.loadCardImages()
		
		
		
		# frames
		self.scoreFrame = ttk.Frame(self.root, padding = 8, borderwidth = 2, relief = "groove")
		self.tableFrame = ttk.Frame(self.root, style = "tableFrame.TFrame", padding = 8)
		self.panelFrame = ttk.Frame(self.root)
		self.leftPanelFrame = ttk.Frame(self.panelFrame)
		self.rightPanelFrame = ttk.Frame(self.panelFrame, padding = 8, borderwidth = 2, relief = "groove")
		self.cardsPanelFrame = ttk.Frame(self.leftPanelFrame, padding = 8, borderwidth = 2, relief = "groove")
		self.buttonPanelFrame = ttk.Frame(self.leftPanelFrame, padding = 8, borderwidth = 2, relief = "groove")
		
		
		
		# scores
		self.redScoreLabel = ttk.Label(self.scoreFrame, text = "Red team score: 0", font = ("Arial", 12, "bold"), foreground = "#800000")
		self.blueScoreLabel = ttk.Label(self.scoreFrame, text = "Blue team score: 0", font = ("Arial", 12, "bold"), foreground = "#000080")
		
		
		
		# cardinal directions
		#directionNames = ("East", "North", "West", "South")
		directionColors = ("#ff8080", "#8080ff", "#ff8080", "#8080ff")
		usernames = ("Arrombadilson", "Melacudêncio", "Fodecincollier", "Prolapsademir")
		
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
		
		for _ in range(3):
			self.cardButtons.append(ttk.Button(self.cardsPanelFrame, image = self.specialCardImages[CardSpecial.EMPTY], padding = 4))
		
		
		
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
		self.trucoButton = ttk.Button(self.rightPanelFrame, style = "trucoButton.TButton", text = "TRUCO", padding = 4)
	
	
	
	'''
	+---------------
	| Packing
	+---------------
	'''
	def packWidgets(self):
		# frames
		self.scoreFrame.pack(side = tk.TOP, fill = tk.X)
		self.tableFrame.pack(side = tk.TOP, expand = True)
		self.panelFrame.pack(side = tk.BOTTOM, fill = tk.X)
		self.leftPanelFrame.pack(side = tk.LEFT)
		self.rightPanelFrame.pack(side = tk.RIGHT, fill = tk.BOTH, expand = True)
		self.cardsPanelFrame.pack(side = tk.TOP, fill = tk.X)
		self.buttonPanelFrame.pack(side = tk.BOTTOM, fill = tk.X)
		#self.canvas.pack()
		
		
		
		# scores
		self.redScoreLabel.pack(side = tk.LEFT, expand = True)
		self.blueScoreLabel.pack(side = tk.RIGHT, expand = True)
		
		
		
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
			cardButton.pack(side = tk.LEFT)
		
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
