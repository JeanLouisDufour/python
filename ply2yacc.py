'''
Created on 29 mars 2018

@author: F074018
'''
import base64, inspect, re, sys, types

def tok2str(t):
	""
	if not t[0].isalpha():
		t = "'"+t+"'"
	return t

### bouchons ####

class PlyLogger(object):
	def __init__(self, f):
		pass

### code reel ####

yaccdebug   = True             # Debugging mode.  If set, yacc generates a
								# a 'parser.out' file in the current directory

debug_file  = 'parser.out'     # Default name of the debugging file
tab_module  = 'parsetab'       # Default name of the table module

if sys.version_info[0] < 3:
	string_types = basestring
else:
	string_types = str

class YaccError(Exception):
	pass

def get_caller_module_dict(levels):
	f = sys._getframe(levels)
	ldict = f.f_globals.copy()
	if f.f_globals != f.f_locals:
		ldict.update(f.f_locals)
	return ldict

def parse_grammar(doc, file, line):
	grammar = []
	# Split the doc string into lines
	pstrings = doc.splitlines()
	lastp = None
	dline = line
	for ps in pstrings:
		dline += 1
		p = ps.split()
		if not p:
			continue
		try:
			if p[0] == '|':
				# This is a continuation of a previous rule
				if not lastp:
					raise SyntaxError("%s:%d: Misplaced '|'" % (file, dline))
				prodname = lastp
				syms = p[1:]
			else:
				prodname = p[0]
				lastp = prodname
				syms   = p[2:]
				assign = p[1]
				if assign != ':' and assign != '::=':
					raise SyntaxError("%s:%d: Syntax error. Expected ':'" % (file, dline))

			grammar.append((file, dline, prodname, syms))
		except SyntaxError:
			raise
		except Exception:
			raise SyntaxError('%s:%d: Syntax error in rule %r' % (file, dline, ps.strip()))

	return grammar

