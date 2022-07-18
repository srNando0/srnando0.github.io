import socket
import json



'''
+---------------
| Functions
+---------------
'''
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
| Main
+---------------
'''
if __name__ == "__main__":
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
		conn.connect(('localhost', 30000))
		
		dictTest = {"test": 123, 456: "leech"}
		sendJson(conn, dictTest)
		dictTest = recvJson(conn)
		
		print(dictTest)
