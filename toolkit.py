import construct as cs

from io import BytesIO
from itertools import zip_longest
from json import dumps
from queue import Queue
from scapy.all import *
from struct import unpack


def get_index_pairs(text, substring):
    indexes = []
    pos = 0
    while pos >= 0:
        pos = text.find(substring, pos)
        if pos >= 0:
            indexes.append(pos - 8)
            pos += len(substring)

    return zip_longest(indexes, indexes[1:])


def get_queue(*args, **kwargs):
    q = Queue()
    
    def handle_packet(p):
        q.put(p)
    
    # Will override prn keyword
    kwargs['prn'] = handle_packet
    
    sniffer = AsyncSniffer(*args, **kwargs)
    sniffer.start()
    
    return q, sniffer


def queue_yielder(q):
    while True:
        yield q.get(block=True)


def gate_factory(class_dict):
    normal_color_struct = cs.Struct(
        cs.Padding(2),
        'category' / cs.Byte,
        'color' / cs.Byte
    )
    offset_color_struct = cs.Struct(
        'source' / cs.Int,
        cs.Const(class_dict['color_triplet']),
        'hsv' / cs.Single[3]
    )
    color_entry_struct = cs.Struct(
        'type' / cs.RawCopy(cs.Short),
        'colors' / cs.Switch(cs.this.type.data, {
            class_dict['normal_color']: normal_color_struct,
            class_dict['offset_color']: offset_color_struct
        })
    )
    color_struct = cs.Struct(
        cs.Const(class_dict['colorization']),
        'num_entries' / cs.Int,
        'colorizations' / color_entry_struct[cs.this.num_entries]
    )
    level_struct = cs.Struct(
        cs.Const(class_dict['gate_level']),
        cs.Const(b'\x01'),
        'level_name' / cs.PascalString(cs.Short, 'ascii'),
        cs.Const(b'\x01'),
        'level_icon' / cs.PascalString(cs.Short, 'ascii'),
        'colorization' / color_struct,
        cs.Const(b'\x01'),
        'description' / cs.PascalString(cs.Short, 'ascii'),
        cs.Const(class_dict['level_type']),
        'level_type' / cs.Byte,
        'restricted' / cs.Byte
    )
    velocity_struct = cs.Struct(
        'velocity' / cs.Single,
        cs.Const(b'\x01'),
        'num_entries' / cs.Int,
        'lengths' / cs.Single[cs.this.num_entries],
        'start' / cs.Long
    )
    wheel_struct = cs.Struct(
        'class_id' / cs.RawCopy(cs.Short),
        'unknown' / cs.Byte[0x05],
        'num_levels' / cs.Short,
        'levels' / level_struct[cs.this.num_levels],
        'velocity' / cs.If(cs.this.class_id.data != class_dict['random_depth'], velocity_struct)
    )
    gate_struct = cs.Struct(
        cs.Const(b'\x01'),
        'gate_id' / cs.Int,
        cs.Const(b'\x01'),
        'gate_name' / cs.PascalString(cs.Short, 'ascii'),
        cs.Const(b'\x01'),
        'gate_icon' / cs.PascalString(cs.Short, 'ascii'),
        'colorization' / color_struct,
        cs.Const(b'\x01'),
        'description' / cs.PascalString(cs.Short, 'ascii'),
        'unknown' / cs.Byte[0x16],
        'num_wheels' / cs.Int,
        'wheels' / wheel_struct[cs.this.num_wheels],
        'class_id' / cs.Int16sb,
        cs.If(cs.this.class_id < 0, cs.PascalString(cs.Short, 'ascii')),
        'themes' / cs.Struct(
            'unknown' / cs.Byte[0x07],
            'themes' / cs.Byte[0x06]
        )
    )

    return gate_struct


def parse_data(data):
    # Class names to get the class numbers
    class_names = {
        'colorization': b'[Lcom.threerings.opengl.renderer.config.ColorizationConfig;',
        'normal_color': b'com.threerings.opengl.renderer.config.ColorizationConfig$Normal',
        'offset_color': b'com.threerings.opengl.renderer.config.ColorizationConfig$CustomOffsets',
        'color_triplet': b'com.threerings.opengl.renderer.config.ColorizationConfig$Triplet',
        'gate_summary': b'com.threerings.projectx.dungeon.data.RotatingGateSummary',
        'constant_depth': b'com.threerings.projectx.dungeon.data.GateSummary$Constant',
        'random_depth': b'com.threerings.projectx.dungeon.data.GateSummary$Random',
        'gate_level': b'com.threerings.projectx.dungeon.data.GateSummary$Level',
        'level_type': b'com.threerings.projectx.dungeon.data.DungeonCodes$LevelType'
    }

    class_ids = {}
    for key, val in class_names.items():
        index = data.index(val) - 4
        class_id = -cs.Int16sb.parse(data[index:index+2])
        class_ids[key] = cs.Short.build(class_id)
    struct = gate_factory(class_ids)

    gate_index = []
    subs = b'%town:m.rotating_gate_name'
    pos = 0
    while True:
        try:
            pos = data.index(subs, pos)
        except ValueError:
            break
        gate_index.append(pos - 8)
        pos += len(subs)

    index_pairs = itertools.zip_longest(gate_index, gate_index[1:])
    raw_gates = [data[i:j] for i, j in index_pairs]

    return [struct.parse(d) for d in raw_gates]


