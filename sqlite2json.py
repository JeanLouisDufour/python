import sqlite3 as s3
from hexdump import dump

def doit(fn):
	""
	# db = sqlite3.connect('file:path/to/database?mode=ro', uri=True)
	uri = 'file:' + fn + '?mode=ro'
	with s3.connect(uri, uri=True) as con:
		cur = con.cursor()
		cur.execute("SELECT name FROM sqlite_temp_master WHERE type='table'")
		x = cur.fetchall()
		assert x==[], x
		cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
		tl = cur.fetchall()
		for t1 in tl:
			[t] = t1
			cur.execute(f"SELECT sql FROM sqlite_master WHERE tbl_name = '{t}'")
			x = cur.fetchall()
			assert len(x) >= 1
			[create] = x[0]
			assert create.startswith('CREATE TABLE '+t)
			print(create)
			i0 = create.find('(')
			i1 = create.rfind(')')
			sl = create[i0+1:i1].split(',')
			field_l = []
			for s in sl:
				xl = s.strip().split()
				assert len(xl) in (2,4), create
				assert xl[1].startswith(('BLOB','CHAR(','CHARACTER(','INTEGER','REAL','TEXT','VARCHAR(')), xl
				field_l.append(xl if len(xl)==2 else (xl[:2]+[' '.join(xl[2:])]))
			#
			cur.execute("SELECT * FROM " + t)
			xl = cur.fetchall()
			for x_i, x in enumerate(xl):
				assert len(x) == len(field_l)
				for y_i, y in enumerate(x):
					field = field_l[y_i][0]
					ty = field_l[y_i][1]
					if ty == 'BLOB':
						assert isinstance(y, bytes)
						if y.startswith(b'<?xml'): # TABLE DMRBLOBCHUNKS (  BLOBID INTEGER,  CHUNKINDEX INTEGER,  CHUNKLENGTH INTEGER,  CHUNKDATA BLOB)
							_ = 2+2
						elif y.startswith(b'\x00\x01IM\x00\x00\x00\x00\x0e\x00\x00\x00'):
							print(f'{field} {len(y)}')
							dump(y[:1024])
							_ = 2+2  ### aller chercher R2FInfo mxarray dans le xml
						else:
							assert y==b'', y
					elif ty == 'INTEGER':
						assert isinstance(y, int)
					elif ty == 'REAL':
						assert isinstance(y, float)
					else:
						assert isinstance(y, str), (ty,y)
						assert '<?xml' not in y, y
					_ = 2+2
			_ = 2+2
		_ = 2+2

if __name__ == '__main__':
	fn = r'C:\Users\F074018\Documents\MATLAB\obfuscation\dsp_expm\slprj\modeladvisor\dsp_expm_27_test\ModelAdvisorData'
	doit(fn)
