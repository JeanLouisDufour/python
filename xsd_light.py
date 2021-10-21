from lxml import etree

def _validate(xml_path: str, xsd_path: str) -> bool:

	xmlschema_doc = etree.parse(xsd_path)
	xmlschema = etree.XMLSchema(xmlschema_doc)

	xml_doc = etree.parse(xml_path)
	result = xmlschema.validate(xml_doc)

	return result

#xml_path = r'C:\Users\F074018\Documents\IMUGS\xml\backbone_pr9.reqif'
#xsd_path = r'C:\Users\F074018\Documents\IMUGS\xml\dtc-11-04-05.xsd'
#v = _validate(xml_path, xsd_path)

#import xmlschema

# schema = xmlschema.XMLSchema(xsd_path)

from xml_light import parse, get

def dict_add(d,n,v):
	""
	if n not in d:
		d[n] = [v]
	else:
		d[n].append(v)
		
xsd_types = {'boolean','dateTime','double','ID','IDREF','integer','string'}
# str -> path list (tous des simpleType ou complexType)
typ_d = {k: None for k in xsd_types}

def typ_add(n,v):
	""
	dict_add(typ_d,n,v)

elt_d = {}

def elt_add(n,v):
	""
	dict_add(elt_d,n,v)
	
def xsd_gen(x,p):
	""
	assert isinstance(x,list) # pas d'info en chaine de charactere
	kind = x[0] # [:4] == 'xsd:'
	if len(x) >= 2:
		assert isinstance(x[1],dict)
		if 'name' in x[1]:
			assert ':' not in x[1]['name'], x
			assert kind in ('xsd:attribute', 'xsd:complexType', 'xsd:element', 'xsd:simpleType'), x
		if 'type' in x[1]:
			assert ':' in x[1]['type'], x
			assert kind in ('xsd:attribute', 'xsd:element')
	f = kind_d[kind]
	return f(x,p)

def xsd_all(x,p):
	""
	assert x[1] == {}, x
	assert all(y[0] == 'xsd:element' for y in x[2:]), x

def xsd_any(x,p):
	""
	assert len(x) == 2, x

def xsd_attribute(x,p):
	""
	assert len(x) == 2 and set(x[1]) in ({'name','type','use'}, {'ref','use'}), x
	if 'ref' in x[1]: # utilise uniquement sur REQ-IF
		assert x[1]['ref'] == 'xml:lang'
	else:
		ty = x[1]['type']
		assert ty[:4] == 'xsd:' and ty[4:] in xsd_types, ty
	assert x[1]['use'] in ('optional','required')

def xsd_choice(x,p):
	""
	assert set(x[1]) == {'maxOccurs','minOccurs'}, x
	assert all(y[0] == 'xsd:element' for y in x[2:]), x

def xsd_complexType(x,p):
	""
	name = x[1].get('name')
	if name is None:
		assert x[1] == {}, x
		father = get(xsd,p[:-1])
		assert father[0] == 'xsd:element' and 'type' not in father[1], father
	else:
		assert ':' not in name
		typ_add(name, p)
	k = x[2][0]
	assert k in ('xsd:all','xsd:choice','xsd:group','xsd:sequence'), x
	assert all(y[0]=='xsd:attribute' for y in x[3:]), x

def xsd_element(x,p):
	"""
	obligatoire : name
	soit type
	soit maxOccurs/minOccurs et une def interne 
	"""
	attrs = x[1]
	name = attrs['name']
	assert ':' not in name
	elt_add(name,p)
	minO = attrs.get('minOccurs')
	maxO = attrs.get('maxOccurs')
	ty = attrs.get('type')
	if ty is None:
		assert len(x) == 3
		ty_def = x[-1]
		assert ty_def[0] == 'xsd:complexType' and ty_def[1] == {}
		assert minO in ('0','1'), attrs
		assert maxO in ('1','unbounded'), attrs
	else:
		assert ':' in ty, ty
		assert len(x) == 2
		assert minO in (None,'0','1'), attrs
		assert maxO in (None,'1'), attrs
		assert (minO is None) == (maxO is None), attrs

def xsd_group(x,p):
	""
	pass

def xsd_import(x,p):
	""
	assert len(x)==2 and set(x[1]) == {'namespace','schemaLocation'}
	
def xsd_restriction(x,p):
	""
	assert len(x)==2 and set(x[1]) == {'base'}
	base = x[1]['base']
	assert base.startswith('xsd:') and base[4:] in typ_d, base

def xsd_schema(x,p):
	""
	assert p == []
	assert x[1]['xmlns:xsd'] == "http://www.w3.org/2001/XMLSchema"
	
def xsd_sequence(x,p):
	""
	assert x[1] == {}, x
	assert all(y[0] in ('xsd:element',) for y in x[2:]) or [y[0] for y in x[2:]] == ['xsd:any'], x

