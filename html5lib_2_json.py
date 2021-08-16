import html5lib
import glob, xml.etree.ElementTree as ET

xmlns_default = 'http://www.w3.org/1999/xhtml'
xmlns = None
xmlns_ext = {}

def analyze_tag(tag):
	""
	assert isinstance(tag, str), tag
	i = tag.find('}')
	if i >= 0:
		assert tag[0] == '{', tag
		#assert tag[1:i] == (xmlns or xmlns_default), (tag,xmlns)
		tag = tag[i+1:]
	else:
		_ = 2+2 # assert xmlns is None
	assert tag.isidentifier() or all(s.isidentifier() for s in tag.split(':')), tag
	return tag

def to_json(e):
	""
	assert isinstance(e, ET.Element) and e.tag != ET.Comment
	js = [analyze_tag(e.tag), e.attrib]
	t = e.text
	if t is not None:
		assert isinstance(t,str), type(t)
		if t == '': ### possible sur restructuration ex : <p> ... </strong> </p>  -> ''<strong> inséré
			_ = 2+2
		js.append(t)
	for child in e:
		if child.tag != ET.Comment:
			js.append(to_json(child))
		t = child.tail
		if t is not None:
			assert isinstance(t,str), type(t)
			assert t != ''
			js.append(t)
	return js

def parse(fn, strict=False):
	""
	global xmlns, xmlns_ext
	p5 = html5lib.HTMLParser(strict=strict)
	with open(fn, "rb") as fd:
		doc = p5.parse(fd) # html5lib
	assert isinstance(doc, ET.Element)
	tag = doc.tag
	attrib = doc.attrib
	xmlns = attrib.get('xmlns')
	xmlns_ext = {k:v for k,v in attrib.items() if k.startswith('xmlns') and k != 'xmlns'} # xmlns:foo
	assert all(k.startswith('xmlns:') for k in xmlns_ext), xmlns_ext
	#
	tag = analyze_tag(tag)
	assert tag == 'html'
	js = to_json(doc)
	return js
	
if __name__ == '__main__':
	if False:
		s = """
		<html><body>
		aaa <em>bbb</em><em>ccc</em> ddd
		</body></html>
		"""
		doc = html5lib.parse(s)
		js = to_json(doc)
		print(js)
	file_pat = r'C:\Program Files\MATLAB\R2020b\help\**\*.html'
	file_pat = r'C:\Program Files\MATLAB\R2020b\help\physmod\sps\ref\accelerometer.html'
	file_pat = r'C:\Program Files\MATLAB\R2020b\help\physmod\simscape\ref\**\*.html'
	file_pat = r'C:\Program Files\MATLAB\R2020b\**\*.html'
	#file_pat = r'C:\Program Files\MATLAB\R2020b\examples\slrequirements\data\autopilot_requirements.html'
	#file_pat = r'C:\Program Files\MATLAB\R2020b\help\map\ref\elevation.html'
	end_excluded = ()
	for f in glob.glob(file_pat, recursive=True):
		if f.endswith(end_excluded): continue
		print(f)
		js = parse(f)
		_ = 2+2
		