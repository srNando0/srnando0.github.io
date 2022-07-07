import rpyc
import json
from rpyc.utils.server import ThreadedServer



class Node(rpyc.Service):
	# ID number and its neighbours
	id = None
	adjacentList = None
	
	# variables used in probe-echo algorithm
	parent = None
	elected = None
	
	
	
	# kind of a constructor
	def defineVariables(id, adjacentList):
		Node.id = id
		Node.adjacentList = adjacentList
	
	
	
	# probe function
	def exposed_probe(self, parent):
		# if it is the second probe call, return acknowledge
		if Node.parent is not None:
			print(f'Acknowledging {parent}')
			return (False,)
		
		# else, set the parent node and reset the elected node
		print(f'Parent node: {parent}')
		Node.elected = None
		Node.parent = parent
		
		# getting the node with the greatest id number among itself and its neighbours
		vote = Node.id
		for node in Node.adjacentList:
			if vote < node:
				vote = node
		
		# for each adjacent node distinct from itself and its parent node, probe it
		for node in Node.adjacentList:
			if node != Node.id and node != parent:
				# does the connection and probes				
				print(f'Probing {node}')
				conn = rpyc.connect('localhost', 30000 + node)
				response = conn.root.probe(Node.id)
				conn.close()
				
				# if it is an echo, get the node that has the greatest id
				if response[0]:
					if vote < response[1]:
						vote = response[1]
		
		# echo
		print(f'Vote: {vote}')
		return (True, vote)
	
	
	
	# election function
	def exposed_election(self, parent, elected):
		# if it is the second election call, return acknowledge
		if Node.elected is not None:
			return
		
		# else, set elected node and reset the parent one
		print(f'Elected node: {elected}')
		Node.parent = None
		Node.elected = elected
		
		# for each adjacent node distinct from itself and its parent node, send the elected node
		for node in Node.adjacentList:
			if node != Node.id and node != parent:
				# does the connection and send the elected node
				conn = rpyc.connect('localhost', 30000 + node)
				conn.root.election(Node.id, elected)
				conn.close()



'''
+---------------
| Main
+---------------
'''
if __name__ == "__main__":
	# choosing an node by its ID
	with open("graph.json") as file:
		# getting the graph
		graph = json.load(file)
		
		# selecting a valid id
		id = int(input("ID number: "))
		while len(graph) <= id:
			print(f'Invalid ID!\nID you typed: {id}\nGraph size: {len(graph)}\n')
			id = int(input("ID number: "))
		
		# setting variables
		Node.defineVariables(id, graph[id])
		print(graph[id])
	
	# initiates the server
	initiator = ThreadedServer(Node, hostname = 'localhost', port = 30000 + id)
	initiator.daemon = True
	initiator.start()