def convert_gate_struct(d):
    terminals = [0, 4, 8, 13, 18, 23, 29]
    dir_defined = False
    prev_dir = None
    lines = ['##LEVELS']
    for i, wheel in enumerate(d.wheels):
        if i in terminals:
            dir_defined = False
            prev_dir = None
            continue
            
        str_chunk = []
        if wheel.velocity is not None:
            dir = 'l' if wheel.velocity.velocity < 0 else 'r'
        else:
            dir = 'rand'
        level_data = [a.level_name for a in wheel.levels]
        
        if dir == 'rand':
            levels = level_data[:-2]
            tv_level = level_data[-2]
            if 'tvault' in tv_level:
                status = tv_level.split('_')[-1]
                status = 'x' if status == 'vanilla' else status
                dir += '_' + status
            dir_defined = False
        else:
            levels = level_data[:]
            dir_defined = True
        
        if not dir_defined or prev_dir not in ['l', 'r']:
            str_chunk.append(dir)
        
        prev_dir = dir
        
        for i, lv_name in enumerate(levels):
            if 'minis' in lv_name:
                family = wheel.levels[i].colorization.colorizations[0].colors.color
                main_family = ('construct' if family == 5 else
                               'fiend' if family == 6 else
                               'gremlin')
                suffix = '_' + main_family
            else:
                suffix = ''
            levels[i] = lv_name + suffix
        
        str_chunk += [get_string_rep(level) for level in levels]
        lines.append(', '.join(str_chunk))
    
    stratum_themes = ['Slime',
                      'Beast',
                      'Undead',
                      'Fiend',
                      'Gremlin',
                      'Construct',
                      'Fire',
                      'Freeze',
                      'Shock',
                      'Poison',
                      'Sleep',
                      'Curse',
                      'Stun',
                      'None']
    lines.append('##THEMES')
    lines.append(', '.join([stratum_themes[a] for a in d.themes.themes]))
    
    lines.append('##ROTATIONS')
    velocities = [convert_container(a.velocity) for a in d.wheels]
    velocities = [{'n': d.wheels[i].num_levels, 'data': a} for i, a in enumerate(velocities)]
    lines.append(dumps(velocities))
    
    return lines


def convert_container(c):
    if isinstance(c, cs.ListContainer):
        return [convert_container(a) for a in c]
    elif isinstance(c, cs.Container):
        if 'offset1' in c and 'offset2' in c:
            return c.value
        out = {}
        for k, v in c.items():
            if k == '_io':
                continue
            out[k] = convert_container(v)
        return out
    return c


