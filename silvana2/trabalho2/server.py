from enum import Enum

import random
import time

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
def sendJson(conn, message):
	# get message size
	text = json.dumps(message, separators = (',', ':'))
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
class TeamPoint:
	RED = 0
	BLUE = 1
	DRAW = 2



# --| Team |-- Enum
# Description: enumerates the teams' pointuation
class TrucoResponse:
	REFUSE = 0
	ACCEPT = 1
	TRUCO = 2



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



# ----------------



class Card:
	def __init__(self, game, value, suit):
		self.game = game
		self.value = value
		self.suit = suit
		self.hidden = False
	
	
	
	def maoValue(self):
		if self.hidden:
			return 0
		manilhaValue = (self.game.mao.vira.value + 1)%10
		return 1 + (10 + self.suit if self.value == manilhaValue else self.value)
	
	
	
	def hide(self):
		self.hidden = True
	
	
	
	def serialize(self):
		if self.hidden:
			return {
				"hidden": True
			}
		else:
			return {
				"value": self.value,
				"suit": self.suit,
				"hidden": False
			}
	
	
	
	def print(self):
		if self.hidden:
			return '🂠'
		
		valueString = {
			0: '4',
			1: '5',
			2: '6',
			3: '7',
			4: 'Q',
			5: 'J',
			6: 'K',
			7: 'A',
			8: '2',
			9: '3'
		}
		suitString = {
			0: '♦',
			1: '♠',
			2: '♥',
			3: '♣'
		}
		return valueString[self.value] + suitString[self.suit]
	
	
	
	def deserialize(self, serial):
		if serial["hidden"]:
			self.hidden = True
		else:
			self.value = serial["value"]
			self.suit = serial["suit"]
	
	
	
	def __lt__(self, other):
		return self.maoValue() < other.maoValue()
	
	def __gt__(self, other):
		return self.maoValue() > other.maoValue()
	
	def __le__(self, other):
		return self.maoValue() <= other.maoValue()
	
	def __ge__(self, other):
		return self.maoValue() >= other.maoValue()
	
	def __eq__(self, other):
		return self.maoValue() == other.maoValue()
	
	def __ne__(self, other):
		return self.maoValue() != other.maoValue()



# ----------------



# --| Deck |-- Class
# Description: the cards' deck
class Deck:
	def __init__(self, game):
		self.game = game
		self.cardList = [Card(game, v, s) for s in range(4) for v in range(10)]
	
	
	
	def shuffle(self):
		self.cardNumber = 0
		random.seed(time.time())
		random.shuffle(self.cardList)
	
	
	
	def takeCard(self):
		card = self.cardList[self.cardNumber]
		self.cardNumber += 1
		
		return Card(self.game, card.value, card.suit)



# ----------------



# --| Player |-- Class
# Description: the player's data structure
class Player:
	def __init__(self, game, name, conn, addr):
		self.game = game
		self.name = name
		self.conn = conn
		self.addr = addr
		
		self.position = 0
	
	
	
	def getCards(self):
		deck = self.game.deck
		self.cardList = [deck.takeCard() for _ in range(3)]
	
	
	
	def team(self):
		if self.position%2 == 0:
			return TeamPoint.RED
		else:
			return TeamPoint.BLUE
	
	
	
	def drawCard(self, position):
		self.card = self.cardList.pop(position)
	
	
	
	def play(self):
		# sending the current state of the game (not necessary)
		# self.sendGameState()
		
		response = self.getInput()
		
		# check if can call truco
		while response["type"] == "truco" and not self.canTruco():
			sendJson(self.conn, {"type": "error", "message": "your team cannot call truco! do something else!"})
			response = self.getInput()
		
		# truco case
		if response["type"] == "truco":
			mao = self.game.mao
			
			# do truco
			mao.truco = True
			mao.trucoTurn = Mao.otherTeam(self.team())
			self.game.send()
			self.game.trucoResponse()
			
			# refuse case
			if mao.refused:
				return
			
			# accept case
			response = self.getInput()
			
			while response["type"] == "truco" and not self.canTruco():
				sendJson(self.conn, {"type": "error", "message": "your team cannot call truco! do something else!"})
				response = self.getInput()
		
		self.drawCard(response["card"])
		self.hide = True if response["hide"] else False
	
	
	
	def trucoResponse(self):
		response = self.getInput()
		
		while response["type"] != "truco":
			sendJson(self.conn, {"type": "error", "message": "incorrect type!"})
			response = self.getInput()
		
		return max(TrucoResponse.REFUSE, min(response["response"], TrucoResponse.TRUCO))
	
	
	
	def canTruco(self):
		mao = self.game.mao
		return True if mao.value < 12 and (mao.trucoTurn == TeamPoint.DRAW or mao.trucoTurn == self.team()) else False
	
	
	
	'''
	+---------------
	| Send Methods
	+---------------
	'''
	def sendStatus(self):
		game = self.game
		mao = game.mao
		vaza = mao.vaza
		
		vazaCardList = [card.serialize() if card is not None else None for card in vaza.cardList]
		playerCardList = [card.serialize() if card is not None else None for card in self.cardList]
		
		message = {
			"type": "status",
			
			"game": {
				"playerList": [player.name for player in self.game.playerList],
				"redTeamScore": game.redTeamScore,
				"blueTeamScore": game.blueTeamScore
			},

			"mao": {
				"value": mao.value,
				"pointList": mao.pointList,
				"vira": mao.vira.serialize(),
				"truco": mao.truco,
				"refused": mao.refused
			},

			"vaza": {
				"playerNumber": vaza.playerNumber,
				"cardList": vazaCardList
			},

			"player": {
				"position": self.position,
				"cardList": playerCardList,
				"canTruco": self.canTruco()
			}
		}
		
		sendJson(self.conn, message)
	
	
	
	def getInput(self):
		sendJson(self.conn, {"type": "input"})
		return recvJson(self.conn)
	
	
	
	'''
	def send(self):
		message = {
			"type": "player",
			"position": self.position,
			"cardList": self.cardList,
			"canTruco": self.canTruco()
		}
		sendJson(self.conn, message)
	'''



