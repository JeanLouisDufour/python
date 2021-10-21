# coding:utf-8

import xml.parsers.expat, re, codecs, json, os.path
from functools import reduce

class six():
	"equivalent de 'import six'"
	import sys
	if sys.version_info[0] == 2:
		PY2,PY3 = True,False
		import types
		string_types = basestring,
		integer_types = (int, long)
		class_types = (type, types.ClassType)
		text_type = unicode
		binary_type = str
	else:
		assert sys.version_info[0] == 3
		PY2,PY3 = False,True
		string_types = str,
		integer_types = int,
		class_types = type,
		text_type = str
		binary_type = bytes

stack = []
def push(x):
	global stack
	stack.append(x)
def pop():
	global stack
	return stack.pop()
def path():
	global stack
	return [len(x) for x in stack[1:]]

# 5 handler functions
curr_elem = None
parse_tree = None
parse_ids = {}
G_re_blank = None
debug = False
debug_string = None
ID_name = 'id'

def start_document():
	global parse_tree, parse_ids
	assert stack == [] and curr_elem == None
	parse_tree = None
	parse_ids = {}
	
def end_document():
	assert stack == [] and curr_elem == None

def lastSonHasToBeSkipped():
	#
	return len(curr_elem)>1 and isinstance(curr_elem[-1], six.string_types) and G_re_blank and G_re_blank.match(curr_elem[-1])
	
def start_element(name, attrs):
	global curr_elem, parse_ids, debug
	if debug:
		debug = True
	if curr_elem and lastSonHasToBeSkipped():
		curr_elem.pop()
	push(curr_elem)
	curr_elem = [name,attrs]
	aid = attrs.get(ID_name) # if ID_name is not None else None
	if aid != None:
		if aid not in parse_ids:
			parse_ids[aid] = (curr_elem, path())
		elif parse_ids[aid] != None:
			parse_ids[aid] = None
			print('WARNING : multiple id : <<'+aid+'>>')

def end_element(name):
	global curr_elem, parse_tree, debug
	if debug:
		debug = True
	assert name == curr_elem[0]
	### attention : cela transforme <foo> </foo> en <foo/>  (genant pour <strong> par exemple)
	if lastSonHasToBeSkipped():
		curr_elem.pop()
	father = pop()
	if father != None:
		father.append(curr_elem)
		curr_elem = father
	else: # fin de parsing
		assert stack == []
		parse_tree = curr_elem
		curr_elem = None

def char_data(data):
	global curr_elem, debug
	if debug or (debug_string and debug_string in data):
		debug = True
	if len(curr_elem)>1 and isinstance(curr_elem[-1], six.string_types):
		curr_elem[-1] += data
	else:
		curr_elem.append(data)
	#print('Character data:', repr(data))
	#if not (G_re_blank and G_re_blank.match(data)):
	#	curr_elem.append(data)

def parse(fn, txt_skip="^[ \t\r\n]*$", id_name='id'):
	global parse_tree, parse_ids, G_re_blank, ID_name
	ID_name = id_name
	if txt_skip == None:
		G_re_blank = None
	else:
		G_re_blank = re.compile(txt_skip)
	
	p = xml.parsers.expat.ParserCreate()
	p.StartElementHandler = start_element
	p.EndElementHandler = end_element
	p.CharacterDataHandler = char_data
	
	if isinstance(fn,six.string_types):
		if os.path.exists(fn):
			# print('XML parse : '+fn)
			fd = open(fn,'rb' if six.PY3 else 'rb') # 'r' en Py2
		else:
			print('ERREUR: fichier non trouve: '+fn)
			return (None, None)
	else:
		fd = fn
	start_document()
	p.ParseFile(fd)
	end_document()
	if isinstance(fn,six.string_types):
		fd.close()
	r = (parse_tree, parse_ids)
	parse_tree = None
	parse_ids = {}
	return r

def parseString(s, txt_skip="^[ \t\r\n]*$", id_name='id'):
	#
	import io
	return parse(io.BytesIO(bytes(s,encoding='utf-8')), txt_skip, id_name)

#############################

fn_getitem1 = list.__getitem__
fn_getitem2 = lambda o, i: o[i]
def get(tree,path, default=None):
	#
	try:
		return reduce(fn_getitem2,path,tree)
	except IndexError:
		return default

def firstChildIndex(js):
	"""
	l'index peut etre en dehors de l'element
	pour avoir le nombre d'elements :
	len(curr_elem)-firstChildIndex(curr_elem)
	"""
	assert isinstance(js,list) and len(js)>=1
	if len(js)==1 or not isinstance(js[1],dict):
		return 1
	else:
		return 2

##########  API DOM de Javascript

