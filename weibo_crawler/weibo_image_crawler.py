# coding: utf-8
import urllib
import urllib2
import cookielib
import base64
import re
import json
import rsa
import binascii
import threading
import time


# preprocess
def preprocess_base_url_1and2(base_url):
    """return [(serial num of comic, url of comics) ...]"""
    # 第2集：<a href=\"http:\/\/www.weibo.com\/2241275235\/BnLlS7xME\"
    # 第100集：<a href=\"http:\/\/www.weibo.com\/2241275235\/Bxlh9cZMO\"
    url_page = urllib2.urlopen(base_url).read()
    pattern = re.compile(r'第(\d{1,3})集：<a href=\\"http:\\/\\/www.weibo.com\\/2241275235\\/(\w{9})\\"+')
    return pattern.findall(url_page)


def preprocess_base_url3(base_url):
    """return [(serial num of comic, url of comics) ...]"""
    # 第201集 &nbsp;<a href=\"http:\/\/weibo.com\/2241275235\/BFeIgdNWq\"
    url_page = urllib2.urlopen(base_url).read()
    pattern = re.compile(r'第(\d{3})集 &nbsp;<a href=\\"http:\\/\\/weibo.com\\/2241275235\\/(\w{9})\\"+')
    return pattern.findall(url_page)


# crawler logins when initialed
class crawler(object):
    global basedir
    basedir = '/home/phoenix/Downloads/zhaoshi/'

    def __init__(self, username, pwd):
        self.username = username
        self.pwd = pwd
        self.initial_cookie()
        self.login()

    def initial_cookie(self):
        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)

    def login(self):
        postdata={
           'cdult': '3',
           'entry': 'account',
           'gateway': '1',
           'from': '',
           "savestate": '30',
           'userticket': '0',
           'pagerefer': '',
           'geteway': '1',
           'rsakv': '1330428213',
           'prelt': '317',
           'su': '',
           'service': 'sso',
           'servertime': '',
           'nonce': '',
           'pwencode': 'rsa2',
           'sp': '',
           'encoding': 'UTF-8',
           'domain': 'sina.com.cn',
           'returntype': 'TEXT',
           'vsnf': '1'
        }
        url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.3.18)'
        try:
            servertime, nonce = self.get_servertime()
            # print servertime,nonce
        except Exception, e:
            print 'call get_servertime() error'
            print e.message
            return None

        postdata['servertime'] = servertime
        postdata['nonce'] = nonce
        postdata['su'] = self.get_user(self.username)
        postdata['sp'] = self.get_pwsd(self.pwd, servertime, nonce)
        postdata = urllib.urlencode(postdata)

        headers = {'User-Agent':'Mozilla/5.0 (X11;Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0'}
        req = urllib2.Request(
            url=url,
            data=postdata,
            headers=headers
            )
        result = urllib2.urlopen(req)
        text = result.read()
        # print text
        dic = json.loads(text)
        # print dic
        # print dic['crossDomainUrlList'][0]
        # print dic['crossDomainUrlList'][1]
        # p =re.compile('location\.replace\"(.∗?)\"')

        try:
            # login_url=p.search(text).group(1)
            login_url = dic['crossDomainUrlList'][0]
            urll = urllib2.urlopen(login_url).read()
            # for index, cookie in enumerate(cj):
            #    print '[',index, ']',cookie;
            urll2 = urllib2.urlopen(dic['crossDomainUrlList'][1]).read()
            print "login succesfully!", urll
            print urll2

        except Exception, e:
            print'Login error!'
            print e.message
            return None

    @staticmethod
    def get_servertime():
        url = 'http://login.sina.com.cn/sso/prelogin.php?' \
               'entry=weibo&callback=sinaSSOController.preloginCallBack&' \
               'su=dW5kZWZpbmVk&client=ssologin.js(v1.3.18)%lih211@sina.com'

        data = urllib2.urlopen(url).read()
        p = re.compile('(sinaSSOController\.preloginCallBack\()(\S.*)(\))')

        try:
            json_data = p.search(data).group(2)
            # print json_data
            data = json.loads(json_data)
            servertime = str(data['servertime'])
            nonce = str(data['nonce'])
            return servertime, nonce
        except Exception, e:
            print'get servertime error'
            print e.message
            return None

    @staticmethod
    def get_pwsd(pwd, servertime, nonce):
        # pwd1=hashlib.sha1(pwd).hexdigest()
        # pwd2=hashlib.sha1(pwd1).hexdigest()
        # pwd3_ =""+pwd2 + servertime +nonce
        # pwd3=hashlib.sha1(pwd3_).hexdigest()
        # return pwd3

        pubkey = 'EB2A38568661887FA180BDDB5CABD5F21C7BFD59C090CB' \
                 '2D245A87AC253062882729293E5506350508E7F9AA3BB77F43' \
                 '33231490F915F6D63C55FE2F08A49B353F444AD3993CACC02DB78' \
                 '4ABBB8E42A9B1BBFFFB38BE18D78E87A0E41B9B8F73A928EE0CCEE1F6' \
                 '739884B9777E4FE9E88A1BBE495927AC4A799B3181D6442443'
        rsaPublickey = int(pubkey, 16)
        pub_key = rsa.PublicKey(rsaPublickey, int('10001', 16))
        pwd = '%s\t%s\n%s' % (servertime, nonce, pwd)
        pwd1 = rsa.encrypt(pwd, pub_key)
        pwd1 = binascii.b2a_hex(pwd1)
        return pwd1

    @staticmethod
    def get_user(username):
        username1 = urllib.quote(username)
        username = base64.encodestring(username1)[:-1]
        return username

    def run(self, information):
        if len(information) != 2:
            print 'expected tuple with serial number and image index'
            raise ValueError
        name, url = information[0], 'http://weibo.com/2241275235/'+information[1]
        second_page = urllib2.urlopen(url, timeout=20).read()
        # http://ww3.sinaimg.cn/bmiddle/85972563tw1eo6ufzo6qcj20egc6mhdt.jpg
        # pic_id=85972563tw1eo6ufzo6qcj20egc6mhdt
        pattern = re.compile(r'pic_id=(\w*)\\')
        path = basedir+name
        result = pattern.findall(second_page)
        print result
        if result is not None:
            for index, child_url in enumerate(result):
                picture_name = path+'('+str(index)+').jpg'
                child_url = 'http://ww3.sinaimg.cn/bmiddle/'+child_url
                picture = urllib2.urlopen(child_url, timeout=20)
                try:
                    with open(picture_name, 'wb') as pic:
                        pic.write(picture.read())
                except Exception, e:
                    print e.message
                print picture_name+' saved!!!'
        else:
            return
        time.sleep(30)


# thread
class thread_crawler(threading.Thread):
    def __init__(self, interval, crawler, information):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False
        self.crawler = crawler
        self.aim_information = information

    def run(self):
        self.crawler.run(self.aim_information)
        time.sleep(self.interval)

    def stop(self):
        self.thread_stop = True


if __name__ == '__main__':
    cm = crawler('jason0916phoenix@126.com', 'chenminghaolihai')
    base_information = preprocess_base_url3('http://weibo.com/p/1001603834417519974398')
    base_information += preprocess_base_url_1and2('http://weibo.com/p/1001603779662672207251')
    base_information += preprocess_base_url_1and2('http://weibo.com/p/1001603801594557773224')
    print base_information
    """
    for i in range(0, len(base_information), 2):
        a = thread_crawler(10, cm, base_information[i])
        b = thread_crawler(10, cm, base_information[i+1])
        a.start()
        b.start()
    """
    for information in base_information:
        cm.run(information)
