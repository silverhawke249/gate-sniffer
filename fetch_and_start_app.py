import os
import psutil
import subprocess
import toolkit
import time
from scapy.all import IP, Raw, IPSession

# This script fetches gate data by sniffing traffic and dumping it into a file

STR_INIT_COMM = b'com.threerings.presents.net.SecureResponse'
STR_ROTATING_GATE = b'%town:m.rotating_gate_name'
STR_DATA_CHECK = b'm.terminal_core_desc'
STR_STEAM_VC = b'steamVoiceChatEnabled'  # this only works with Steam launcher
PACKET_FILTER = 'dst net 192.168.1 and tcp and ip'
SK_PATH = 'C:\\SteamLibrary\\steamapps\\common\\Spiral Knights'
SK_ARGS = 'java_vm/bin/javaw.exe -jar getdown-pro.jar . "" username password'  # use your own credentials you fools
DUMP_DIR = 'raw_dump/'

# TODO: Determine when this stream ends more precisely
print('Monitoring packets...')
state = 0
src_ip = None
queue, sniffer = toolkit.get_queue(session=IPSession, filter=PACKET_FILTER)

# Start game
curdir = os.getcwd()
os.chdir(SK_PATH)
process = subprocess.Popen(SK_ARGS)
process = psutil.Process(process.pid)
children = []
while not children:
    children = process.children(recursive=True)
# time_start = time.time()

# Start sniffer and accumulate the relevant packets
for pkt in toolkit.queue_yielder(queue):
    if src_ip is not None:
        if IP in pkt:
            if pkt.getlayer(IP).src != src_ip:
                continue
    
    if Raw in pkt:
        raw_data = pkt.getlayer(Raw).load
        if state == 0 and STR_INIT_COMM in raw_data:
            print('Found threerings packet!')
            print('Storing packets...')
            state = 1
            src_ip = pkt.getlayer(IP).src
            raw_dump = raw_data
        elif state == 1:
            raw_dump += raw_data
            if raw_dump.count(STR_ROTATING_GATE) >= 4 and raw_dump.count(STR_DATA_CHECK) == 2 + raw_dump.count(STR_ROTATING_GATE):
            # if STR_STEAM_VC in raw_dump:
                state = 2
        elif state == 2:
            raw_dump += raw_data
            if raw_dump.count(STR_DATA_CHECK) != 2 + raw_dump.count(STR_ROTATING_GATE):
                state = 1
            else:
                break

sniffer.stop()

# Try to kill game process
for child in children:
    try:
        child.kill()
    except psutil.NoSuchProcess:
        pass
os.chdir(curdir)

fn = DUMP_DIR + time.strftime('%Y%m%d%H%M%S', time.localtime())
with open(fn, 'wb') as f:
    f.write(raw_dump)

print('Saved to {}!'.format(fn))
