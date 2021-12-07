from bs4 import BeautifulSoup
import requests
import time
import csv, codecs, sys
import os
from dingtalkchatbot.chatbot import DingtalkChatbot
import json

"""
for Dingtalk Chatbot
"""
config = None
DingtalkBotToken = None
DingtalkBotSecret = None

def SendDingtalkMsg(msg):
    webhook = 'https://oapi.dingtalk.com/robot/send?access_token=' + DingtalkBotToken
    secret = DingtalkBotSecret  # 可选：创建机器人勾选“加签”选项时使用
    # 初始化机器人
    #dingbot = DingtalkChatbot(webhook)  # 方式一：通常初始化方式
    dingbot = DingtalkChatbot(webhook, secret=secret)  # 方式二：勾选“加签”选项时使用（v1.5以上新功能）
    #dingbot = DingtalkChatbot(webhook, pc_slide=True)  # 方式三：设置消息链接在PC端侧边栏打开（v1.5以上新功能）
    # Text消息@所有人
    dingbot.send_text(msg=msg, is_at_all=True)


def GetBOCMRateHeader(currency, debug=0):
    BOCMRateHeader = {
        'Host': 'www.bankofchina.com',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': "Windows",
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Dest': 'iframe',
        'Referer': 'https://www.bankofchina.com/mo/index.html',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    if currency == 0 : # MOP
        BOCMRateHeader['Referer'] = 'https://www.bankofchina.com/mo/fimarkets/fm1/200912/t20091219_933600.html'
        if debug : print("[Debug] MOP in Get BOCM Rate Header!")
    elif currency == 1: # HKD
        BOCMRateHeader['Referer'] = 'https://www.bankofchina.com/mo/fimarkets/fm1/200912/t20091219_933601.html'
        if debug : print("[Debug] HKD in Get BOCM Rate Header!")
    return BOCMRateHeader

def GetBOCMRate(currency, debug):
    """
    Initialing
    """
    BOCMMopRateUrl= 'https://www.bankofchina.com/mo/ftpdata/2009p6.htm'
    # BOCMMopRateHeader = GetBOCMRateHeader(currency=0)
    BOCMHKDRateUrl= 'https://www.bankofchina.com/mo/ftpdata/2009p1.htm'
    # BOCMHKDRateHeader = GetBOCMRateHeader(currency=1)

    RateDatas = []
    res = requests
    try:
        if(currency == 0):
            res = requests.get(BOCMMopRateUrl, headers=GetBOCMRateHeader(currency=0), timeout=10)
        elif(currency == 1):
            res = requests.get(BOCMHKDRateUrl, headers=GetBOCMRateHeader(currency=1), timeout=10)
    except requests.exceptions.RequestException as e:
        print(e)
        SendDingtalkMsg("[ERROR] Network Error in requests!\n"+e)
        raise

    #if debug : print(res.content.decode('UTF-8'))

    """
    Working
    """
    page = BeautifulSoup(res.content.decode('UTF-8'),'html.parser')
    tables = page.find_all('table')
    if debug : print(tables[0])
    rows = tables[0].find_all('tr')
    # reduce if in for-loop, handle title fisrtly
    datas = rows[0].find_all('th')
    needDataIndexs = []
    tmpDataRow = []
    for i in range(0, len(datas)):
        data = datas[i].contents[0]
        if data == "票匯":
            continue
        #print(len(datas[i]))
        if len(datas[i]) > 1:
            data += str(datas[i].contents[2])
        needDataIndexs.append(i)
        tmpDataRow.append(data)
    RateDatas.append(tmpDataRow)
    for i in range(1, len(rows)):
        datas = rows[i].find_all('td')
        tmpDataRow = []
        for j in needDataIndexs:
            tmpDataRow.append(''.join(datas[j].contents[0]))
        #print(tmpDataRow)
        RateDatas.append(tmpDataRow)

    #print('finish')
    if debug : print(RateDatas)
    tmp = page.find('body').contents[0]
    lastUpdateTime = str(tmp).split(':', 1).pop().strip().replace('/', '-').split(' ')
    #print(lastUpdateTime)
    outputFile(RateDatas, lastUpdateTime, currency)
    return 0
    
def makeDir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def outputFile(RateDatas, datetime, currency):
    date = time.strftime('%Y-%m-%d', time.localtime())
    outputPath = 'RateDatas'
    makeDir(outputPath)
    nowPath = outputPath
    if(currency == 0):
        nowPath = outputPath + "/BOCMMOPRate"
    elif(currency == 1):
        nowPath = outputPath + "/BOCMHKDRate"
    makeDir(nowPath)
    nowPath += "/" + datetime[0]
    makeDir(nowPath)
    writeListToCSV(RateDatas, filename=datetime[1], path=nowPath)

def writeListToCSV(list, filename='unname.csv', path='output/', encoding='utf_8', replace=False):
    pathName = path + ("" if (path[len(path)-1] == "/" or filename[0] == "/") else "/") + filename
    f = codecs.open(pathName , 'w' if replace else 'a', encoding=encoding)
    writer = csv.writer(f)
    try:
        for row in list:
            writer.writerow(row)
    except csv.Error as e:
        sys.exit('file {}, line {}: {}'.format(pathName, writer.line_num, e))
        SendDingtalkMsg("file"+  pathName +" line " + writer.line_nu + " " + e)
    except:
        print("[ERROR] Unexpected error:", sys.exc_info()[0])
        SendDingtalkMsg("[ERROR] Unexpected error:"+sys.exc_info()[0])
        raise
    



if __name__ == "__main__":
    with open("BOCMRateBot.json") as config_file:
        config = json.loads(config_file.read())
        DingtalkBotToken = config['token']
        if(DingtalkBotToken == 'token_here' or DingtalkBotToken == ""):
            print("Token is not set")
            exit(0)
        DingtalkBotSecret = config['secret']
        if(DingtalkBotSecret == 'secret_here' or DingtalkBotSecret == ""):
            print("Secret is not set")
            exit(0)
    if not GetBOCMRate(currency=0, debug=0):
        print("Get BOCM MOP Rate Data successed!")
    else:
        print("ERROR in Get BOCM MOP Rate!")
        SendDingtalkMsg("[ERROR] Get BOCM MOP Rate Fail!\n")
    if not GetBOCMRate(currency=1, debug=0):
        print("Get BOCM HKD Rate Data successed!")
    else:
        print("ERROR in Get BOCM HKD Rate!")
        SendDingtalkMsg("[ERROR] Get BOCM HKD Rate Fail!\n")