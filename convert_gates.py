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
print('Opening {}...'.format(fn))

with open(fn, 'rb') as f:
    raw_data = f.read()

gates = toolkit.parse_data(raw_data)

for gate in gates:
    id = gate.gate_id
    names = gate.gate_name
    names = names.split('|')[1:]
    names = [a[2:] for a in names]
    name = '_'.join(names)
    fn = SAVE_DIR + f'{id}_{name}.txt'
    with open(fn, 'w') as f:
        f.write('##GATEDATA\n')
        f.write('\n'.join(toolkit.convert_gate_struct(gate)))
    print(f'Saved to {fn}.')
