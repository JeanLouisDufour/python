import math

def is_character_printable(s):
	## This method returns true if a byte is a printable ascii character ##
	return all((c < 127) and (c >= 32) for c in s)
  
dump_header = "Offset 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\n"
  
def b2c(byte):
	## Check if byte is a printable ascii character. If not replace with a '.' character ##
	if is_character_printable(byte):
		return chr(ord(byte))
	else:
		return '.'

def dump(ba):
	""
	for i in range(math.ceil(len(ba) / 16)):
		j = i*16
		b = ba[j:j+16]
		bx = ' '.join(b[k:k+1].hex() for k in range(len(b)))
		bx += ' '*(3*15+2-len(bx))
		s = ''.join((chr(c) if 32<=c<127 else '.') for c in b)
		print(f'{j:06X} {bx} {s}')
