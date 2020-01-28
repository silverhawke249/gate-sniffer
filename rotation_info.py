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
    print(gate.gate_name[27:])
    prev_velocity = 0
    for i, wheel in enumerate(gate.wheels):
        velocity_data = wheel.velocity
        if velocity_data is not None:
            velocity = velocity_data.velocity - prev_velocity
            segment_lengths = velocity_data.lengths
            if velocity != 0:
                segment_time = [round(a / abs(velocity), 2) for a in segment_lengths]
            else:
                segment_time = '---'
            prev_velocity = velocity_data.velocity
        else:
            segment_time = '---'
            prev_velocity = 0
        print(f'D{i:2}: {", ".join([a.level_name for a in wheel.levels])}')
        print(f'     {segment_time}')
    print()
