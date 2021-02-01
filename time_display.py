import os
import time
import toolkit

# This script grabs the most recent raw dump and displays level timings

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
gate = gates[-1]

while True:
    os.system('cls')
    print(f'reading from {gate.gate_name[27:]} (id {gate.gate_id})...')
    t_delta = time.time() - gate.wheels[0].velocity.start / 1000
    print(f'current time: {int(t_delta)}')
    print()
    print('level lengths, in seconds:')
    for i, wheel in enumerate(gate.wheels):
        prev_wheel = gate.wheels[i - 1] if i != 0 else None
        print(f'{i+1:2}', end='')
        prev_velocity = 0 if i == 0 or prev_wheel.velocity is None else prev_wheel.velocity.velocity
        if wheel.num_levels > 1 and wheel.velocity is not None:
            actual_velocity = abs(wheel.velocity.velocity - prev_velocity)
            print(f'{t_delta % (6.2831855 / actual_velocity):12.2f}', end='')
            for length in wheel.velocity.lengths:
                print(f'{length / actual_velocity:12.2f}', end='')
        print()
    
    time.sleep(0.3)
