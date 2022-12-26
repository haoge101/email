from sys import stdout
from typing import Dict, List
import requests
import sys
import re
import time
import json
import datetime
import smtplib
# 发送字符串的邮件
from email.mime.text import MIMEText
# 需要 MIMEMultipart 类
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup


def get_chapter_url_list(book_url: str) -> List[str]:
    """
    根据书籍链接获取全部章节链接列表

    Parameters
    ----------
    book_url : str
        书籍链接

    Returns
    -------
    List[str]
        章节链接列表
    """
    # 匹配章节链接的正则表达式
    href_regex = "<dd><a href='(.*)' >"
    response = requests.get(book_url, headers=headers)
    response.encoding = 'utf-8'
    chapter_href_list = re.findall(href_regex, response.text)
    return [base_url+href for href in chapter_href_list]


def get_chapter_detail(chapter_url: str) -> Dict[str, str]:
    """
    根据章节链接获取章节信息

    Parameters
    ----------
    chapter_url : str
        章节链接

    Returns
    -------
    Dict[str, str]
        章节链接信息
    """
    # 反复尝试获取,直到有正确的信息
    while 1:
        response = requests.get(chapter_url, headers=headers)
        if '503 Service Temporarily Unavailable' not in response.text:
            break
        else:
            print('漏数据了，3 秒之后继续爬')
            time.sleep(3)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    # 查找正文内容
    content = soup.find(attrs={'id': 'content'}).text
    # 标题
    title = soup.find('h1').text
    return {
        'content': content,
        'title': title,
        'url': chapter_url
    }


# 网站链接
base_url = 'http://www.ibiquge.la'
# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
}
# 要采集的最大章节数
max_chapter_count = 10
# 书籍链接
book_url = 'https://www.ibiquge.la/9/9419/'
# 获取章节列表
chapter_url_list = get_chapter_url_list(book_url)
latestChapter = len(chapter_url_list)
with open('chapterdata.json', 'r') as f:
    data = json.load(f)
lastChapter = data['Number']
fileExist=False
if (latestChapter > lastChapter):
    fileExist = True
    chapter_url_list = chapter_url_list[lastChapter - 1:]
    # 存储路径
    file_name = str(datetime.date.today()) + '.txt'
    with open(file_name, 'w', encoding='utf-8') as f:

        for index, chapter_url in enumerate(chapter_url_list, start=1):
            item = get_chapter_detail(chapter_url)
            f.write('标题: '+item['title']+'\n\n')
            #f.write('原文链接: '+item['url']+'\n')
            f.write(item['content']+'\n')
            stdout.write(f'进度:{index}/{len(chapter_url_list)}\r')
    print('生成文件:',file_name)

    latestChapterJson = {
        'Number': latestChapter,
    }
    with open('chapterdata.json', 'w') as f:
        json.dump(latestChapterJson, f)
        
# 设置服务器所需信息
fromEmailAddr = sys.argv[1]  # 邮件发送方邮箱地址
password = sys.argv[2]  # 密码(部分邮箱为授权码)
toEmailAddrs = [sys.argv[1]]  # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发

# 设置email信息
# ---------------------------发送带附件邮件-----------------------------
# 邮件内容设置
message =  MIMEMultipart()
# 邮件主题
message['Subject'] = 'ETA'
# 发送方信息
message['From'] = fromEmailAddr
# 接受方信息
message['To'] = toEmailAddrs[0]
# 邮件正文内容

#股票1
stock1='访问失败'
url = 'http://web.juhe.cn:8080/finance/stock/hs?gid=sh600703&key=9615702e4482efbeac283c4a1d7919cc'   # 目标网站，？wd=后面为参数，可以使用params，不过看起来不舒服
result = requests.get(url)    # 发送请求，将准备好的url与headers参数放入
if result.status_code==200:
    result=json.loads(result.text)
    if result['error_code']==0:
        name=result['result'][0]['data']['name']  #股票名称
        todayStartPri=result['result'][0]['data']['todayStartPri'] #今日开盘价
        nowPri=result['result'][0]['data']['nowPri'] #当前价格
        yestodEndPri=result['result'][0]['data']['yestodEndPri'] #昨日收盘价
        increPer=result['result'][0]['data']['increPer'] #涨跌百分比
        date=result['result'][0]['data']['date'] #日期
        time=result['result'][0]['data']['time'] #时间
        stock1 = '时间： %s %s\n股票名称： %s\n昨日收盘价： %s\n今日开盘价： %s\n当前价格： %s\n涨跌百分比： %s%%'%(date, time, name, yestodEndPri, todayStartPri, nowPri, increPer)