# ----------------



# --| Vaza |-- Class
# Description: Vaza of mao
class Vaza:
	def __init__(self, game, firstPlayerNumber):
		self.game = game
		self.firstPlayerNumber = firstPlayerNumber
		
		self.canHide = False
	
	
	
	def start(self):
		self.cardList = [None, None, None, None]
		
		self.bestPlayerNumber = self.firstPlayerNumber
		self.highestCard = None
		self.result = TeamPoint.DRAW
	
	
	
	def updateResult(self, playerNumber, player):
		# defining the highest card and its player
		if self.highestCard is None:
			# first player
			self.bestPlayerNumber = playerNumber
			self.highestCard = player.card
			self.result = player.team()
		elif self.highestCard <= player.card:
			# card not lower
			self.bestPlayerNumber = playerNumber
			
			if self.highestCard == player.card:
				# same card value
				self.result = TeamPoint.DRAW
			else:
				# higher card
				self.highestCard = player.card
				self.result = player.team()
	
	
	
	def execute(self):
		# reset variables
		self.start()
		
		# print test
		# print('VAZA!!!')
		# l = [card.print() if card is not None else '?' for card in self.cardList]
		# print(f'table: {l}')
		
		# 4 turns
		for i in range(Game.MAXIMUM_PLAYERS):
			# getting the player info
			self.playerNumber = (i + self.firstPlayerNumber)%Game.MAXIMUM_PLAYERS
			player = self.game.playerList[self.playerNumber]
			
			# notify players
			self.game.send()
			
			# play of the player
			player.play()
			
			# case of truco refused
			if self.game.mao.refused:
				return
			
			# get the drawn card
			self.cardList[self.playerNumber] = player.card
			
			# hide the card if permitted
			if player.hide and self.canHide:
				player.card.hide()
			
			# getting the vaza highest card and its player
			self.updateResult(self.playerNumber, player)
			
			# print test
			# l = [card.print() if card is not None else '?' for card in self.cardList]
			# print(f'table: {l}')
		
		# print test
		# print(f'best player: {self.bestPlayerNumber}, result: {self.result}')
		
		# set the first player to play in the next vaza
		self.firstPlayerNumber = self.bestPlayerNumber
		
		# return the result of the vaza
		return self.result
	
	
	
	def serializeCardList(self):
		cardList = []
		
		for card in self.cardList:
			if card is None:
				cardList.append(41)
			elif card.hidden:
				cardList.append(40)
			else:
				cardList.append(card.serialize())
		
		return cardList
	
	
	
	'''
	+---------------
	| Send Methods
	+---------------
	
	def send(self):
		for player in self.game.playerList:
			message = {
				"type": "vaza",
				"cardList": self.cardList
			}
			sendJson(player.conn, message)
	'''



# ----------------



