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
    data = {
        'gate_id': gate.gate_id,
        'gate_name': gate.gate_name[27:],
        'fg_color': None,
        'bg_color': None
    }
    for c in gate.colorization.colorizations:
        if c.colors.source == 2:
            data['fg_color'] = [round(a, 3) for a in c.colors.hsv]
        elif c.colors.source == 3:
            data['bg_color'] = [round(a, 3) for a in c.colors.hsv]
    print('ID {gate_id}  Name {gate_name}  FG {fg_color}  BG {bg_color}'.format(**data))