#A股行情
stock='访问失败'
url = 'http://web.juhe.cn:8080/finance/stock/hs?gid=0&key=9615702e4482efbeac283c4a1d7919cc&type=0'
result = requests.get(url)    # 发送请求，将准备好的url与headers参数放入
if result.status_code==200:
    result=json.loads(result.text)
    if result['error_code']==0:
        name=result['result']['name']  #A股
        increPer=result['result']['increPer'] #涨跌百分比
        nowpri=result['result']['nowpri'] #当前价格
        yesPri=result['result']['yesPri'] #昨收
        time=result['result']['time'] #日期时间
        stock = '时间： %s\n名称： %s\n昨收： %s\n当前价格： %s\n涨跌百分比： %s%%'%(time, name, yesPri, nowpri, increPer)

#美金汇率
exchangerate='访问失败'
url = 'http://op.juhe.cn/onebox/exchange/query?key=19d529117f0981090cb5ba2fb37fd8ba'
result = requests.get(url)    # 发送请求，将准备好的url与headers参数放入
if result.status_code==200:
    result=json.loads(result.text)
    if result['error_code']==0:
        for x in result['result']['list']:
            if x[0]=='美元':
        
                name=x[0]  #美元
                Per=x[2] #现汇买入价
                centralrate=x[5] #中间价
                time=result['result']['update'] #日期时间
                exchangerate = '时间： %s\n名称： %s\n现汇买入价： %s元\n中间价： %s元'%(time, name, float(Per)/100, float(centralrate)/100)

message.attach(MIMEText(stock + '\n\n' + stock1 + '\n\n' +  exchangerate, 'plain', 'utf-8'))

#每日要闻
content=''
url = 'https://www.mxnzp.com/api/news/list?typeId=518&page=1&app_id=pvljeormloijom82&app_secret=RHlncVEzd2FBVjM5d2dESDJ1ZXEwZz09'   # 目标网站，？wd=后面为参数，可以使用params，不过看起来不舒服
result = requests.get(url)    # 发送请求，将准备好的url与headers参数放入
if result.status_code==200:
    result=json.loads(result.text)
    # print(len(result['data']))
    for x in result['data']:
        newsId=x['newsId']
        count=0
        code=0
        while (code!=1 and count<15):
            url = 'https://www.mxnzp.com/api/news/details?newsId=%s&app_id=pvljeormloijom82&app_secret=RHlncVEzd2FBVjM5d2dESDJ1ZXEwZz09'%(newsId)
            result = requests.get(url)    # 发送请求，将准备好的url与headers参数放入
            result=json.loads(result.text)
            code=int(result['code'])
            count+=1
            # print(code)
            # print(count)
        if code==1:
            content=content +'\n\n&nbsp&nbsp&nbsp=====================&nbsp&nbsp\n\n\n\n' + result['data']['content'] 
        
content='<html><head><meta charset="UTF-8"></head><body>' + content + '</body></html>'

if content:
    # 构造附件
    att2 = MIMEText(content, 'base64', 'utf-8')
    att2['Content-type'] = 'application/octet-stream'
    att2['Content-Disposition'] = 'attachment; filename="news.html"'
    message.attach(att2)   

if fileExist:
    # 构造附件
    att1 = MIMEText(open(file_name, 'rb').read(), 'base64', 'utf-8')
    att1['Content-type'] = 'application/octet-stream'
    att1['Content-Disposition'] = 'attachment; filename="test.txt"'
    message.attach(att1)
    # ---------------------------------------------------------------------

# 登录并发送邮件
try:
    server = smtplib.SMTP('smtp.263.net')  # 163邮箱服务器地址，端口默认为25
    server.login(fromEmailAddr, password)
    server.sendmail(fromEmailAddr, toEmailAddrs, message.as_string())
    print('success')
    server.quit()
except smtplib.SMTPException as e:
    print("error:", e)