# --| Mao |-- Class
# Description: mao of truco
class Mao:
	# Mao constructor
	# Description: declares variables
	# Input: empty
	def __init__(self, game):
		self.game = game
		self.value = 1
		self.truco = False
		self.refused = False
		self.trucoTurn = TeamPoint.DRAW
		self.pointList = []
	
	
	
	'''
	+---------------
	| Functions
	+---------------
	'''
	def otherTeam(team):
		return TeamPoint.RED if team == TeamPoint.BLUE else TeamPoint.BLUE
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# --| execute |-- method
	# Description: do a mao, which is, running at most 3 vazas
	# Input: empty
	# Output: the winner team
	def execute(self):
		# shuffling the deck
		deck = self.game.deck
		deck.shuffle()
		
		# distributing cards
		playerList = self.game.playerList
		for player in playerList:
			player.getCards()
		
		# getting the vira
		self.vira = deck.takeCard()
		
		# creating the vaza
		firstPlayerNumber = (self.game.shufflerNumber + 1)%Game.MAXIMUM_PLAYERS
		self.vaza = Vaza(self.game, firstPlayerNumber)
		
		# print test
		#print(f'shuffler: {self.game.shufflerNumber}, vira: {self.vira.print()}')
		
		# ----------------
		# start of the mao
		# ----------------
		vaza1 = self.vaza.execute()
		
		# refused truco
		if self.refused:
			return self.trucoTurn
		
		# register the point
		self.pointList.append(vaza1)
		
		# points cases
		if vaza1 == TeamPoint.DRAW:
			# ----------------
			# 1 draw
			# ----------------
			# notify players
			self.game.send()
			self.game.sendPlayers({"type": "vazaWinner", "winner": vaza1})
			time.sleep(3.0)
			
			vaza2 = self.vaza.execute()
			
			# refused truco
			if self.refused:
				return self.trucoTurn
			
			# register the point
			self.pointList.append(vaza2)
			
			if vaza2 == TeamPoint.DRAW:
				# ----------------
				# 2 draws
				# ----------------
				# notify players
				self.game.send()
				self.game.sendPlayers({"type": "vazaWinner", "winner": vaza2})
				time.sleep(3.0)
				
				vaza3 = self.vaza.execute()
				
				# notify players
				self.game.send()
				
				# refused truco
				if self.refused:
					return self.trucoTurn
				
				# register the point
				self.pointList.append(vaza3)
				
				if vaza3 == TeamPoint.DRAW:
					# ----------------
					# 5º case: 3 draws
					# ----------------
					# shufflerPlayer = Game.playerList[Game.shufflerNumber]
					return self.trucoTurn
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
			# notify players
			self.game.send()
			self.game.sendPlayers({"type": "vazaWinner", "winner": vaza1})
			time.sleep(3.0)
			
			self.vaza.canHide = True
			vaza2 = self.vaza.execute()
			
			# refused truco
			if self.refused:
				return self.trucoTurn
			
			# register the point
			self.pointList.append(vaza2)
			
			if (
				vaza1 == TeamPoint.RED and vaza2 == TeamPoint.BLUE or
				vaza1 == TeamPoint.BLUE and vaza2 == TeamPoint.RED
			):
				# ----------------
				# 1 win, 1 lose
				# ----------------
				# notify players
				self.game.send()
				self.game.sendPlayers({"type": "vazaWinner", "winner": vaza2})
				time.sleep(3.0)
				
				vaza3 = self.vaza.execute()
				
				# refused truco
				if self.refused:
					return self.trucoTurn
				
				# register the point
				self.pointList.append(vaza3)
				
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
	
	
	
	# --| promote |-- method
	# Description: increase the mao's value
	# Input: empty
	# Output: true if value increased, false if not
	def promote(self):
		# if can promote
		if self.value < 12:
			# increase value
			if self.value == 1:
				self.value = 3
			else:
				self.value += 3
			
			# could promote
			return True
		else:
			# could not promote
			return False
	
	
	
	def swithTrucoTurn(self):
		if self.trucoTurn == TeamPoint.RED:
			self.trucoTurn = TeamPoint.BLUE
		elif self.trucoTurn == TeamPoint.BLUE:
			self.trucoTurn = TeamPoint.RED
	
	
	
	'''
	+---------------
	| Send Methods
	+---------------
	
	def send(self):
		for player in self.game.playerList:
			message = {
				"type": "mao",
				"value": self.value,
				"pointList": self.pointList
			}
			sendJson(player.conn, message)
	'''



# ----------------



