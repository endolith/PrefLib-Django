def findChoiceValue(choices, key):
	return next((v for k, v in choices if k == key), None)

def isAChoice(choices, choice):
	return any(c[0] == choice for c in choices)

DATACATEGORY = [
	('ED', 'election'),
	('MD', 'matching'),
	('CD', 'combinatorial'),
	# ('OD', 'optimization')
]

DATATYPES = [
	('soc', 'strict order complete'), 
	('soi', 'strict order incomplete'), 
	('toc', 'tie order complete'), 
	('toi', 'tie order incomplete'), 
	('tog', 'tournament graph'), 
	('mjg', 'majority graph'), 
	('wmg', 'weighted majority graph'), 
	('pwg', 'pairwise graph'), 
	('wmd', 'weighted matching data'),
	('dat', 'extra data file'),
	('csv', 'comma-separated values')
]

MODIFICATIONTYPES = [
	('original', 'original'),
	('induced', 'induced'),
	('imbued', 'imbued'),
	('synthetic', 'synthetic')
]

METADATACATEGORIES = [
	('general', 'general properties'),
	('preference', 'preference structure'),
	('ballot', 'ballot structure'),
	# ('graph', 'graph structure')
]

SEARCHWIDGETS = [
	('ternary', 'ternary choices'),
	('range', 'range')
]