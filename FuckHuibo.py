import requests
from prettytable import PrettyTable
import json
import sys
from MagicGoogle import MagicGoogle
import multiprocessing
import time
import random
import os
import getopt

headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'
}

errorlist = []
def FuckHuibo(name,username,number,page):
    '''
    获得慧博中的内容
    :param name: 公司名，如瑞声科技
    :param username: 用户在慧博的ID
    :param number: 搜索多少份研报
    :param page: 过滤小于一定页数的研报
    :return: 返回Huibo中的内容列表
    '''
    url_1 = 'http://newsmag.hibor.com.cn/MobilePhone/SelectJsonHandler.ashx'
    url_2 = 'http://newsmag.hibor.com.cn/MobilePhone/DocDetailHandler.ashx'
    data = {
    'systype':'android',
    'x':1,
    'btype':1,
    'stype':0,
    'count':number,
    'page':1,
    'reportrange':1,
    'keyword':name,
    'timerange':5,
    'username':username
    }
    data2 = {
        'systype':'android',
        'btype':1,
        # 用户名
        'username':username,
        # 慧博pdf文件id
        'id':'2225354'
    }

    r = requests.get(url_1, data=data, headers=headers)
    if r.status_code != 200:
        print('获得{}失败'.format(name))
        sys.exit()
    data_list = json.loads(r.text).get('data',{}).get('list',[])
    showlist = []
    for d in data_list:
        id = d.get('id','')
        title = ''.join(d.get('title','').split('-')[:-1])
        time = d.get('time','').split(' ')[0]
        grade = d.get('grade','')
        data2['id'] = id
        r2 = requests.get(url_2, data=data2, headers=headers)
        if r2.status_code != 200:
            print('获得{}失败'.format(name))
            sys.exit()
        data_d = json.loads(r2.text).get('data', {})
        author = data_d.get('author','')
        filepages = data_d.get('filepages','')
        if int(filepages) > page:
            showlist.append([title,filepages,author,grade,time])

    col = PrettyTable()
    col.field_names = (['文件名称','页数','作者','方向','发布时间'])
    for show in showlist:
        col.add_row(show)
    print(col)
    return showlist

def PDFDownloader(url,filename,path):
    '''
    下载PDF
    '''
    if url:
        downurl = url[0]
        # 确认模式，不然下载会失败
        if 'http' not in downurl:
            downurl = 'http://'+downurl
        r =requests.get(downurl, headers)
        # pdf为二进制，以下方法写入
        with open(path+'/'+filename+'.pdf','wb') as f:
            for data in r.iter_content():
                f.write(data)

def PDFUrlGeter(filename):
    '''
    通过Google查重filename文件，获得其url
    :return: url列表
    '''
    try:
        mg = MagicGoogle()
        urls = mg.search_url(query=filename+'filetype:pdf')
        u = [i for i in urls]
        if u:
            return u
        time.sleep(random.randint(1, 5))
        urls = mg.search_url(query=filename + 'inurl:pdf')
        u = [i for i in urls]
        if u:
            return u
        time.sleep(random.randint(1, 5))
        urls = mg.search_url(query=filename)
        u = [i for i in urls if 'pdf' in i]
        return u
    except:
        errorlist.append(filename)
        return []


def LoginHuibo(username,pw):
    '''
    模拟登录
    :param username: 用户名
    :param pw: 密码
    :return:
    '''
    headers = {
        'If-Modified-Since': 'Tue, 06 Mar 2018 06:56:07 GMT+00:00',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.1; ONEPLUS A3010 Build/NMF26F)',
        'Host': 'newsmag.hibor.com.cn',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'Content-Length': '61'
    }
    data = {
        'versionnum': '317',
        'username': username,
        'action': 'login',
        'pw': pw
    }

    url = 'http://newsmag.hibor.com.cn/MobilePhone/GetJsonHandler.ashx?systype=android'
    r = requests.post(url, headers=headers, data=data)
    if r.status_code != 200:
        print('登录失败，请检查用户名和密码是否正确')
        sys.exit()
    logindict = json.loads(r.text).get('data', {})
    # 获得慧博的
    un= logindict.get('username', '')
    type = logindict.get('type', -1)
    if not type:
        print('登录失败，请检查用户名和密码是否正确')
        sys.exit()
    return un

def GetParameter():
    try:
        # 参数命令的含义依次为：帮助，用户名，密码，公司中文，下载文件保存地址，查找多少研报，研报页数
        options, args = getopt.getopt(sys.argv[1:], "hu:p:c:o:N:P:", ["help", "username=", "password=","company=","output=",'number=','page='])
    except getopt.GetoptError:
        print('输入错误')
        sys.exit()
    username = ''
    password = ''
    company = ''
    output = ''
    number = ''
    page = ''
    for name, value in options:
        if name in ("-h", "--help"):
            help = '''
            最简单命令：python FuckHuibo.py -u 你的账号 -p 你的密码 -c 公司中文名称
            最简单命令默认查找20份研报，下载保存到当前目录
            你可以指定查找研报的数量(不可超过50份)和指定目录
            python FuckHuibo.py -u 账号 -p 密码 -c 公司名 -o 路径 -N 份数
            python FuckHuibo.py -u xxx -p xxx -c '瑞声科技' -o '.' -N 50

            参数解释：
            -u 账号
            -p 密码
            -c 公司中文名
            -o 研报保存路径
            -N 搜索研报的份数，会一次性搜索出多少研报
            -P 限制下载研报的页数，研报必须大于这个页数才能被下载
            '''
            print(help)
            sys.exit()
        if name in ("-u", "--username"):
            username = value
        if name in ("-p", "--password"):
            password = value
        if name in ("-c", "--company"):
            company = value
        if name in ("-o", "--output"):
            output = value
        if name in ("-N", "--number"):
            number = value
        if name in ("-P", "--page"):
            page = value
    if username=='' or password=='' or company=='':
        print('必须输入用户名、密码、公司名')
        sys.exit()
    return username, password, company, output, number,page

if __name__=='__main__':

    username, pw, company, output, number,page = GetParameter()
    # username, pw, company, output, number, page = '13229483208','bohui137','瑞声科技','./ayupdf',10,50
    if not output:
        output = '.'
    if not number:
        number = 20
    if int(number) > 50:
        number = 50
    if not page:
        page = 1
    if not os.path.exists(output):
        os.makedirs(output)
    username = LoginHuibo(username,pw)
    filelist = FuckHuibo(company,username,int(number),int(page))
    filedict = {}
    for file in filelist:
        title = file[0]
        print('获取--》',title)
        urls = PDFUrlGeter(title)
        filedict[title] = urls[:1]
        time.sleep(random.randint(1, 10))
    # 多进程下载
    multiprocessing.freeze_support()
    cpus = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(cpus)
    for fn,url in filedict.items():
        fk = fn
        uu = url
        pool.apply_async(PDFDownloader, args=(url, fn, output))
    print('开始下载...')
    pool.close()
    pool.join()
    print('下载完成')

    print('下载失败的文件有：')
    for i in errorlist:
        print(i,'\n')
