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

index_pairs = toolkit.get_index_pairs(raw_data, b'%town:m.rotating_gate_name')
gates = [raw_data[i:j] for i, j in index_pairs]

for gate in gates:
    data = toolkit.parse_binary_gate_data(gate)
    print('ID {gate_id}  Name {gate_name}  FG {fg_color}  BG {bg_color}\nThemes  {themes}'.format(**data))
