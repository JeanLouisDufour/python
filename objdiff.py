import json

diff_tol_lt = False  ## tol_lt == tol. list / tuple

def diff(o1,o2,ctx=[]):
	"returns : None ou une liste"
	if type(o1) != type(o2):
		if diff_tol_lt and isinstance(o1, (list,tuple)) and isinstance(o2, (list,tuple)):
			if len(o1) != len(o2):
				return ctx
			else:
				for i in range(len(o1)):
					ctx1 = diff(o1[i],o2[i],ctx+[i])
					if ctx1 != None:
						return ctx1
				return None
		elif isinstance(o1,str) or isinstance(o2,str):  # py2x : str et unicode
			if o1==o2:
				return None
			else:
				return ctx
		else:
			return ctx
	elif isinstance(o1, (list,tuple)):
		if len(o1) != len(o2):
			return ctx
		else:
			for i in range(len(o1)):
				ctx1 = diff(o1[i],o2[i],ctx+[i])
				if ctx1 != None:
					return ctx1
			return None
	elif isinstance(o1,dict):
		if len(o1) != len(o2):
			return ctx
		else:
			for i in o1:
				if i not in o2:
					return ctx+[i]
				else:
					ctx1 = diff(o1[i],o2[i],ctx+[i])
					if ctx1 != None:
						return ctx1
			return None
	else:
		if o1 != o2:
			return ctx
		else:
			return None

def is_jsonable(o):
	"returns : None ou une liste"
	print('begin json')
	js = json.dumps(o)
	o1 = json.loads(js)
	delta = diff(o,o1)
	print('end json')
	return delta