def getAttribute(js,k):
	"""
	"""
	assert isinstance(js,list) and len(js)>=1
	if len(js)==1 or not isinstance(js[1],dict):
		return None
	else:
		return js[1].get(k)
	
def hasAttribute(js,k):
	"""
	"""
	assert isinstance(js,list) and len(js)>=1
	return False if len(js)==1 or not isinstance(js[1],dict) else k in js[1]

def setAttribute(js,k,v):
	"""
	"""
	assert isinstance(js,list) and len(js)>=1
	if len(js)==1 or not isinstance(js[1],dict):
		js.insert(1,{k:v})
	else:
		js[1][k] = v


########################################
# match with 'function toto(' and 'var toto ='
G_re_function_or_var = re.compile(r'function\s+[\$\w]\w*\s*\(|var\s+[\$\w]\w*\s*=')

def createJHTML_head(titre="", entetes=[]):
	"""
	"""
	#from json import dumps
	jh = ['head',
			['meta',{'charset':"utf-8", 'content':"text/html", 'http-equiv':"Content-type"}],
			['title', titre]]
	for s in entetes:
		if isinstance(s,dict):
			r = ['script', {'type':"text/javascript"}]
			for k,v in s.items():
				r.append(" ".join(['var',k,'=',json.dumps(v,indent=0),';']))
			jh.append(r)
		elif isinstance(s,list):
			assert False
		elif s.endswith('.css'):
			# <link href="css/classic.css" media="screen" rel="stylesheet" type="text/css"/>
			jh.append(['link', {'href':s, 'media':"screen", 'rel':"stylesheet", 'type':"text/css"}])
		elif s.endswith('.js'):
			# <script src="scripts/menubar.js"></script>
			jh.append(['script', {'src':s},'']) #### WARNING : le '' est important
		elif s.endswith('.ico'):
			# <link href="images/favicon.ico" rel="icon" type="image/png"/>
			jh.append(['link', {'href':s, 'rel':"icon", 'type':"image/png"}])
		elif G_re_function_or_var.search(s): # 'function ' in s and 'var ' in s:
			jh.append(['script', {'type':"text/javascript"}, s])
		else:
			jh.append(['style',s])
	return jh

# pour Jython
xhtml_preamble = """\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
"""

writeJHTML_fd = None
writeJHTML_tagsNotEmpty = None

def writeJHTML2File(f, js, html=True):
	"""
	"""
	global writeJHTML_fd, writeJHTML_tagsNotEmpty
	writeJHTML_fd = codecs.open(f, mode = 'w', encoding = 'utf-8')
	#writeJHTML_fd.write(xhtml_preamble)
	writeJHTML_fd.write('<?xml version="1.0" encoding="utf-8"?>\n')
	if html:
		writeJHTML_fd.write('<!DOCTYPE html>\n')
		writeJHTML_tagsNotEmpty = {'div'}
	else:
		writeJHTML_tagsNotEmpty = set()
	writeJHTML_doit(js)
	writeJHTML_fd.close()
	writeJHTML_fd = None
	writeJHTML_tagsNotEmpty = None

def writeJHTML_doit(js):
	"""
	"""
	if isinstance(js,list):
		writeJHTML_fd.writelines(['<',js[0]])
		if len(js)>1 and isinstance(js[1],dict):
			inext = 2
			for k,v in js[1].items():
				v = v.replace('"','&quot;')
				writeJHTML_fd.writelines([' ',k,'="',v,'"'])
		else:
			inext = 1
		if inext == len(js) and js[0] not in writeJHTML_tagsNotEmpty:
			writeJHTML_fd.write('/>\n')
		elif inext == len(js)-1 and not isinstance(js[inext],list):
			v = js[inext].replace('&','&amp;').replace('<','&lt;') # ordre important
			writeJHTML_fd.writelines(['>',v,'</',js[0],'>\n'])
		else:
			writeJHTML_fd.write('>\n')
			for son in js[inext:]:
				writeJHTML_doit(son)
			writeJHTML_fd.writelines(['</',js[0],'>\n'])
	else:
		js = js.replace('&','&amp;').replace('<','&lt;') # ordre important
		writeJHTML_fd.writelines([js,'\n'])

######################################

# def ref_parseString(s):
# 	#
# 	from xml.dom.minidom import parseString as dom_parseString
# 	from libXMLUtil import XML2JsonML
# 	xml = dom_parseString(s)
# 	js = XML2JsonML(xml) # TEXT_filter=libXMLUtil.isXmlBlank
# 	return js

if __name__ == '__main__':
	
	sl = ["""<foo>
ligne1
ligne2
</foo>
""", """
<foo>


</foo>
"""]
	for s in sl:
		print('<<<<')
		print(s)
		print('>>>>')
# 		ref_js = ref_parseString(s)
# 		print(ref_js)
		js = parseString(s)
		print(js)
	