class ParserReflect(object):
	def __init__(self, pdict, log=None):
		self.pdict	  = pdict
		self.start	  = None
		self.error_func = None
		self.tokens	 = None
		self.modules	= set()
		self.grammar	= []
		self.error	  = False

		if log is None:
			self.log = PlyLogger(sys.stderr)
		else:
			self.log = log

	# Get all of the basic information
	def get_all(self):
		self.get_start()
		self.get_error_func()
		self.get_tokens()
		self.get_precedence()
		self.get_pfunctions()

	# Validate all of the information
	def validate_all(self):
		self.validate_start()
		self.validate_error_func()
		self.validate_tokens()
		self.validate_precedence()
		self.validate_pfunctions()
		self.validate_modules()
		return self.error

	# Compute a signature over the grammar
	def signature(self):
		try:
			from hashlib import md5
		except ImportError:
			from md5 import md5
		try:
			sig = md5()
			if self.start:
				sig.update(self.start.encode('latin-1'))
			if self.prec:
				sig.update(''.join([''.join(p) for p in self.prec]).encode('latin-1'))
			if self.tokens:
				sig.update(' '.join(self.tokens).encode('latin-1'))
			for f in self.pfuncs:
				if f[3]:
					sig.update(f[3].encode('latin-1'))
		except (TypeError, ValueError):
			pass

		digest = base64.b16encode(sig.digest())
		if sys.version_info[0] >= 3:
			digest = digest.decode('latin-1')
		return digest

	# -----------------------------------------------------------------------------
	# validate_modules()
	#
	# This method checks to see if there are duplicated p_rulename() functions
	# in the parser module file.  Without this function, it is really easy for
	# users to make mistakes by cutting and pasting code fragments (and it's a real
	# bugger to try and figure out why the resulting parser doesn't work).  Therefore,
	# we just do a little regular expression pattern matching of def statements
	# to try and detect duplicates.
	# -----------------------------------------------------------------------------

	def validate_modules(self):
		# Match def p_funcname(
		fre = re.compile(r'\s*def\s+(p_[a-zA-Z_0-9]*)\(')

		for module in self.modules:
			try:
				lines, linen = inspect.getsourcelines(module)
			except IOError:
				continue

			counthash = {}
			for linen, line in enumerate(lines):
				linen += 1
				m = fre.match(line)
				if m:
					name = m.group(1)
					prev = counthash.get(name)
					if not prev:
						counthash[name] = linen
					else:
						filename = inspect.getsourcefile(module)
						self.log.warning('%s:%d: Function %s redefined. Previously defined on line %d',
										 filename, linen, name, prev)

	# Get the start symbol
	def get_start(self):
		self.start = self.pdict.get('start')

	# Validate the start symbol
	def validate_start(self):
		if self.start is not None:
			if not isinstance(self.start, string_types):
				self.log.error("'start' must be a string")

	# Look for error handler
	def get_error_func(self):
		self.error_func = self.pdict.get('p_error')

	# Validate the error function
	def validate_error_func(self):
		if self.error_func:
			if isinstance(self.error_func, types.FunctionType):
				ismethod = 0
			elif isinstance(self.error_func, types.MethodType):
				ismethod = 1
			else:
				self.log.error("'p_error' defined, but is not a function or method")
				self.error = True
				return

			eline = self.error_func.__code__.co_firstlineno
			efile = self.error_func.__code__.co_filename
			module = inspect.getmodule(self.error_func)
			self.modules.add(module)

			argcount = self.error_func.__code__.co_argcount - ismethod
			if argcount != 1:
				self.log.error('%s:%d: p_error() requires 1 argument', efile, eline)
				self.error = True

	# Get the tokens map
	def get_tokens(self):
		tokens = self.pdict.get('tokens')
		if not tokens:
			self.log.error('No token list is defined')
			self.error = True
			return

		if not isinstance(tokens, (list, tuple)):
			self.log.error('tokens must be a list or tuple')
			self.error = True
			return

		if not tokens:
			self.log.error('tokens is empty')
			self.error = True
			return

		self.tokens = tokens

	# Validate the tokens
	def validate_tokens(self):
		# Validate the tokens.
		if 'error' in self.tokens:
			self.log.error("Illegal token name 'error'. Is a reserved word")
			self.error = True
			return

		terminals = set()
		for n in self.tokens:
			if n in terminals:
				self.log.warning('Token %r multiply defined', n)
			terminals.add(n)

	# Get the precedence map (if any)
	def get_precedence(self):
		self.prec = self.pdict.get('precedence')

	# Validate and parse the precedence map
	def validate_precedence(self):
		preclist = []
		if self.prec:
			if not isinstance(self.prec, (list, tuple)):
				self.log.error('precedence must be a list or tuple')
				self.error = True
				return
			for level, p in enumerate(self.prec):
				if not isinstance(p, (list, tuple)):
					self.log.error('Bad precedence table')
					self.error = True
					return

				if len(p) < 2:
					self.log.error('Malformed precedence entry %s. Must be (assoc, term, ..., term)', p)
					self.error = True
					return
				assoc = p[0]
				if not isinstance(assoc, string_types):
					self.log.error('precedence associativity must be a string')
					self.error = True
					return
				for term in p[1:]:
					if not isinstance(term, string_types):
						self.log.error('precedence items must be strings')
						self.error = True
						return
					preclist.append((term, assoc, level+1))
		self.preclist = preclist

	# Get all p_functions from the grammar
	def get_pfunctions(self):
		p_functions = []
		for name, item in self.pdict.items():
			if not name.startswith('p_') or name == 'p_error':
				continue
			if isinstance(item, (types.FunctionType, types.MethodType)):
				line = getattr(item, 'co_firstlineno', item.__code__.co_firstlineno)
				module = inspect.getmodule(item)
				p_functions.append((line, module, name, item.__doc__))

		# Sort all of the actions by line number; make sure to stringify
		# modules to make them sortable, since `line` may not uniquely sort all
		# p functions
		p_functions.sort(key=lambda p_function: (
			p_function[0],
			str(p_function[1]),
			p_function[2],
			p_function[3]))
		self.pfuncs = p_functions

	# Validate all of the p_functions
	def validate_pfunctions(self):
		grammar = []
		# Check for non-empty symbols
		if len(self.pfuncs) == 0:
			self.log.error('no rules of the form p_rulename are defined')
			self.error = True
			return

		for line, module, name, doc in self.pfuncs:
			file = inspect.getsourcefile(module)
			func = self.pdict[name]
			if isinstance(func, types.MethodType):
				reqargs = 2
			else:
				reqargs = 1
			if func.__code__.co_argcount > reqargs:
				self.log.error('%s:%d: Rule %r has too many arguments', file, line, func.__name__)
				self.error = True
			elif func.__code__.co_argcount < reqargs:
				self.log.error('%s:%d: Rule %r requires an argument', file, line, func.__name__)
				self.error = True
			elif not func.__doc__:
				self.log.warning('%s:%d: No documentation string specified in function %r (ignored)',
								 file, line, func.__name__)
			else:
				try:
					parsed_g = parse_grammar(doc, file, line)
					for g in parsed_g:
						grammar.append((name, g))
				except SyntaxError as e:
					self.log.error(str(e))
					self.error = True

				# Looks like a valid grammar rule
				# Mark the file in which defined.
				self.modules.add(module)

		# Secondary validation step that looks for p_ definitions that are not functions
		# or functions that look like they might be grammar rules.

		for n, v in self.pdict.items():
			if n.startswith('p_') and isinstance(v, (types.FunctionType, types.MethodType)):
				continue
			if n.startswith('t_'):
				continue
			if n.startswith('p_') and n != 'p_error':
				self.log.warning('%r not defined as a function', n)
			if ((isinstance(v, types.FunctionType) and v.__code__.co_argcount == 1) or
				   (isinstance(v, types.MethodType) and v.__func__.__code__.co_argcount == 2)):
				if v.__doc__:
					try:
						doc = v.__doc__.split(' ')
						if doc[1] == ':':
							self.log.warning('%s:%d: Possible grammar rule %r defined without p_ prefix',
											 v.__code__.co_filename, v.__code__.co_firstlineno, n)
					except IndexError:
						pass

		self.grammar = grammar


