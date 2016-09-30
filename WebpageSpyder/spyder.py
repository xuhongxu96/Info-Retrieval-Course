from urllib.request import *
from urllib.parse import *
import re
import codecs
import os
import threading


class Spyder:
    url_list = ['http://www.bnu.edu.cn']
    finish = []

    HYPERLINK = 'hyperlink'
    RESOURCE = 'resource'
    IGNORE = '#'
    PAGE_SUFFIX = ['.htm', '.html', '.php', '.asp', '.aspx', '.jsp', '.cgi', '.jspx', '.shtml', '.jspa',
                   '.action', '.do', '.jhtml']
    RESOURCE_SUFFIX = ['.js', '.css', '.txt', '.jpg', '.png', '.gif', '.bmp', '.mp3', '.flv', '.swf', '.pdf',
                       '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.mp4', '.wav', '.wmv', '.rar',
                       '.zip', '.7z', '.iso', '.avi', '.rm', '.rmvb', '.jpeg', '.exe', '.msi', '.ico', '.apk',
                       '.xml', '.dwg']

    def next_url(self):
        url = self.url_list.pop(0)
        self.finish.append(url)
        return url

    def add_url(self, url):
        if url not in self.finish:
            self.url_list.append(url)

    @staticmethod
    def cut_link(link):
        # cut all after '?'
        return link[link.rfind('?') + 1:]

    @staticmethod
    def judge_link(link):
        # save link
        o = link

        # lowercase
        link = link.lower()

        # ignore urls
        if link == '#':
            return Spyder.IGNORE
        elif 'mailto' in link:
            return Spyder.IGNORE

        # cut ?
        link = Spyder.cut_link(link)

        # cut http
        if 'http' in link:
            link = link[8:]

        # reserve the last part
        link = link[link.rfind('/'):]

        # if no suffix
        if '.' not in link:
            return Spyder.HYPERLINK
        # get suffix
        suffix = link[link.rfind('.'):].strip()
        if suffix in Spyder.PAGE_SUFFIX:
            return Spyder.HYPERLINK
        elif suffix in Spyder.RESOURCE_SUFFIX:
            return Spyder.RESOURCE
        else:
            raise Exception(o + ": suffix " + suffix + " not recognized")

    @staticmethod
    def local_dir(url):
        if '//' in url:
            url = url[url.find('//') + 2:]
        parts = url.split('/')
        parts[0] = parts[0].replace('.', '_')

        if '.' not in parts[-1]:
            if parts[-1] == '':
                parts[-1] = 'index.htm'
            else:
                parts.append('index.htm')

        local = os.path.dirname(__file__) + '/docs/' + '/'.join(parts)\
            .replace('?', '')\
            .replace('&', '')\
            .replace(':', '')\
            .replace('=', '')\
            .replace('+', '')
        return local

    @staticmethod
    def download(url):
        local = Spyder.local_dir(url)
        if os.path.isfile(local):
            return
        print('Download: ', url, ' ==> ', local)
        os.makedirs(local[:local.rfind('/')], exist_ok=True)
        urlretrieve(url, local)

    @staticmethod
    def write_html(url, htm):
        local = Spyder.local_dir(url)
        print('Save Page: ', url, ' ==> ', local)
        os.makedirs(local[:local.rfind('/')], exist_ok=True)
        pattern = re.compile(r'charset=(.*?)"', re.IGNORECASE)
        enc = pattern.findall(htm)[0].replace('"', '')
        if enc == '': enc = 'utf-8'
        with open(local, 'w', encoding=enc) as f:
            f.write(htm)

    def process(self, url):
        with urlopen(url) as response:
            html = codecs.decode(response.read())

            def repl(m):
                attr = m.group(1)
                link = m.group(2)

                cat = Spyder.judge_link(link)
                if cat == Spyder.HYPERLINK:
                    if 'http' not in link:
                        link = urljoin(url, link)
                    self.add_url(link)
                elif cat == Spyder.RESOURCE:
                    if 'http' not in link:
                        link = urljoin(url, link)
                    t = threading.Thread(target=Spyder.download, args=(link,))
                    t.daemon = True
                    t.start()
                    # Spyder.download(link)
                else:
                    return  attr + '="' + link + '"'
                return  attr + '="file:///' + Spyder.local_dir(link) + '"'
            res = re.sub(r'(src|href)\s*=\s*"(.*?)"', repl, html)
            t = threading.Thread(target=Spyder.write_html, args=(url, res))
            t.daemon = True
            t.start()
            # Spyder.write_html(url, res)

    def fetch(self):
        while len(self.url_list) > 0:
            try:

                url = self.next_url()
                print("New Page: ", url)
                self.process(url)
            except Exception as e:
                with open('error.log', 'a') as log:
                    log.write(str(e) + '\n\r')
                print(e)


if __name__ == '__main__':
    spyder = Spyder()
    spyder.fetch()
