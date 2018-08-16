# -*- coding: utf-8 -*-
# @Time    : 2018/8/16 11:52
# @Author  : ronething
# @FileName: zhihucollection.py
# @Software: PyCharm
# @Github  : https://github.com/ronething

import time
import re
import os
import requests
import re
from bs4 import BeautifulSoup
from multiprocessing import Pool

"""
获取收藏夹最大页数
"""

def getMaxUrl(target_url):
    print(target_url)
    html = requests.get(target_url, headers=headers).text
    soup = BeautifulSoup(html, 'lxml')
    page_soup = soup.find_all('a', href=re.compile(r'\?page=\d+'))
    print(page_soup)
    # 如果 page_soup 为空 说明只有一页
    if not page_soup:
        return 1
    page_digit = set()
    for page in page_soup:
        test = page.get_text()
        if test.isdigit():
            page_digit.add(int(test)) # 转为 int 类型 不然字符串 '24' 比 '3' 就小了
    max_page = max(page_digit)

    return max_page


def get_list():
    article_dict = {}
    page = 1
    while True:
        url = 'https://www.zhihu.com/collection/{0}?page={1}'.format(collection, str(page))
        print(url)
        html = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        page_soup = soup.find("div", {"id": "zh-list-collection-wrap"})
        for i in page_soup.findAll("div", {"class", "zm-item"}):
            title = i.h2.a.get_text()
            try:
                topicUrl = i.find("a", {"class": "toggle-expand"}).get('href')
            except:
                print("get url error")
                continue
            if (topicUrl[0] == '/'):
                topicUrl = "https://www.zhihu.com" + topicUrl
            print(title, topicUrl)
            akeys = article_dict.keys()
            if topicUrl not in akeys:
                article_dict[topicUrl] = title
        time.sleep(3)
        page += 1
        if page > max_page:
            break
    with open('zhihu_ids.txt', 'w', encoding='utf-8') as f:
        items = sorted(article_dict.items())
        for item in items:
            f.write('%s %s\n' % item)


def get_html(url):
    title = re.sub('[\/:*?"<>|]', '-', url[1])  # 正则过滤非法文件字符
    file_name = '%03d. %s.html' % (url[2], title)
    if os.path.exists(file_name):
        print(title, 'already exists.')
        return
    else:
        print('saving', title)
    html = requests.get(url[0], headers=url[3]).text
    soup = BeautifulSoup(html, 'lxml')
    pattern = re.compile(r'https://zhuanlan.zhihu.com/.*?')  # 通过正则判断是专栏还是问题
    if pattern.match(url[0]):
        try:
            content = soup.find("div", {"class": "Post-RichText"}).prettify()
        except:
            print("saving", title, "error")
            return
    else:
        try:
            content = soup.find("div", {"class": "RichContent-inner"}).prettify()
        except:
            print("saving", title, "error")
            return
    content = content.replace('data-actual', '')
    content = content.replace('h1>', 'h2>')
    content = re.sub(r'<noscript>.*?</noscript>', '', content)
    content = re.sub(r'src="data:image.*?"', '', content)
    content = '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><h1>%s</h1>%s</body></html>' % (
        title, content)
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(content)
    time.sleep(3)


def get_details():
    detailList = []
    with open('zhihu_ids.txt', 'r', encoding='utf-8') as f:
        i = 1
        for line in f:
            lst = line.strip().split(' ')
            url = lst[0]
            title = '_'.join(lst[1:])
            detailList.append((url,title,i,headers))
            i += 1
    return detailList


def get_args():
    print('exporting PDF...')
    htmls = ""
    htmlsList = []
    count = 1
    for root, dirs, files in os.walk('.'):
        for name in files:
            if name.endswith(".html"):
                htmls += '"' + name + '"' + " "
                count += 1
                # 每 50 个问题生成一个 pdf 文件
                if count % 50 == 0:
                    htmlsList.append(htmls)
                    htmls = ""
    if htmls:
        htmlsList.append(htmls)
    print(htmlsList)
    return htmlsList

def to_pdf():
    pdfArgs = get_args()
    flag = 0
    for i in pdfArgs:
        filename = collection + "_" + str(flag) + ".pdf"
        if os.path.exists(filename):
            print(filename, 'already exists.')
            flag += 1
            continue
        pdfEnd = 'wkhtmltopdf ' + i + filename
        if (os.system(pdfEnd) == 0):
            print("exporting PDF success")
        else:
            print("exporting PDF failed")
        flag += 1
    print("done")

"""
删除目录中的html文件
"""
def remove_html():
    pattern = re.compile(r'.*\.html$')
    for root, dirs, files in os.walk('.'):
        for name in files:
            if os.path.exists(root + "\\" + name):
                if pattern.match(name):
                    os.remove(root + "\\" + name)
                    print("remove",name,"done")


if __name__ == '__main__':
    pool = Pool(processes=10) # 进程池
    collection = input('Please input collection id:(default 45804384)')
    if not collection:
        collection = '45804384'
    headers = {
        'referer': 'https://www.zhihu.com/collection/{0}'.format(collection),
        'User-Agent': 'Mozilla/5.0',
        'cookie': '' # 按需填写
    }
    max_page = getMaxUrl("https://www.zhihu.com/collection/{0}".format(collection))
    print("最大页码:",max_page)
    get_list()
    s1 = time.time()
    pool.map(get_html,get_details())
    pool.close()
    pool.join()
    print("time used ",int(time.time()-s1))
    to_pdf()
    remove_html()
