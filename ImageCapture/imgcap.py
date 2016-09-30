from urllib.request import urlopen
from urllib.request import urlretrieve
from urllib.parse import urljoin
import re
import codecs

url = input("Please input URL to be captured: ")
html = codecs.decode(urlopen(url).read(), 'utf-8')

p = re.compile(r'<img\s+src\s*=\s*"(.*?)"')
res = p.findall(html)

for i in res:
    cur = urljoin(url, i)
    urlretrieve(cur, 'imgs/' + cur[cur.rfind('/')+1:])