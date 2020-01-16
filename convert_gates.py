import os
import toolkit

# This script grabs the most recent raw dump and converts the data into
# gatemap-viewer suitable text file.

DUMP_DIR = 'raw_dump/'
SAVE_DIR = 'output/'

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

for gate in gates:
    data = toolkit.parse_binary_gate_data(gate)
    id = data['gate_id']
    name = data['gate_name']
    fn = SAVE_DIR + '{}_{}.txt'.format(id, name)
    with open(fn, 'w') as f:
        f.write('##GATEDATA\n')
        f.write('\n'.join(toolkit.convert_gate_dict(data)))
    print 'Saved to {}.'.format(fn)
