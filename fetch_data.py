import toolkit
import time
from scapy.all import IP, Raw, IPSession

# This script fetches gate data by sniffing traffic and dumping it into a file

STR_INIT_COMM = 'com.threerings.presents.net.SecureResponse'
STR_BEGIN_GATE_DATA = 'com.threerings.projectx.dungeon.data.RotatingGateSummary'
STR_DATA_CHECK = 'm.terminal_core_desc'
PACKET_FILTER = 'dst net 192.168.1 and tcp and ip'
DUMP_DIR = 'raw_dump/'

# TODO: Determine when this stream ends more precisely
print 'Monitoring packets...'
state = 0
src_ip = None
queue, sniffer = toolkit.get_queue(session=IPSession, filter=PACKET_FILTER)
for pkt in toolkit.queue_yielder(queue):
    if src_ip is not None:
        if IP in pkt:
            if pkt.getlayer(IP).src != src_ip:
                continue
    
    if Raw in pkt:
        raw_data = pkt.getlayer(Raw).load
        if state == 0 and STR_INIT_COMM in raw_data:
            print 'Found threerings packet!'
            print 'Storing packets...'
            state = 1
            src_ip = pkt.getlayer(IP).src
            raw_dump = raw_data
        elif state == 1:
            raw_dump += raw_data
            if raw_dump.count(STR_DATA_CHECK) >= 6:
                state = 2
        elif state == 2:
            break

sniffer.stop()

fn = DUMP_DIR + time.strftime('%Y%m%d%H%m%S', time.localtime())
with open(fn, 'wb') as f:
    f.write(raw_dump)

print 'Saved to {}!'.format(fn)