# --| Game |-- Class
# Description: class where the whole game will be running
class Game:
	# constants
	MAXIMUM_PLAYERS = 4
	MAXIMUM_SCORE = 12
	
	
	
	# Game constructor
	# Description: declares variables
	# Input: empty
	def __init__(self):
		self.deck = Deck(self)
	
	
	
	'''
	+---------------
	| Methods
	+---------------
	'''
	# --| startGame |-- method
	# Description: starts a new truco match
	# Input: empty
	# Output: empty
	def startGame(self):
		# wait for players
		self.connectPlayers()
		
		# start team scores and select the first shuffler
		self.redTeamScore = 0
		self.blueTeamScore = 0
		
		random.seed(time.time())
		self.shufflerNumber = random.randint(0, 3)
		
		# notify players
		# self.send()
		
		# while there is no winner, do the maos
		while self.redTeamScore < Game.MAXIMUM_SCORE and self.blueTeamScore < Game.MAXIMUM_SCORE:
			# do a mao
			self.mao = Mao(self)
			result = self.mao.execute()
			
			# add the points to the winner team
			if result == TeamPoint.RED:
				self.redTeamScore += self.mao.value
			elif result == TeamPoint.BLUE:
				self.blueTeamScore += self.mao.value
			
			# notify players
			self.send()
			self.sendPlayers({"type": "maoWinner", "winner": result})
			time.sleep(3.0)
			
			# the player to the shuffler's left is the new shuffler
			n1 = (Game.MAXIMUM_PLAYERS - 1)
			self.shufflerNumber = (self.shufflerNumber + n1)%Game.MAXIMUM_PLAYERS
			
			# print test
			# print(f'red team: {self.redTeamScore}, blue team: {self.blueTeamScore}')
	
	
	
	# --| connectPlayers |-- method
	# Description: waits for players to connect and create the player list
	# Input: empty
	# Output: empty
	def connectPlayers(self):
		# open the json file
		with open("json/serverConfig.json") as file:
			self.serverConfig = json.load(file)
		
		# create the player list
		self.playerList = []
		
		# start the server
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((self.serverConfig["host"], self.serverConfig["port"]))
		self.server.listen(4)
		
		# connect with each player
		for _ in range(4):
			conn, addr = self.server.accept()
			
			name = recvJson(conn)["name"]
			
			player = Player(self, name, conn, addr)
			self.playerList.append(player)
		
		# shuffle the players
		random.seed(time.time())
		random.shuffle(self.playerList)
		
		for i in range(4):
			self.playerList[i].position = i
	
	
	
	# --| trucoResponse |-- method
	# Description: waits for a truco response from the other team
	# Input: empty
	# Output: empty
	def trucoResponse(self):
		# getting the player positions
		if self.mao.trucoTurn == TeamPoint.RED:
			index1 = 0
			index2 = 2
		elif self.mao.trucoTurn == TeamPoint.BLUE:
			index1 = 1
			index2 = 3
		
		# getting players responses to the truco
		response1 = self.playerList[index1].trucoResponse()
		response2 = self.playerList[index2].trucoResponse()
		
		# computing the common response
		response = max(response1, response2)
		
		# can not increase more than 12
		if 12 <= self.mao.value:
			response = min(response, TrucoResponse.ACCEPT)
		
		# update truco status
		self.mao.truco = (2 == response)
		
		# notify players
		self.send()
		
		# print test
		# print(f'response: {response}, team: {self.mao.trucoTurn}')
		#teamString = "red" if self.mao.trucoTurn == TeamPoint.RED else TeamPoint.BLUE
		
		if response == TrucoResponse.REFUSE:
			# print test
			#print(f'the {teamString} team has refused')
			
			self.mao.swithTrucoTurn()
			self.mao.refused = True
		elif response == TrucoResponse.ACCEPT:
			# print test
			#print(f'the {teamString} team has accepted')
			
			self.mao.promote()
			
			# notify players
			self.send()
		else:
			self.mao.swithTrucoTurn()
			self.mao.promote()
			
			# notify players
			self.send()
			self.trucoResponse()
	
	
	
	'''
	+---------------
	| Send Methods
	+---------------
	'''
	def send(self):
		for player in self.playerList:
			player.sendStatus()
	
	
	
	'''
	def sendScore(self):
		for player in self.playerList:
			message = {
				"type": "score",
				"redTeamScore": self.redTeamScore,
				"blueTeamScore": self.redTeamScore
			}
			sendJson(player.conn, message)
	'''
	
	
	
	def sendPlayers(self, message):
		for player in self.playerList:
			sendJson(player.conn, message)
	


'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	trucao = Game()
	trucao.startGame()