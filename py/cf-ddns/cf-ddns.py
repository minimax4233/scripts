#! /usr/bin python3
import requests
import json
import CloudFlare
import time
import logging
from logging.handlers import RotatingFileHandler

DEBUG = False

# 設定 logging 等級
logging.basicConfig(filename='ddns.log', level=logging.DEBUG)

# 創建 logger 物件
logger = logging.getLogger()

# 設定輸出格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


# 創建 RotatingFileHandler 對象，設置日誌文件名和大小，以及保留日誌文件的數量
handler = RotatingFileHandler(
    filename="ddns.log",
    maxBytes=104857600,  # 100MB
    backupCount=5
)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

# 將 RotatingFileHandler 添加到日誌處理器中
logger = logging.getLogger()
logger.addHandler(handler)

if __name__ == '__main__':
    
    with open('cf-ddns.json') as config_file:
        config = json.loads(config_file.read())
    token = config['api_token']
    dnames = config['domain_names']
    if(token == 'your_api_token' or token == ''):
        print('Token is not set!')
        exit(0)
    if(len(dnames) == 0 or dnames[0] == 'your_domain_name1' or dnames[1] == 'your_domain_name2'):
        print('Domain Names is not set!')
        exit(0)
    logger.debug(f'token:{token}, dnames:{dnames}')
    if DEBUG: print(f'token:{token}, dnames:{dnames}')
    cf = CloudFlare.CloudFlare(token=token)
    zones = cf.zones.get()
    for zone in zones:
        zone_id = zone['id']
        zone_name = zone['name']
        logger.debug(f'zoneid:{zone_id},\n name:{zone_name}')
        if DEBUG: print(zone_id, zone_name)
    for dname in dnames:
        cf_dns_records = cf.zones.dns_records.get(zone_id, params={'name':dname + '.' + zone_name})
        cf_ipv4 = ''
        if(len(cf_dns_records) != 0):
            cf_ipv4 = cf_dns_records[0]['content']
        logger.debug(f'{dname} cf_ipv4:'+ cf_ipv4)
        if DEBUG: print(f'{dname} cf_ipv4:'+ cf_ipv4)
        try:
            ipv4 = requests.get('https://1.1.1.1/cdn-cgi/trace').text.split('\n')
            ipv4.pop()
            ipv4 = dict(s.split('=') for s in ipv4)['ip']
        except Exception:
            logger.error(f'Get {dname} ipv4 Fail!')
            #print(f'Get {dname} ipv4 Fail!')
            exit(-1)

        if DEBUG: print('ipv4:'+ipv4)
        if(ipv4 != cf_ipv4):
            dns_new_records = {'name':dname, 'type':'A', 'content':ipv4}
            #r = cf.zones.dns_records.delete(zone_id, cf_dns_records[0]['id'])
            dns_records = cf.zones.dns_records.get(zone_id, params={'name':dname + '.' + zone_name})
            for dns_record in dns_records:
                dns_record_id = dns_record['id']
                r = cf.zones.dns_records.delete(zone_id, dns_record_id)
            r = cf.zones.dns_records.post(zone_id, data=dns_new_records)
            logger.info(f'{dname} IP updated successfully!')
            #print(f'{dname} IP updated successfully!')
            if DEBUG == False:
                exit(0)
            if DEBUG: 
                dns_records = cf.zones.dns_records.get(zone_id, params={'name':dname + '.' + zone_name})
                print(dns_records)
        else:
            logger.info(f'{dname} IP has not Changed!')
            #print(f'{dname} IP has not Changed!')
