from Queue import Queue
from struct import unpack
from scapy.all import *
from StringIO import StringIO


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


def clamp(val, min, max):
    if val <= min:
        return min
    elif val >= max:
        return max
    else:
        return val


def parse_binary_gate_data(d):
    # Any seek operation that isn't 1 byte discards unknown data!
    # Refer to gatemap.bt for how the struct is arranged
    s = StringIO(d)
    s.seek(1, 1)
    gate_id = unpack('>I', s.read(4))[0]
    s.seek(1, 1)
    name_len = unpack('>H', s.read(2))[0]
    
    # Discarding the prefix since we're only interested in the actual name
    s.seek(0x1B, 1)
    internal_gate_name = s.read(name_len - 0x1B)
    s.seek(1, 1)
    icon_name_len = unpack('>H', s.read(2))[0]
    s.seek(icon_name_len, 1)
    color_data = read_colorization(s)
    s.seek(1, 1)
    gate_desc_len = unpack('>H', s.read(2))[0]
    s.seek(gate_desc_len, 1)
    s.seek(0x16, 1)
    wheel_num = unpack('>I', s.read(4))[0]
    
    gate_name_pieces = internal_gate_name.split('|')
    gate_name_pieces = [x.split('.')[1] for x in gate_name_pieces]
    gate_name = '_'.join(gate_name_pieces)
    for color in color_data:
        hsv = tuple(round(c, 3) for c in color[3])
        if color[1] == 2:
            fg_color = hsv
        elif color[1] == 3:
            bg_color = hsv
        else:
            raise ValueError('unrecognized color source: {}'.format(color[1]))
    data = {'gate_id': gate_id,
            'gate_name': gate_name,
            'fg_color': fg_color,
            'bg_color': bg_color,
            'contents': None}
    
    contents = []
    for _ in xrange(wheel_num):
        levels = ['?']
        rand_bit = unpack('>H', s.read(2))[0]
        s.seek(0x05, 1)
        num_levels = unpack('>H', s.read(2))[0]
        
        for _ in xrange(num_levels):
            s.seek(0x03, 1)
            lv_name_len = unpack('>H', s.read(2))[0]
            lv_name = s.read(lv_name_len)
            s.seek(1, 1)
            lv_icon_len = unpack('>H', s.read(2))[0]
            s.seek(lv_icon_len, 1)
            color_data = read_colorization(s)
            s.seek(1, 1)
            desc_len = unpack('>H', s.read(2))[0]
            s.seek(desc_len, 1)
            s.seek(0x04, 1)
            
            # Special treatment for compounds, since main family is only
            # discernible via colorization
            if 'minis' in lv_name:
                family = color_data[0][1][1]
                main_family = ('construct' if family == 5 else
                               'fiend' if family == 6 else
                               'gremlin')
                suffix = '_' + main_family
            else:
                suffix = ''
            levels.append(lv_name + suffix)
            
        # This is 0x44 or 0x45, depends on whether an extra class
        # gets declared or not
        if 0x44 <= rand_bit <= 0x45:
            levels[0] = 'rand'
        else:
            dir_byte = unpack('B', s.read(1))[0]
            levels[0] = 'l' if dir_byte & 0x80 else 'r'
            s.seek(0x10 + num_levels*4, 1)
            
        contents.append(levels)
    
    class_id = unpack('>h', s.read(2))[0]
    if class_id < 0:
        class_name_len = unpack('>H', s.read(2))[0]
        s.seek(class_name_len, 1)
    s.seek(0x07, 1)
    themes = unpack('>BBBBBB', s.read(6))
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
    
    data['contents'] = contents[1:]
    data['themes'] = tuple(stratum_themes[x] for x in themes)
    return data


def read_colorization(s):
    # Might be worth it to really unravel this structure?
    # Class ID can be a different number, but so far it's
    # either 0x3A or 0x3B -- classes are IDed as they get declared
    class_id = unpack('>H', s.read(2))[0]
    offset = class_id - 0x3A
    s.seek(0x02, 1)
    num_entries = unpack('>H', s.read(2))[0]
    data = []
    for _ in xrange(num_entries):
        type = unpack('>H', s.read(2))[0]
        if type == 0x42 + offset:
            source = unpack('>I', s.read(4))[0]
            # Usually this is 0x43 -- haven't encountered others yet
            specifier = unpack('>H', s.read(2))[0]
            hsv_offset = unpack('>fff', s.read(12))
            data.append((type, source, specifier, hsv_offset))
        elif type == 0x2D:
            # Seems to just be zero bytes
            s.seek(0x02, 1)
            colors = unpack('>BB', s.read(2))
            data.append((type, colors))
    return data


def convert_gate_dict(d):
    depths = d['contents']
    
    terminals = [4, 8, 13, 18, 23, 29]
    dir_defined = False
    prev_dir = None
    lines = ['##LEVELS']
    for depth, level_data in enumerate(depths):
        if depth+1 in terminals:
            dir_defined = False
            prev_dir = None
            continue
            
        str_chunk = []
        dir = level_data[0]
        
        if dir == 'rand':
            levels = level_data[1:-2]
            tv_level = level_data[-2]
            if 'tvault' in tv_level:
                status = tv_level.split('_')[-1]
                status = 'x' if status == 'vanilla' else status
                dir += '_' + status
            dir_defined = False
        else:
            levels = level_data[1:]
            dir_defined = True
        
        if not dir_defined or prev_dir not in ['l', 'r']:
            str_chunk.append(dir)
        
        prev_dir = dir
        
        str_chunk += [get_string_rep(level) for level in levels]
        lines.append(', '.join(str_chunk))
    
    lines.append('##THEMES')
    lines.append(', '.join(d['themes']))
    
    return lines


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
