class Graph(object):
	def __init__(self):
		self.dict = {}
		self.weight = {}

	# Returns the neighbours of a given node
	def neighbours(self, node):
		return self.dict[node]

	# Returns the list of all outgoing edges from a node
	def outgoingEdges(self, node):
		return {(node, n, self.weight[(node, n)]) for n in self.dict[node]}

	# Adds a node to the graph
	def addNode(self, node):
		if node not in self.dict:
			self.dict[node] = set([])

	# Adds an edge to the graph, and the nodes if they do not exist
	def addEdge(self, node1, node2, weight):
		self.addNode(node1)
		self.addNode(node2)
		self.dict[node1].add(node2)
		self.weight[(node1, node2)] = weight

	def edges(self):
		return {(n1, n2, self.weight[(n1, n2)]) for n1 in self.dict for n2 in self.dict[n1]}

	def nodes(self):
		return self.dict.keys()

	# Returns the string used when printing the graph
	def __str__(self):
		res = f"Graph with {len(self.dict)} vertices and {len(self.edges())} edges :\n"
		for node in self.dict:
			res += f"{str(node)}: "
			for edge in self.outgoingEdges(node):
				res += f"{str(edge)} "
			res = res[:-1] + "\n"
		return res[:-1]