def xsd_simpleType(x,p):
	""
	assert set(x[1]) == {'name'}
	name = x[1]['name']
	assert ':' not in name
	typ_add(name,p)
	assert [y[0] for y in x[2:]] == ['xsd:restriction']

kind_d = {
	"xsd:all": xsd_all,
	"xsd:any": xsd_any,
	"xsd:attribute": xsd_attribute,
	"xsd:choice": xsd_choice,
	"xsd:complexType": xsd_complexType,
	"xsd:element": xsd_element,
	"xsd:group": xsd_group,
	"xsd:import": xsd_import,
	"xsd:restriction": xsd_restriction,
	"xsd:schema": xsd_schema,
	"xsd:sequence": xsd_sequence,
	"xsd:simpleType": xsd_simpleType,
}
	
def xsd_chk(x,p):
	""
	if isinstance(x,list):
		k = x[0]
		if k == 'xsd:element':
			ty = x[1].get('type')
			if ty is not None:
				colon_idx = ty.index(':')
				assert ty[:colon_idx] in ('xsd','REQIF'), x
				assert ty[colon_idx+1:] in typ_d, x

xsd = None
#elt_name = elt_type = None

def XMLSchema(xsd_path, ty_prefix_l = ("REQIF:","xsd:")):
	""
	global xsd # , elt_name, elt_type
	xsd, _ = parse(xsd_path)
	xml_iter(xsd, xsd_gen)
	assert all(tv is None or len(tv)==1 for tv in typ_d.values())
	for en, epl in elt_d.items():
		for p in epl:
			elt = get(xsd,p)
			ty = elt[1].get('type')
			if ty is not None:
				assert ty.startswith(ty_prefix_l), ty
				assert ty[ty.index(':')+1:] in typ_d, ty
	xml_iter(xsd, xsd_chk)
# 	assert xsd[0] == "xsd:schema"
# 	assert xsd[1]['xmlns:xsd'] == "http://www.w3.org/2001/XMLSchema"
# 	for i, x in enumerate(xsd[2:], start=2):
# 		assert isinstance(x,list) and x[0][:4] == 'xsd:'
# 		k = x[0][4:]
# 		if k == 'import':
# 			assert len(x)==2 and set(x[1]) == {'namespace','schemaLocation'}
# # 		elif k == 'element': ## le (ou les) top-level(s)
# # 			assert len(x)==2 and len(x[1]) == 2
# # 			assert elt_name == None
# # 			elt_name = x[1]['name']
# # 			elt_type = x[1]['type']
# # 		elif k == 'simpleType':
# # 			pass
# # 		elif k == 'complexType':
# # 			pass
# 		else:
# 			xsd_gen(x,[i])
	return xsd

xml_iter_root = None
def xml_iter(x, f, p = []):
	"f(x,p)"
	global xml_iter_root
	if p == []:
		xml_iter_root = x
	f(x,p)
	if not isinstance(x,list):
		return
	#
	for i,y in enumerate(x[2:], start=2):
		xml_iter(y,f,p+[i])

def xml_pass2(x, p):
	""
	if isinstance(x,list):
		k = x[0]
		if k not in elt_d:
			print('????', k, 'not constrained ????')
		else:
			x_father = get(xml_iter_root, p[:-1]) if len(p)>=1 else None
			kpl = elt_d[k]
			for kp in kpl:
				sch = get(xsd, kp)
				_ = 2+2

##############################

xml_chk_root = None

def td_of_elt(e):
	""
	pass

def xml_element(xml,xml_p, e, e_p):
	""
	if xml != get(xml_chk_root,xml_p):
		assert False
	assert e[0] == 'xsd:element'
	if e != get(xsd,e_p):
		assert False
	if 'type' in e[1]:
		assert len(e)==2
		new_cpty_name = e[1]['type']
		new_cpty_name = new_cpty_name[new_cpty_name.index(':')+1:]
		xml_complexType(xml, xml_p, new_cpty_name)
	else:
		assert len(e)==3
		new_cpty = e[2]
		new_cpty_p = e_p+[2]
		xml_complexType(xml, xml_p, new_cpty, new_cpty_p)