def yacc(method='LALR', debug=yaccdebug, module=None, tabmodule=tab_module, start=None,
		 check_recursion=True, optimize=False, write_tables=True, debugfile=debug_file,
		 outputdir=None, debuglog=None, errorlog=None, picklefile=None):
	if module:
		_items = [(k, getattr(module, k)) for k in dir(module)]
		pdict = dict(_items)
		# If no __file__ attribute is available, try to obtain it from the __module__ instead
		if '__file__' not in pdict:
			pdict['__file__'] = sys.modules[pdict['__module__']].__file__
	else:
		pdict = get_caller_module_dict(2)
	# Set start symbol if it's specified directly using an argument
	if start is not None:
		pdict['start'] = start

	# Collect parser information from the dictionary
	pinfo = ParserReflect(pdict, log=errorlog)
	pinfo.get_all()

	if pinfo.error:
		raise YaccError('Unable to build parser')
	
	if pinfo.validate_all():
		raise YaccError('Unable to build parser')

	####
	
	if 'start' in pdict:
		prod_start = pdict['start']
	else:
		fr = pinfo.pfuncs[0][3]
		prod_start = fr[:fr.find(':')].strip()
	prod_tokens = pinfo.tokens
	prec_dict = {}
	for tok,assoc, prec in pinfo.preclist:
		if prec in prec_dict:
			if assoc in prec_dict[prec]:
				prec_dict[prec][assoc].append(tok)
			else:
				prec_dict[prec][assoc] = [tok]
		else:
			prec_dict[prec] = {assoc:[tok]}
	prod_precedence = []
	for prec in sorted(prec_dict):
		for assoc in prec_dict[prec]:
			tokl = prec_dict[prec][assoc]
			prod_precedence.append([assoc]+tokl)
	prods = [pf[3].strip() for pf in pinfo.pfuncs]
	
	with open('gram.y','w') as f:
		f.write('%start {}\n'.format(prod_start))
		for tok in prod_tokens:
			f.write('%token {}\n'.format(tok))
		for prec in prod_precedence:
			f.write('%{} {}\n'.format(prec[0], ' '.join(map(tok2str,prec[1:]))))
		f.write('%%\n')
		for r in sorted(prods):
			f.write(r)
			if not r.endswith(('\n','\n\t','\t\t')):
				f.write('\n')
		f.write('%%\n')
