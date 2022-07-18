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



# ----------------



'''
+---------------
| Classes
+---------------
'''
# --| Team |-- Enum
# Description: enumerates the teams' pointuation
class TeamPoint(Enum):
	RED = 0
	BLUE = 1
	DRAW = 2



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



# --| Play |-- Enum
# Description: enumerates the types of what a player can do
class Play(Enum):
	CARD = 0
	HIDE = 1
	TRUCO = 2



class Card:
	def __init__(self, value, suit, isManilha):
		self.value = value
		self.suit = suit
		self.isManilha = isManilha
	
	
	
	def number(self):
		return 10 + self.suit if self.isManilha else self.value
	
	
	
	def __lt__(self, other):
		return 



# --| Deck |-- Class
# Description: the cards' deck
class Deck:
	def __init__(self):
		pass
	
	
	
	def takeCard(self):
		pass



# --| Player |-- Class
# Description: the player's data structure
class Player:
	def __init__(self, team):
		self.team = team



# --| Truco |-- Class
# Description: class where the whole game will be running
class Truco:
	def __init__(self):
		self.resetGame()
	
	
	
	def resetGame(self):
		# players
		self.playerList = []
		
		# game status
		self.redTeamPoints = 0
		self.blueTeamPoints = 0
		
		# mao status
		self.maoValue = 0
		self.vira = None
		self.shufflerNumber = 0
	
	
	
	def resetMao(self):
		self.maoValue = 1
		self.vira = 0
	
	
	
	def resetVara(self):
		self.firstPlayerNumber = 0
		self.cardsOnBoard = [None, None, None, None]
	
	
	
	def mao(self):
		self.resetMao()
		shuffler = self.playerList[self.shufflerNumber]
		
		vaza1 = self.vaza(False)
		# refused truco
		if self.refused:
			return vaza1
		
		
		# points cases
		if vaza1 == TeamPoint.DRAW:
			# 1 draw
			vaza2 = self.vaza(False)
			# refused truco
			if self.refused:
				return vaza2
			
			if vaza2 == TeamPoint.DRAW:
				# 2 draws
				vaza3 = self.vaza(False)
				# refused truco
				if self.refused:
					return vaza3
				
				if vaza3 == TeamPoint.DRAW:
					# 5º case: 3 draws
					return shuffler.team
				else:
					# 4º case: 2 draws, 1 win
					return vaza3
			else:
				# 1º case: 1 draw, 1 win
				return vaza2
		else:
			# 1 win
			vaza2 = self.vaza(True)
			# refused truco
			if self.refused:
				return vaza2
			
			if (
				vaza1 == TeamPoint.RED and vaza2 == TeamPoint.BLUE or
				vaza1 == TeamPoint.BLUE and vaza2 == TeamPoint.RED
			):
				# 1 win, 1 lose
				vaza3 = self.vaza(True)
				# refused truco
				if self.refused:
					return vaza3
				
				if vaza3 == TeamPoint.DRAW:
					# 1 win, 1 lose, 1 draw
					return vaza1
				else:
					# 1 win, 1 lose, 1 win
					return vaza3
			else:
				return vaza1
	
	
	
	def vaza(self, hideAllowed):
		point = TeamPoint.DRAW						# point of the vaza to be returned
		highestCard = None							# highest card of the vaza
		bestPlayerNumber = self.firstPlayerNumber	# the array position of the player that has drawn the best card
		
		
		
		# 4 turns
		for i in range(4):
			# getting the player info
			currentPlayerNumber = (i + self.firstPlayerNumber)%4
			currentPlayer = self.playerList[currentPlayerNumber]
			
			# play of the player
			play = currentPlayer.play()
			
			if play == Play.CARD
			
			# defining the highest card and its player
			if highestCard is None:
				# first player
				bestPlayerNumber = currentPlayerNumber
				highestCard = card
				point = currentPlayer.team
			else:
				# card not lower
				if highestCard <= card:
					bestPlayerNumber = currentPlayerNumber
					
					if highestCard == card:
						# same card value
						point = TeamPoint.DRAW
					else:
						# higher card
						point = currentPlayer.team
						highestCard = card
		
		
		
		# 
	
	
	
	'''
	+---------------
	| Test Section
	+---------------
	'''
	'''def vaza(self, hideAllowed):
		test = {
			"red": TeamPoint.RED,
			"blue": TeamPoint.BLUE,
			"draw":  TeamPoint.DRAW
		}
		return test[input()]'''



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	'''
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.bind(("localhost", 30000))
		s.listen(5)
		
		conn, addr = s.accept()
		
		with conn:
			dictTest = recvJson(conn)
			dictTest["boa"] = 666
			dictTest["arrombado"] = 13
			print(dictTest)
			sendJson(conn, dictTest)
	'''
	trucao = Truco()
	while(True):
		'''
		printDict = {
			TeamPoint.RED: "red wins",
			TeamPoint.BLUE: "blue wins"
		}
		test = {
			"red": TeamPoint.RED,
			"blue": TeamPoint.BLUE
		}
		
		team = test[input()]
		shuffler = Player(team)
		
		winnerTeam = trucao.mao()
		
		print(printDict[winnerTeam])
		'''
