import os

# This script grabs the most recent raw dump and outputs raw binary data
# for each individual gate, for easier analysis.

DUMP_DIR = 'raw_dump/'

for _, _, fns in os.walk(DUMP_DIR):
    break

fns.sort()
fn = DUMP_DIR + fns[-2]
print 'Opening {}...'.format(fn)

with open(fn, 'rb') as f:
    raw_data = f.read()

subs = '%town:m.rotating_gate_name'
indexes = []
pos = 0
while pos >= 0:
    pos = raw_data.find(subs, pos)
    if pos >= 0:
        indexes.append(pos - 8)
        pos += len(subs)

index_pairs = map(None, indexes, indexes[1:])
gates = [raw_data[i:j] for i, j in index_pairs]

for i, gate in enumerate(gates):
    with open('gate{}.dat'.format(i), 'wb') as f:
        f.write(gate)
    print 'Saved to gate{}.dat.'.format(i)