def get_string_rep(s):
    lv_parts = []
    arena = {'fla': 'fire',
             'ima': 'freeze',
             'tfa': 'shock',
             'vfa': 'poison',
             'iea': 'x'}
    tunnel = {'bf': 'fire',
              'cc': 'freeze',
              'pc': 'shock',
              'ww': 'poison',
              'ct': 'x'}
    compound = {'cc': 'fire',
                'fc': 'freeze',
                'sc': 'shock',
                'bc': 'poison',
                'rc': 'x'}
    
    if 'minis' in s:
        lv_parts.append('compound')
        parts = s.split('_')
        lv_parts.append(parts[-1])
        k = [x for x in compound if x in s][0]
        lv_parts.append(compound[k])
        lv_parts.append(parts[1])
    elif 'starlight_cradle' in s:
        if 'miniboss' in s:
            lv_parts.append('starlight_boss')
        else:
            lv_parts.append('starlight')
            n = s[-1]
            n = '' if n == 'r' else n
            if 'shrine_of_slumber' in s:
                lv_parts.append('ss' + n)
            elif 'meteor_mile' in s:
                lv_parts.append('mm' + n)
            else:
                raise ValueError('unrecognized level name: {}'.format(s))
    elif 'dark_city' in s:
        if 'miniboss' in s:
            lv_parts.append('darkcity_boss')
        else:
            lv_parts.append('darkcity')
            n = s[-1]
            n = '' if n == 'y' else n
            if n in ['', '2', '3']:
                lv_parts.append('rr' + n)
            elif n in ['4', '5']:
                n = '' if n == '4' else '2'
                lv_parts.append('ss' + n)
            elif n == '6':
                lv_parts.append('pm')
            else:
                raise ValueError('unrecognized level name: {}'.format(s))
    elif 'concrete_jungle' in s:
        if 'miniboss' in s:
            lv_parts.append('concrete_boss')
        else:
            lv_parts.append('concrete')
            n = s[-1]
            n = '' if n != '2' else n
            if 'totem_trouble' in s:
                lv_parts.append('tt' + n)
            elif 'blight_boulevard' in s:
                lv_parts.append('bb' + n)
            else:
                raise ValueError('unrecognized level name: {}'.format(s))
    elif 'scarlet_fortress' in s or 'lost_castle' in s:
        lv_parts.append('scarlet')
        n = s[-1]
        n = '' if (n != '2' and n != '3') else n
        if 'cravat_hall' in s:
            lv_parts.append('ch' + n)
        elif 'spiral_court' in s:
            lv_parts.append('sc' + n)
        elif 'grim_gallery' in s:
            lv_parts.append('gg')
        else:
            raise ValueError('unrecognized level name: {}'.format(s))
    elif 'aurora_isles' in s:
        lv_parts.append('aurora')
        if 'stone_grove' in s:
            lv_parts.append('sto')
        elif 'the_jelly_farm' in s:
            n = s[-1]
            n = '' if n != '2' else n
            lv_parts.append('jly' + n)
        elif 'the_low_gardens' in s:
            lv_parts.append('low')
        else:
            raise ValueError('unrecognized level name: {}'.format(s))
    elif 'jigsaw_valley' in s:
        lv_parts.append('jigsaw')
        n = s[-1]
        n = '' if n != '2' else n
        if 'emerald_axis' in s:
            lv_parts.append('ax' + n)
        elif 'the_jade_tangle' in s:
            lv_parts.append('jt' + n)
        elif 'perimeter_promenade' in s:
            lv_parts.append('pp' + n)
        else:
            raise ValueError('unrecognized level name: {}'.format(s))
    elif 'gloaming_wildwoods' in s:
        if 'snarbolax' in s:
            lv_parts.append('snarb')
        else:
            lv_parts.append('gww')
            if 'path' in s:
                lv_parts.append('d1')
            elif 'ruins' in s:
                lv_parts.append('d2')
            else:
                raise ValueError('unrecognized level name: {}'.format(s))
    elif 'royal_jelly' in s:
        if 'lair' in s:
            lv_parts.append('jk')
        else:
            lv_parts.append('rjp')
            if 'garden' in s:
                lv_parts.append('d1')
            elif 'court' in s:
                lv_parts.append('d2')
            else:
                raise ValueError('unrecognized level name: {}'.format(s))
    elif 'ironclaw_munitions_factory' in s:
        if 'twins' in s:
            lv_parts.append('rt')
        else:
            lv_parts.append('imf')
            if 'assembly' in s:
                lv_parts.append('d1')
            elif 'workshop' in s:
                lv_parts.append('d2')
            else:
                raise ValueError('unrecognized level name: {}'.format(s))
    elif 'firestorm_citadel' in s:
        if 'vanaduke' in s:
            lv_parts.append('vana')
        else:
            lv_parts.append('fsc')
            if 'blackstone_bridge' in s:
                lv_parts.append('d1')
            elif 'charred_court' in s:
                lv_parts.append('d2')
            elif 'ash_armory' in s:
                lv_parts.append('d3')
            elif 'smoldering_steps' in s:
                lv_parts.append('d4')
            else:
                raise ValueError('unrecognized level name: {}'.format(s))
    elif 'candlestick_keep' in s:
        lv_parts.append('csk')
        status = s.split('_')[-1]
        status = 'x' if status == 'vanilla' else status
        lv_parts.append(status)
    elif 'deconstruction_zone' in s:
        lv_parts.append('decon')
        status = s.split('_')[-1]
        status = 'x' if status == 'vanilla' else status
        lv_parts.append(status)
    elif 'wolver_den' in s:
        lv_parts.append('den')
        status = s.split('_')[-1]
        status = 'x' if status == 'vanilla' else status
        lv_parts.append(status)
    elif 'lichenous_lair' in s:
        lv_parts.append('lichen')
        status = s.split('_')[-1]
        status = 'x' if status == 'vanilla' else status
        lv_parts.append(status)
    elif 'devilish_drudgery' in s:
        lv_parts.append('dd')
        status = s.split('_')[-1]
        status = 'x' if status == 'vanilla' else status
        lv_parts.append(status)
    elif any([x in s for x in arena]):
        lv_parts.append('arena')
        lv_parts.append(s.split('_')[1])
        k = [x for x in arena if x in s][0]
        lv_parts.append(arena[k])
    elif any([x in s for x in tunnel]):
        lv_parts.append('tunnel')
        lv_parts.append(s.split('_')[1])
        k = [x for x in tunnel if x in s][0]
        lv_parts.append(tunnel[k])
    else:
        raise ValueError('unrecognized level name: {}'.format(s))
    
    return ' '.join(lv_parts)