def xml_complexType(xml, xml_p, cpty, cpty_p = None):
	""
	if isinstance(cpty,str):
		assert cpty_p is None
		if cpty in ('dateTime','string'):
			assert len(xml)==3 and isinstance(xml[-1],str)
			return
		[cpty_p] = typ_d[cpty]
		cpty = get(xsd,cpty_p)
		assert cpty is not None
	else:
		if cpty != get(xsd,cpty_p):
			assert False
	if xml != get(xml_chk_root,xml_p):
		assert False
	if cpty[0] == 'xsd:simpleType':
		assert len(xml)==3 and isinstance(xml[-1],str)
		return
	assert cpty[0] == 'xsd:complexType', cpty
	td = cpty; td_p = cpty_p
	tattr_req = {d.get('name','xmlns'):d.get('type') for [_,d] in td[3:] if d['use']=='required'}
	tattr_opt = {d.get('name','xmlns'):d.get('type') for [_,d] in td[3:] if d['use']=='optional'}
	assert len(tattr_req) + len(tattr_opt) + 3 == len(td), td
	for n,t in tattr_req.items():
		if n not in xml[1]:
			print(xml[0], xml_p, 'required attribute',n)
	for n,v in xml[1].items():
		assert n in tattr_req or n in tattr_opt or (xml_p==[] and n.startswith(('xmlns:','xsi:'))), n
	# body
	tbody = td[2]; tbody_p = td_p + [2]
	tbk = tbody[0]
	if tbk == 'xsd:all': # any order
		tag_d = {e[1]['name']:(tbody_p+[e_i],e) for e_i,e in enumerate(tbody[2:], start=2)}
		for x_i,x in enumerate(xml[2:], start=2):
			assert x[0] in tag_d
			elt_p, elt = tag_d[x[0]]
			xml_element(x, xml_p+[x_i], elt, elt_p)
	elif tbk == 'xsd:choice':
		min_max = tbody[1].get('minOccurs'), tbody[1].get('maxOccurs')
		tag_d = {e[1]['name']:(tbody_p+[e_i],e) for e_i,e in enumerate(tbody[2:],start=2)}
		assert len(tag_d) == len(tbody)-2
		for x_i,x in enumerate(xml[2:], start=2):
			assert x[0] in tag_d
			elt_p, elt = tag_d[x[0]]
			xml_element(x, xml_p+[x_i], elt, elt_p)
	elif tbk == 'xsd:sequence':
		if [y[0] for y in tbody[2:]] == ['xsd:any']:
			pass # print(xml[0], xml_p, 'sequence/any : rien a verifier')
		else:
			assert all(y[0] in ('xsd:element',) for y in tbody[2:])
			xml_i = 2
			for e_i,e in enumerate(tbody[2:], start=2):
				e_p = tbody_p + [e_i]
				name = e[1]['name']
				min_max = e[1].get('minOccurs'), e[1].get('maxOccurs')
				if min_max == ('1','1'):	
					x = xml[xml_i]; x_p = xml_p+[xml_i]
					assert x[0] == name
					xml_element(x, x_p, e, e_p)
# 					if 'type' in e[1]:
# 						new_cpty_name = e[1]['type']
# 						new_cpty_name = new_cpty_name[new_cpty_name.index(':')+1:]
# 						xml_complexType(x, xml_p+[xml_i], new_cpty_name)
# 					else:
# 						assert len(e)==3
# 						new_cpty = e[2]
# 						new_cpty_p = cpty_p+[e_i,2]
# 						xml_complexType(x, xml_p+[xml_i], new_cpty, new_cpty_p)
					xml_i += 1
				elif min_max == ('0','1'):
					if xml_i < len(xml) and xml[xml_i][0] == name:
						x = xml[xml_i]; x_p = xml_p+[xml_i]
						xml_element(x, x_p, e, e_p)
# 						if 'type' in e[1]:
# 							new_cpty_name = e[1]['type']
# 							new_cpty_name = new_cpty_name[new_cpty_name.index(':')+1:]
# 							xml_complexType(x, x_p, new_cpty_name)
# 						else:
# 							assert len(e)==3
# 							new_cpty = e[2]; new_cpty_p = e_p+[2]
# 							xml_complexType(x, x_p, new_cpty, new_cpty_p)
						xml_i += 1
				else:
					assert False, min_max
			if xml_i != len(xml):
				assert False
	else:
		assert False, tbk

def xml_chk(xml):
	"""
	"""
	global xml_chk_root
	xml_chk_root = xml
	k = xml[0] # REQ-IF
	assert k == 'REQ-IF'
	pl =  elt_d[k]
	assert len(pl) == 1
	[p] = pl
	elt = get(xsd,p)
	assert elt[0] == 'xsd:element'
	ty = elt[1].get('type')
	if ty is None:
		# type 'inline'
		assert False
	else:
		# type nomme
		[tdp] = typ_d[ty[ty.index(':')+1:]]
		td = get(xsd, tdp)
		if td[0] == 'xsd:simpleType':
			assert False, td # ne sert que pour les attributs ?
		elif td[0] == 'xsd:complexType':
			xml_complexType(xml, [], td, tdp)
		else:
			assert False, td

if __name__ == "__main__":
	xml_path = r'C:\Users\F074018\Documents\IMUGS\xml\backbone_pr9.reqif'
	xsd_path = r'C:\Users\F074018\Documents\IMUGS\xml\dtc-11-04-05.xsd'
	_ = XMLSchema(xsd_path)
	xml,_ = parse(xml_path)
	xml_iter(xml, xml_pass2)
	#
	xml_chk(xml)
	