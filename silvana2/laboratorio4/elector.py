import rpyc
import json



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
		id = int(input("Node ID: "))
		while len(graph) <= id:
			print(f'Invalid ID!\nID you typed: {id}\nGraph size: {len(graph)}\n')
			id = int(input("ID number: "))
	
	# connects with the chosen node
	conn = rpyc.connect('localhost', 30000 + id)
	
	# does the probe-echo to get the elected node
	elected = conn.root.probe(-1)[1]
	
	# prints the elected node
	print(elected)
	
	# spreads out the elected node
	conn.root.election(-1, elected)
	
	# closes the connection
	conn.close()