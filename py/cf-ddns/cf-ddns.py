#! /usr/bin python3
import requests
import json
import CloudFlare

DEBUG = False

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
    if DEBUG: print(f'token:{token}, dnames:{dnames}')
    cf = CloudFlare.CloudFlare(token=token)
    zones = cf.zones.get()
    for zone in zones:
        zone_id = zone['id']
        zone_name = zone['name']
        if DEBUG: print(zone_id, zone_name)
    for dname in dnames:
        cf_dns_records = cf.zones.dns_records.get(zone_id, params={'name':dname + '.' + zone_name})
        cf_ipv4 = ''
        if(len(cf_dns_records) != 0):
            cf_ipv4 = cf_dns_records[0]['content']
        if DEBUG: print(f'{dname} cf_ipv4:'+ cf_ipv4)
        try:
            ipv4 = requests.get('https://1.1.1.1/cdn-cgi/trace').text.split('\n')
            ipv4.pop()
            ipv4 = dict(s.split('=') for s in ipv4)['ip']
        except Exception:
            print(f'Get {dname} ipv4 Fail!')
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
            print(f'{dname} IP updated successfully!')
            if DEBUG == False:
                exit(0)
            if DEBUG: 
                dns_records = cf.zones.dns_records.get(zone_id, params={'name':dname + '.' + zone_name})
                print(dns_records)
        else:
            print(f'{dname} IP has not Changed!')
