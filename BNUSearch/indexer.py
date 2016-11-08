import jieba
import json
from urllib.request import *
from urllib.parse import *
import re
import codecs
from html.parser import HTMLParser
import threading


class Spyder:
    url_list = ['http://www.bnu.edu.cn']
    finish = []
    indices = {}
    size = None

    HYPERLINK = 'hyperlink'
    RESOURCE = 'resource'
    IGNORE = '#'
    PAGE_SUFFIX = ['.htm', '.html', '.php', '.asp', '.aspx', '.jsp', '.cgi', '.jspx', '.shtml', '.jspa',
                   '.action', '.do', '.jhtml']
    RESOURCE_SUFFIX = ['.js', '.css', '.txt', '.jpg', '.png', '.gif', '.bmp', '.mp3', '.flv', '.swf', '.pdf',
                   '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.mp4', '.wav', '.wmv', '.rar',
                   '.zip', '.7z', '.iso', '.avi', '.rm', '.rmvb', '.jpeg', '.exe', '.msi', '.ico', '.apk',
                   '.xml', '.dwg']

    def __init__(self):
        self.lock = threading.Lock()
        self.t = None
        self.cur = 0
        with open('vis', 'r') as f:
            vis = json.load(f)
            print(vis)
            self.finish = vis['f']
            self.url_list = vis['u']
            self.size = threading.Semaphore(len(self.url_list))

    def next_url(self):
        if threading.active_count() == 0 and len(self.url_list) == 0:
            return ''
        self.size.acquire()
        url = self.url_list.pop()
        self.finish.append(url)
        return url

    def add_url(self, url):
        if url not in self.finish and url not in self.url_list and 'bnu' in url:
            self.url_list.append(url)
            self.size.release()

    @staticmethod
    def cut_link(link):
        # cut all after '?' '#'
        link = link[link.rfind('?') + 1:]
        return link[link.rfind('#') + 1:]

    @staticmethod
    def judge_link(link):
        # save link
        o = link

        # lowercase
        link = link.lower()

        if 'javascript' in link:
            return Spyder.IGNORE

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

    def parse_html(self, url, html):

        class XParser(HTMLParser):

            def error(self, message):
                with open('error.log', 'a') as log:
                    log.write(str(message) + '\n\r')
                    print(message)

            def __init__(self):
                super().__init__()
                self.words = {}
                self.count = 0

            def handle_starttag(self, tag, attrs):
                pass

            def handle_endtag(self, tag):
                pass

            def handle_data(self, data):
                wds = jieba.cut_for_search(data)
                for w in wds:
                    if w.isdigit():
                        continue
                    self.count += 1
                    if w in self.words:
                        self.words[w] += 1
                    else:
                        self.words[w] = 1

        try:
            parser = XParser()
            parser.feed(html)
            self.lock.acquire()
            for w in parser.words:
                if parser.words[w] > parser.count * 0.8:
                    continue
                if w in self.indices:
                    self.indices[w].append((parser.words[w], url))
                else:
                    self.indices[w] = [(parser.words[w], url)]
            self.lock.release()
        except Exception as e:
            with open('error.log', 'a') as log:
                log.write(url + ":   " + str(e) + '\n\r')
            print(e)

    def process(self, url):
        try:
            with urlopen(url, timeout=8) as response:
                type = dict(response.getheaders())['Content-Type']
                i = type.find('charset=')
                charset = 'utf-8'
                if i != -1:
                    charset = type[i+8:]
                html = codecs.decode(response.read(), encoding=charset)

                res = re.findall(r'(?:src|href)\s*=\s*"(.*?)"', html)
                for u in res:
                    try:
                        cat = Spyder.judge_link(u)
                        if cat == Spyder.HYPERLINK:
                            if 'http' not in u:
                                u = urljoin(url, u)
                            self.add_url(u)
                    except Exception as e:
                        with open('error.log', 'a') as log:
                            log.write(str(e) + '\n\r')
                            print(e)
                self.parse_html(url, html)
        except Exception as e:
            with open('error.log', 'a') as log:
                log.write(url + ":   " + str(e) + '\n\r')
            print(e)
                

    def save_indices(self):
        self.t = threading.Timer(600, self.save_indices)
        self.t.start()
        if len(self.indices) < 50:
            return
        self.cur += 1
        self.lock.acquire()
        with open('indices' + str(self.cur), 'w') as f:
            json.dump(self.indices, f)
            print("Indices Auto Saved")
        with open('vis', 'w') as f:
            json.dump({'f': self.finish, 'u': self.url_list}, f)
            print("Progress Auto Saved")
        self.indices = {}
        self.lock.release()

    def fetch(self):
        maxconn = 10
        self.save_indices()
        threads = []
        while True:
            try:
                if len(threads) > 30:
                    threads[0].join(10)
                    del threads[0]
                url = self.next_url()
                if url == '':
                    break
                print("New Page: ", url)
                t = threading.Thread(target=self.process, args=(url,))
                t.daemon = True
                t.start()
                threads.append(t)
                #self.process(url)
            except Exception as e:
                if threads:
                    threads[0].join(10)
                    del threads[0]
                else:
                    with open('error.log', 'a') as log:
                        log.write(str(e) + '\n\r')
                    print(e)
        self.t.cancel()
        self.save_indices()
        print("OK")

if __name__ == '__main__':
    spyder = Spyder()
    spyder.fetch()
