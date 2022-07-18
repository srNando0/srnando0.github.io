from enum import Enum

import random
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



class Card:
	def __init__(self, game, value, suit):
		self.game = game
		self.value = value
		self.suit = suit
	
	
	
	def number(self):
		manilhaValue = (self.game.mao.vira.value + 1)%10
		return 10 + self.suit if self.value == manilhaValue else self.value
	
	
	
	def __lt__(self, other):
		return self.number() < other.number()
	
	def __gt__(self, other):
		return self.number() > other.number()
	
	def __le__(self, other):
		return self.number() <= other.number()
	
	def __ge__(self, other):
		return self.number() >= other.number()
	
	def __eq__(self, other):
		return self.number() == other.number()
	
	def __ne__(self, other):
		return self.number() != other.number()



# --| Deck |-- Class
# Description: the cards' deck
class Deck:
	def __init__(self, game):
		self.game = game
		self.cardList = [Card(game, v, s) for s in range(4) for v in range(10)]
	
	
	
	def shuffle(self):
		self.cardNumber = 0
		random.shuffle(self.cardList)
	
	
	
	def takeCard(self):
		card = self.cardList[self.cardNumber]
		self.cardNumber += 1
		
		return card



# ----------------



# --| Player |-- Class
# Description: the player's data structure
class Player:
	def __init__(self, game, team):
		self.game = game
		self.team = team
	
	
	
	def getCards(self):
		deck = self.game.deck
		
		self.cards = set()
		for _ in range(3):
			self.cards.add(deck.takeCard())
	
	
	
	def play():
		# test
		x = json.dumps(input())



# ----------------



# --| Vaza |-- Class
# Description: Vaza of mao
class Vaza:
	def __init__(self, game, firstPlayerNumber):
		self.game = game
		self.firstPlayerNumber = firstPlayerNumber
		
		self.canHide = False
		self.refused = False
		
		self.cardList = [None, None, None, None]
	
	
	
	def start(self):
		self.bestPlayerNumber = self.firstPlayerNumber
		self.highestCard = None
		self.result = TeamPoint.DRAW
	
	
	
	def updateResult(self, playerNumber, player):
		# defining the highest card and its player
		if self.highestCard is None:
			# first player
			self.bestPlayerNumber = playerNumber
			self.highestCard = player.card
			self.result = player.team
		elif self.highestCard <= player.card:
			# card not lower
			self.bestPlayerNumber = playerNumber
			
			if self.highestCard == player.card:
				# same card value
				self.result = TeamPoint.DRAW
			else:
				# higher card
				self.highestCard = player.card
				self.result = player.team
	
	
	
	def execute(self):
		# reset variables
		self.start()
		
		# 4 turns
		for i in range(Game.MAXIMUM_PLAYERS):
			# getting the player info
			playerNumber = (i + self.firstPlayerNumber)%Game.MAXIMUM_PLAYERS
			player = self.game.playerList[playerNumber]
			
			# play of the player
			player.play()
			
			'''
			if player.truco:
				# To do
				# response = self.game.trucoResponse(currentPlayer.team)
				pass
			'''
			
			# get the drawn card
			self.cardList[playerNumber] = player.card
			
			# getting the vaza highest card and its player
			self.updateResult(playerNumber, player)
		
		# set the first player to play in the next vaza
		self.firstPlayerNumber = self.bestPlayerNumber
		
		# return the result of the vaza
		return self.result
		
		
		
		



# ----------------
		


# --| Mao |-- Class
# Description: mao of truco
class Mao:
	def __init__(self, game):
		self.game = game
		
		self.value = 1
		self.vira = None
		self.result = self.execute()
	
	
	
	# executes the mao
	def execute(self):
		# shuffling the deck and distributing cards
		deck = self.game.deck
		deck.shuffle()
		
		
		playerList = self.game.playerList
		for player in playerList:
			player.getCards()
		
		self.vira = deck.takeCard()
		
		
		
		# creating the vaza
		firstPlayerNumber = (self.game.shufflerNumber + 1)%Game.MAXIMUM_PLAYERS
		self.vaza = Vaza(self.game, firstPlayerNumber)
		
		
		# ----------------
		# start of the mao
		# ----------------
		vaza1 = self.vaza.execute()
		
		# refused truco
		if self.vaza.refused:
			return vaza1
		
		
		# points cases
		if vaza1 == TeamPoint.DRAW:
			# ----------------
			# 1 draw
			# ----------------
			vaza2 = self.vaza.execute()
			
			# refused truco
			if self.vaza.refused:
				return vaza2
			
			if vaza2 == TeamPoint.DRAW:
				# ----------------
				# 2 draws
				# ----------------
				vaza3 = self.vaza.execute()
				
				# refused truco
				if self.vaza.refused:
					return vaza3
				
				if vaza3 == TeamPoint.DRAW:
					# ----------------
					# 5º case: 3 draws
					# ----------------
					shufflerPlayer = Game.playerList[Game.shufflerNumber]
					return shufflerPlayer.team
				else:
					# ----------------
					# 4º case: 2 draws, 1 win
					# ----------------
					return vaza3
			else:
				# ----------------
				# 1º case: 1 draw, 1 win
				# ----------------
				return vaza2
		else:
			# ----------------
			# 1 win
			# ----------------
			self.vaza.canHide = True
			vaza2 = self.vaza.execute()
			
			# refused truco
			if self.vaza.refused:
				return vaza2
			
			if (
				vaza1 == TeamPoint.RED and vaza2 == TeamPoint.BLUE or
				vaza1 == TeamPoint.BLUE and vaza2 == TeamPoint.RED
			):
				# ----------------
				# 1 win, 1 lose
				# ----------------
				vaza3 = self.vaza.execute()
				
				# refused truco
				if self.vaza.refused:
					return vaza3
				
				if vaza3 == TeamPoint.DRAW:
					# ----------------
					# 3º case: 1 win, 1 lose, 1 draw
					# ----------------
					return vaza1
				else:
					# ----------------
					# 1 win, 1 lose, 1 win
					# ----------------
					return vaza3
			else:
				# ----------------
				# 2º case: 2 wins or 1 win, 1 draw
				# ----------------
				return vaza1



# ----------------



# --| Game |-- Class
# Description: class where the whole game will be running
class Game:
	# constants
	MAXIMUM_PLAYERS = 4
	MAXIMUM_SCORE = 12
	
	def __init__(self):
		# players
		self.playerList = []
		self.shufflerNumber = random.randint(0, 3)
		self.deck = Deck()
		
		# game status
		self.redTeamScore = 0
		self.blueTeamScore = 0
		
		# mao
		self.mao = None
	
	
	
	def startGame(self):
		self.connectPlayers()
		
		# start things up
		self.redTeamScore = 0
		self.blueTeamScore = 0
		self.shufflerNumber = random.randint(0, 3)
		
		# do the maos
		while self.redTeamScore < Game.MAXIMUM_SCORE and self.blueTeamScore < Game.MAXIMUM_SCORE:
			self.mao = Mao(self)
			
			if self.mao.result == TeamPoint.RED:
				self.redTeamScore += self.mao.points
			elif self.mao.result == TeamPoint.BLUE:
				self.blueTeamScore += self.mao.points
			
	
	
	
	def connectPlayers():
		pass
	'''
	def resetGame(self):
		# players
		self.playerList = []
		self.shufflerNumber = 0
		
		# game status
		self.redTeamPoints = 0
		self.blueTeamPoints = 0
		
		# mao
		self.currentMao = None
	'''	
	
	
	
	'''
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
		'''
		
		
		
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
	trucao = Game()
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
