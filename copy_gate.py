import datetime
import json
import os
import subprocess
import sys

# This script copies over a specified file and adds its entry
# to gate_list.txt, or the last file when not specified

# get filepath and name
if len(sys.argv) == 1:
    for _, _, fns in os.walk('output/'):
        break
    fns = [os.path.join('output', fn) for fn in fns if fn.endswith('.txt')]
    fns.sort()
    fp = fns.pop()
else:
    fp = sys.argv[1]

fn = os.path.basename(fp)

GATEMAP_PATH = os.path.join('..', 'gatemap-viewer', 'gates')

fn_parts = os.path.splitext(fn)[0].split('_')

# figure out date maths to get the next gate's date
# this gets fucked up when a single date has multiple gates (like DST coming off)
"""
BASE_DATE = datetime.date(2020, 5, 23)
BASE_ID = 2087
gate_id = int(fn_parts[0])
gate_date = BASE_DATE + datetime.timedelta(days=2) * (gate_id - BASE_ID)
"""
# i'm just gonna use local time and use that as the timestamp
gate_date = datetime.date.today()

# copy over gate data
with open(fp, 'r') as f:
    contents = f.read()

new_fn_parts = [gate_date.strftime('%Y%m%d')] + fn_parts[1:]
new_fn = '_'.join(new_fn_parts) + '.txt'

with open(os.path.join(GATEMAP_PATH, new_fn), 'w') as f:
    f.write(contents)

# append into gate list
with open(os.path.join(GATEMAP_PATH, 'gate_list.txt'), 'r') as f:
    gate_list = json.loads(f.read())

gate_list.append(new_fn_parts)

with open(os.path.join(GATEMAP_PATH, 'gate_list.txt'), 'w') as f:
    f.write(json.dumps(gate_list))

# commit and push
os.chdir(GATEMAP_PATH)
subprocess.call('git add .')
subprocess.call(f'git commit . -m "{gate_date.strftime("%Y%m%d")} gate update"')
subprocess.call('git push')
