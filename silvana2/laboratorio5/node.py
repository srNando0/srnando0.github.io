import socket
import json

from threading import Thread, Lock



'''
+---------------
| Functions
+---------------
'''
# --| sendJson |-- function
# Description: send JSON data
# Input: a socket and a dictionary
# Output: None
def sendJson(conn, dictionary):
	# get message size
	text = json.dumps(dictionary, separators = (',', ':'))
	size = min(len(text), 65535)
	
	# limit the message size
	text = text[:size]
	
	# concatenate the first byte(size) with the message, and return
	arr = [size.to_bytes(2, byteorder = "little"), text.encode("utf-8")]
	conn.sendall(b''.join(arr))



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



# ----------------



'''
+---------------
| Classes
+---------------
'''
class Node(Thread):
	def __init__(self, id):
		# thread variables
		super().__init__()
		self.daemon = True
		
		# ID numbers
		self.id = id
		self.primaryCopyId = 1
		
		# replica variables
		self.X = 0
		self.changeHistory = []
		
		# mutual exclusion
		self.lock = Lock()
		
		# socket
		self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.conn.bind(('localhost', 30000 + self.id))
		self.conn.listen(4)
		self.start()
	
	
	
	def read(self):
		with self.lock:
			X = self.X
		
		return X
	
	
	
	def getChangeHistory(self):
		with self.lock:
			changeHistory = self.changeHistory
		
		return changeHistory
	
	
	
	def write(self, valueList):
		with self.lock:
			# while this node does not have the primary copy
			while self.primaryCopyId != self.id:
				request = {
					"type": "primaryCopy",
					"id": self.id
				}
				
				# print test
				#print("write. before primaryCopy")
				with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
					conn.connect(('localhost', 30000 + self.primaryCopyId))
					sendJson(conn, request)
					response = recvJson(conn)
					# print test
					#print(response)
				# print test
				#print("write. after primaryCopy")
				
				id = response["id"]
				self.primaryCopyId = id
			
			# change the replica
			for value in valueList:
				self.X = value
				self.changeHistory.append((self.id, value))
			
			# update other replicas
			request = {
				"type": "update",
				"id": self.id,
				"data": self.X
			}
			
			for i in range(1, 5):
				if i != self.id:
					# print test
					#print("write. before update")
					with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
						conn.connect(('localhost', 30000 + i))
						sendJson(conn, request)
						response = recvJson(conn)
						# print test
						#print(response)
					# print test
					#print("write. after update")
	
	
	
	def updateRequest(self, id, value):
		with self.lock:
			self.X = value
			self.changeHistory.append((id, value))
	
	
	
	def primaryCopyRequest(self, id):
		with self.lock:
			if self.primaryCopyId == self.id:
				# if this node has the primary copy
				primaryCopyId = id
				self.primaryCopyId = id
			else:
				# if this node does not have the primary copy
				primaryCopyId = self.primaryCopyId
		
		return primaryCopyId
	
	
	
	def run(self):
		while(True):
			conn, addr = self.conn.accept()
			request = recvJson(conn)
			# print test
			#print(request)
			type = request["type"]
			
			if type == "update":
				id = request["id"]
				data = request["data"]
				self.updateRequest(id, data)
				response = {
					"type": "update",
					"acknowledge": True
				}
			
			elif type == "primaryCopy":
				id = request["id"]
				response = {
					"type": "primaryCopy",
					"id": self.primaryCopyRequest(id)
				}
			
			sendJson(conn, response)	
			conn.close()



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	node = Node(int(input("---> ID: ")))
	
	clientRequest = input("\
+---------------\n\
| 1. read the current X value\n\
| 2. read the X value change history\n\
| 3. change the X value\n\
| 4. exit the program\n\
+---------------\n\
---> Select an option: ")
	
	while(clientRequest != '4'):
		if clientRequest == '1':
			print(f'\n\
+----------------\n\
| The current value of X is: {node.read()}\n\
+----------------\n')
		
		
		
		elif clientRequest == '2':
			changeHistory = node.getChangeHistory()
			
			print("\n\
+----------------\n\
| X value change history\n\
+----------------")
			for id, value in changeHistory:
				print(f'| The {id}th node changed X to {value}')
			print("+----------------\n")
		
		
		
		elif clientRequest == '3':
			print("\n\
+----------------\n\
| changing X value\n\
+----------------")
			valueList = [int(input("---> Type a new value for X: "))]
			
			while input("---> Want to change again? y/n") == 'y':
				valueList.append(int(input("Type a new value for X: ")))
			
			node.write(valueList)
			print(f'\
| changes: {valueList}\n\
+----------------\n')
		
		
		
		else:
			print("\n\
+----------------\n\
| Wrong option. Try again!\n\
+----------------\n")
		
		
		
		clientRequest = input("\
+---------------\n\
| 1. read the current X value\n\
| 2. read the X value change history\n\
| 3. change the X value\n\
| 4. exit the program\n\
+---------------\n\
---> Select an option: ")
