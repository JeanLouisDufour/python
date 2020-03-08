import codecs
	
xprint_fd = None

def xopen(fn):
	""
	global xprint_fd
	if xprint_fd != None: xclose()
	xprint_fd = codecs.open(fn,'w','utf-8')
	return xprint_fd
	
def xclose():
	""
	global xprint_fd
	assert xprint_fd != None
	xprint_fd.close()
	xprint_fd = None
	
def xprint(s,*args):
	if len(args) > 0:
		s = s.format(*args)
	print(s)
	if xprint_fd != None:
		print(s, file=xprint_fd)
