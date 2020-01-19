import os
import toolkit

# This script grabs the most recent raw dump and outputs raw binary data
# for each individual gate, for easier analysis.

DUMP_DIR = 'raw_dump/'

for _, _, fns in os.walk(DUMP_DIR):
    break

fns.sort()
fn = DUMP_DIR + fns[-2]
print('Opening {}...'.format(fn))

with open(fn, 'rb') as f:
    raw_data = f.read()

index_pairs = toolkit.get_index_pairs(raw_data, b'%town:m.rotating_gate_name')
gates = [raw_data[i:j] for i, j in index_pairs]

for i, gate in enumerate(gates):
    with open(f'gate{i}.dat', 'wb') as f:
        f.write(gate)
    print(f'Saved to gate{i}.dat.')
