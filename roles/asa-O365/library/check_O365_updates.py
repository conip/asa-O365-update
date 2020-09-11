#!/usr/bin/python
# this part of the code just checks Microsoft site for latest version and if 
# new version discovered it will download the content and save in /updates_files/o365_version_xxxxxxxxxx.txt file.
# To Ansible it returns only version number - latest files should already be added to the folder, keeping the history of it. 

from ansible.module_utils.basic import AnsibleModule
import json
import tempfile
from pathlib import Path
import urllib.request
import uuid
import ipaddress
#-------------------------------------------------
def webApiGet(methodName, instanceName, clientRequestId):
    ws = "https://endpoints.office.com"
    requestPath = ws + '/' + methodName + '/' + instanceName + '?clientRequestId=' + clientRequestId
    request = urllib.request.Request(requestPath)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())
# example of above
#https://endpoints.office.com/endpoints/Worldwide?clientRequestID=e8df34c7-cacb-43c6-be5a-7e6b11f23a5b
#-------------------------------------------------
# converting IP range from i.e. "8.8.8.0/24" to "8.8.8.0 255.255.255.0"
def f_ip_mask_change(ip_range_list):
    new_list = []
    var_tmp = ''
    for ip in ip_range_list:
        var_tmp = str(ipaddress.IPv4Network(ip).with_netmask)
        new_list.append(var_tmp.replace("/"," "))
    return new_list
#-------------------------------------------------
def main():
    module = AnsibleModule(
        argument_spec={}
    )

    datapath = Path(tempfile.gettempdir() + '/endpoints_clientid_latestversion.txt')

    # fetch client ID and version if data exists; otherwise create new file
    if datapath.exists():
        #print("TEMP folder is:"+str(datapath))
        with open(datapath, 'r') as fin:
            clientRequestId = fin.readline().strip()
            latestVersion = fin.readline().strip()
    else:
        clientRequestId = str(uuid.uuid4())
        latestVersion = '0000000000'
        with open(datapath, 'w') as fout:
            fout.write(clientRequestId + '\n' + latestVersion)
    # call version method to check the latest version, and pull new data if version number is different
    version = webApiGet('version', 'Worldwide', clientRequestId)
    if version['latest'] > latestVersion:
        #print('Published version: ' + str(version['latest']))
        #print('New version of Office 365 worldwide commercial service instance endpoints detected')
        # write the new version number to the data file
        with open(datapath, 'w') as fout:
            fout.write(clientRequestId + '\n' + version['latest'])
        # invoke endpoints method to get the new data
        endpointSets = webApiGet('endpoints', 'Worldwide', clientRequestId)
        # filter results for Allow and Optimize endpoints, and transform these into tuples with port and category
        flatUrls = []
        for endpointSet in endpointSets:
            if endpointSet['category'] in ('Optimize', 'Allow'):
                category = endpointSet['category']
                urls = endpointSet['urls'] if 'urls' in endpointSet else []
                tcpPorts = endpointSet['tcpPorts'] if 'tcpPorts' in endpointSet else ''
                udpPorts = endpointSet['udpPorts'] if 'udpPorts' in endpointSet else ''
                flatUrls.extend([(category, url, tcpPorts, udpPorts) for url in urls])
        flatIps = []
        for endpointSet in endpointSets:
            if endpointSet['category'] in ('Optimize', 'Allow'):
                ips = endpointSet['ips'] if 'ips' in endpointSet else []
                category = endpointSet['category']
                # IPv4 strings have dots while IPv6 strings have colons
                ip4s = [ip for ip in ips if '.' in ip]
                tcpPorts = endpointSet['tcpPorts'] if 'tcpPorts' in endpointSet else ''
                udpPorts = endpointSet['udpPorts'] if 'udpPorts' in endpointSet else ''
                flatIps.extend([(category, ip, tcpPorts, udpPorts) for ip in ip4s])
        
        #print('IPv4 Firewall IP Address Ranges')
        o365_IP_list = sorted(set([ip for (category, ip, tcpPorts, udpPorts) in flatIps]))
        
        update_file_path = './update_files/o365_version_' + version['latest'] + '.txt'
        
        list = f_ip_mask_change(o365_IP_list)
        with open(update_file_path, 'w') as fout:
            fout.write(json.dumps(list))
        
        module.exit_json(changed=True, meta=str(version['latest']))
        # TODO send mail (e.g. with smtplib/email modules) with new endpoints data
    else:
        #print('Published version: ' + str(version['latest']))
        #print('Office 365 worldwide commercial service instance endpoints are up-to-date')
        module.exit_json(changed=False, meta=str(version['latest']))

#--------------------------------------------- MAIN EXECUTION
if __name__ == '__main__':
    main()