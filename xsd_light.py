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
	assert isinstance(x,list)
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
	ty = attrs.get('type')
	if ty is None:
		assert len(x) == 3
		ty_def = x[-1]
		assert ty_def[0] == 'xsd:complexType' and ty_def[1] == {}
	else:
		assert ':' in ty, ty
		assert len(x) == 2

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
	pass

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

def XMLSchema(xsd_path):
	""
	global xsd, elt_name, elt_type
	xsd, _ = parse(xsd_path)
	xml_iter(xsd, xsd_gen)
	assert all(tv is None or len(tv)==1 for tv in typ_d.values())
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

def xml_chk(x, p):
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

if __name__ == "__main__":
	xml_path = r'C:\Users\F074018\Documents\IMUGS\xml\backbone_pr9.reqif'
	xsd_path = r'C:\Users\F074018\Documents\IMUGS\xml\dtc-11-04-05.xsd'
	_ = XMLSchema(xsd_path)
	xml,_ = parse(xml_path)
	xml_iter(xml, xml_chk)
	