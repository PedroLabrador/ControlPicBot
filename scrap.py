from lxml import html
import requests

def get_cne_data(n, c):
	url      = "http://www.cne.gob.ve/web/registro_electoral/ce.php?nacionalidad={}&cedula={}".format(n, c)
	page     = requests.get(url)
	tree     = html.fromstring(page.content)
	selected = tree.xpath('//td[@align="left"]')
	titles   = [d.text_content().rstrip().encode('latin1').decode('utf-8')[:-1] for k, d in enumerate(selected) if k % 2 == 0]
	data     = [d.text_content().rstrip().encode('latin1').decode('utf-8') for k, d in enumerate(selected) if k % 2 == 1]
	return titles, data

