#!/usr/bin/python3
'''
simple load and save utility for the Yaesu VX-7R

uses information from
http://hse.dyndns.org/hiroto/RFY_LAB/vx7/e/vx7_8510.htm and
VX Manager, from http://vx-manager.sourceforge.net/vxreadme.shtml

this software is intentionally very basic so that people can easily
modify it for other radios without having to wade through megabytes
of source. consider this copylefted, i.e. under GNU license, with
*no* guarantees, use at your own risk -- jc at unternet dot net
'''
# pylint: disable=consider-using-f-string
import sys, os, time, logging, serial  # pylint: disable=multiple-imports
logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)
DEV = '/dev'
PORTS = [os.path.join(DEV, port) for port in os.listdir(DEV)
         if port.startswith('ttyUSB')]
ACK = chr(6)
DATASIZE = 16211
CHECKBYTES = [0x611, 0x691, 0x3f52]
HIRAGANA = ''.join([chr(n) for n in range(0x3040, 0x30a0)])
KATAKANA = ''.join([chr(n) for n in range(0x30a0, 0x3100)])
KANJI = [  # box, 0x56d7, used as placeholder for unidentified Kanji
    # (lookup C1 character images by radical at
    #  https://www.chinese-tools.com/tools/sinograms.html?r)
    # (map hex to character and definition at
    #  https://unicode-explorer.com/c/611b)
    # love, voltage, Italy, place,  town,   raise,  one,    briar,
    0x611b, 0x5727, 0x4f0a, 0x4f4d, 0x4e95, 0x80b2, 0x4e00, 0x8328,
    # England, defense, exceed, yen, far,   across, ridge,  pour,
    0x82f1, 0x885b, 0x8d8a, 0x5186, 0x9060, 0x6a2a, 0x5ca1, 0x6c96,
    # house, warm,  tone,   change, song,   river,  fire,   fragrant
    0x5c4b, 0x6e29, 0x97f3, 0x5316, 0x6b4c, 0x6cb3, 0x706b, 0x9999,
    0x9e7f, 0x8cc0, 0x6d77, 0x676e, 0x9694, 0x5b66, 0x6f5f, 0x9593,
    0x95a2, 0x83c5, 0x5ca9, 0x5893, 0x6a5f, 0x6c17, 0x57ce, 0x5c90,
    0x6025, 0x6551, 0x4e5d, 0x4eac, 0x6559, 0x6a4b, 0x7389, 0x7981,
    0x91d1, 0x533a, 0x7a7a, 0x718a, 0x6817, 0x7fa4, 0x90e1, 0x5f62,
    0x8b66, 0x6708, 0x770c, 0x539f, 0x8a00, 0x9650, 0x5eab, 0x8fbc,
    0x53e4, 0x4e94, 0x8a9e, 0x53e3, 0x5e83, 0x822a, 0x9ad8, 0x5408,
    0x523b, 0x56fd, 0x9ed2, 0x6839, 0x4f50, 0x707d, 0x57fc, 0x897f,
    0x5742, 0x5d0e, 0x5bdf, 0x672d, 0x6ca2, 0x6fa4, 0x4e09, 0x5c71,
    0x56db, 0x58eb, 0x5e02, 0x6b62, 0x7d19, 0x6ecb, 0x5150, 0x6642,
    0x793a, 0x81ea, 0x4e03, 0x53d6, 0x624b, 0x6b8a, 0x9152, 0x5dde,
    0x79cb, 0x96c6, 0x5341, 0x91cd, 0x66f8, 0x5c0f, 0x6d88, 0x4e0a,
    0x65b0, 0x68ee, 0x795e, 0x63c4, 0x5236, 0x9752, 0x9759, 0x53f3,
    0x8a2d, 0x4ed9, 0x5343, 0x5ddd, 0x7dda, 0x8239, 0x76f8, 0x7d9b,
    0x9001, 0x675f, 0x6e2c, 0x7d9a, 0x6751, 0x968a, 0x53f0, 0x5927,
    0x7b2c, 0x6edd, 0x5358, 0x77e5, 0x4e2d, 0x5e81, 0x671d, 0x753a,
    0x8074, 0x9577, 0x5cf6, 0x5b9a, 0x9244, 0x5929, 0x7530, 0x96fb,
    0x6238, 0x90fd, 0x5ea6, 0x571f, 0x5cf6, 0x6771, 0x76d7, 0x85e4,
    0x9053, 0x5fb3, 0x7279, 0x8aad, 0x6803, 0x5948, 0x7e04, 0x4e8c,
    0x65e5, 0x6cbc, 0x6fc3, 0x80fd, 0x7109, 0x58f2, 0x8236, 0x516b,
    0x962a, 0x98ef, 0x5c3e, 0x5a9b, 0x767e, 0x8868, 0x79d2, 0x6d5c,
    0x5bcc, 0x5e9c, 0x961c, 0x6b66, 0x90e8, 0x5e45, 0x798f, 0x5206,
    0x6587, 0x9593, 0x5175, 0x4e26, 0x653e, 0x82b3, 0x9632, 0x5317,
    0x5e4c, 0x672c, 0x6bce, 0x4e07, 0x5b98, 0x7121, 0x540d, 0x6728,
    0x8c37, 0x91ce, 0x696d, 0x967d, 0x7d61, 0x68a8, 0x826f, 0x6797,
    0x9234, 0x9023, 0x8def, 0x516d, 0x548c,
]
CHARACTERS = { # two character sets, 0 and 1, total 512 characters
# from http://hse.dyndns.org/hiroto/RFY_LAB/vx7/e/vx7_8510.htm
    'digits': '0123456789',
    'alphabetic': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'symbols': '.,:;!"#$%&\x27()*+-\u22c5=<>?@[\uffe5]^_\\{|}\u2192\u2190' \
        '\u25b2\u25bc~\u203c\u00f7\u00d7\u221a\u03bb' \
        '\u03bc\u03c0\u03c6\u03c9\u03a9\u2103\u2109\u00a3' \
        '\u00b1\u222b\u266a\u266b\u266d\u23b5\u300c\u300d' \
        '\u00b7\u2642\u2640\u3012',
    'hiragana': (
        HIRAGANA[0x2:0xb:2] +
        HIRAGANA[0xb:0x14:2] +
        HIRAGANA[0x15:0x1e:2] +
        HIRAGANA[0x1f:0x22:2] +
        HIRAGANA[0x24:0x29] +
        HIRAGANA[0x2a:0x2f:2] +
        HIRAGANA[0x2f:0x3c:3] +
        HIRAGANA[0x3f:0x43] +
        HIRAGANA[0x44:0x49:2] +
        HIRAGANA[0x49:0x4e] +
        HIRAGANA[0x4f:0x54] +
        HIRAGANA[0x0c:0x15:2] +
        HIRAGANA[0x16:0x1f:2] +
        HIRAGANA[0x20:0x23:2] +
        HIRAGANA[0x25:0x2a:2] +
        '\u3002\u3001' +  # CJK full stop and comma
        HIRAGANA[0x30:0x3d:3] +
        HIRAGANA[0x31:0x3e:3] +
        HIRAGANA[0x1:0xa:2] +
        HIRAGANA[0x43:0x48:2] +
        HIRAGANA[0x23]
    ),
    'katakana': (
        KATAKANA[0x2:0xb:2] +
        KATAKANA[0xb:0x14:2] +
        KATAKANA[0x15:0x1e:2] +
        KATAKANA[0x1f:0x22:2] +
        KATAKANA[0x24:0x29] +
        KATAKANA[0x2a:0x2f:2] +
        KATAKANA[0x2f:0x3c:3] +
        KATAKANA[0x3f:0x43] +
        KATAKANA[0x44:0x49:2] +
        KATAKANA[0x49:0x4e] +
        KATAKANA[0x4f] +
        KATAKANA[0x52:0x54] +  # drop obsolete wi and we
        KATAKANA[0x0c:0x15:2] +
        KATAKANA[0x16:0x1f:2] +
        KATAKANA[0x20:0x23:2] +
        KATAKANA[0x25:0x2a:2] +
        KATAKANA[0x30:0x3d:3] +
        KATAKANA[0x31:0x3e:3] +
        KATAKANA[0x1:0xa:2] +
        KATAKANA[0x43:0x48:2] +
        KATAKANA[0x23]
    ),
}
CHARACTERS['vx7r'] = CHARACTERS['digits'] + ' ' + CHARACTERS['alphabetic'] + \
    CHARACTERS['alphabetic'].lower() + CHARACTERS['symbols'] + \
    CHARACTERS['hiragana'] + CHARACTERS['katakana'] + \
    ''.join(map(chr, KANJI))
def serialread(port, count, check=False):
    '''
    read data over serial connection
    '''
    logging.debug('attempting to read %d bytes from %s', count, port)
    data = port.read(count)
    logging.debug('%d bytes of data read: %s', len(data),
                  data[:40].encode('hex'))
    if not check:
        time.sleep(0.2)  # delay before ACK
        port.write(ACK)
        ack = port.read(1)
        logging.debug('ACK expected: %s, seen: %s', repr(ACK), repr(ack))
    return data
def read(filename):
    '''
    read data from file or stdin
    '''
    # pylint: disable=consider-using-with
    if filename is None:
        infile = sys.stdin
    else:
        infile = open(filename, encoding='utf-8')
    data = infile.read()
    infile.close()
    return data
def serialwrite(port, data, final_block=False):
    '''
    note that the VX-7R echoes back data whether you like it or not

    first tried writing the data in a single 'write', but it was failing
    after block 2 when a spurious 0xff character was coming back either
    before or after the ACK, depending on programmed delays.
    '''
    logging.debug('attempting to write %d bytes to %s', len(data), port)
    readback, error = '', False
    for index, byte in enumerate(data):
        port.write(byte)
        if not final_block:
            port.sendBreak(1.0)
        if index == len(data) - 1:
            echo = port.read(1)
        else:
            echo = port.read(port.inWaiting() or 1)
        readback += echo
        if echo != data[index]:
            logging.debug('echoed data (%s) not same as sent (%s)',
                          repr(echo), repr(byte))
            if final_block:
                logging.info('quitting at block offset %d', index)
                break
            if byte == b'\xff' and echo == b'\xff\xff\x06':  # buggy USB adapter
                logging.info('last character doubled, skipping to next block')
                error = True
                break
    logging.debug('data written: %s', snippet(readback))
    if not final_block and not error:
        time.sleep(0.2)  # delay before ACK
        ack = port.read(port.inWaiting() or 1)
        logging.debug('ACK expected: %s, seen: %s', repr(ACK), repr(ack))
        port.write(ACK)
        echo = port.read(port.inWaiting() or 1)
        logging.debug('ACK read back: %s', repr(echo))
def snippet(data, maxlength=32):
    '''
    generate snippet of data for debugging
    '''
    snipped = data[:maxlength].encode('hex')
    if len(data) > maxlength:
        snipped += '...'
    return snipped
def write(filename, data):
    '''
    write out data to file or stdout
    '''
    # pylint: disable=consider-using-with
    if filename is None:
        if sys.stdin.isatty():
            print((data.encode('hex')))
        else:
            sys.stdout.write(data)
    else:
        outfile = open(filename, 'wb')
        outfile.write(data)
        outfile.close()
def checksum(data, default_offset=-127):
    '''
    verify data checksum
    '''
    failed = False
    if len(data) != DATASIZE:
        filename = data
        data = read(filename)  # assume it's a file and not raw data
    else:
        filename = None
    for index, checkbyte in enumerate(CHECKBYTES):
        # final checkbyte is sum of *all* bytes
        offset = 0 if index == len(CHECKBYTES) - 1 else checkbyte + default_offset
        check = sum(map(ord, data[offset:checkbyte])) & 0xff
        check_sum = ord(data[checkbyte])
        logging.debug('checksum [0x%x:0x%x] calculated: 0x%x, found: 0x%x',
                      offset, checkbyte - 1, check, check_sum)
        if check_sum != check:
            failed = True
            if not filename:
                logging.debug('correcting checksum %d to 0x%x', index, check)
                data = data[:checkbyte] + chr(check) + data[checkbyte + 1:]
    return failed if filename else data
def clone(action=None, filename=None, port=None):
    '''
    clone radio data in two steps: read, followed by write or modwrite

    other options also, primarily for debugging
    '''
    if action in ['read', 'write', 'modwrite']:
        port = serial.Serial(port or PORTS[0], baudrate=19200,
                             stopbits=2, timeout=30)
    if action == 'read':
        vxread(filename, port)
    elif action == 'write':
        vxwrite(filename, port)
    elif action == 'modwrite':
        vxwrite(filename, port, freeband=True)
    elif action == 'checksum':
        sys.exit(checksum(filename))
    elif action == 'rawdump':
        print((rawdump(filename).encode('utf8')))
    elif action == 'dump':
        dump(filename)
    elif action == 'chardump':
        chardump()
    else:
        logging.error('must specify "read" or "write"')
        sys.exit(1)
def freeband_mod(data, modded):
    '''
    modifications for RX and TX outside of HAM bands

    see https://web.archive.org/web/20240513044831/
     https://www.hayseed.net/~jpk5lad/K5LAD%20files/
      Yaesu_VX-7R/VX-7%20downloads/VX7%20Commander%20v.10/MODS.txt
    '''
    modbyte = ord(data[10])
    moddedbyte = ord(data[6])
    hardware_setting = 0xe8 if modded else [moddedbyte, 0xe0][moddedbyte == 0xe8]
    if modbyte == 0xe8:
        logging.debug('image already has mod enabled')
    else:
        logging.debug('enabling mod %02x from %02x', 0xe8, modbyte)
        modbyte = 0xe8
    if moddedbyte == hardware_setting:
        logging.debug('image hardware byte is already correct')
    else:
        logging.debug('changing modded byte %02x to %02x',
                      moddedbyte, hardware_setting)
        moddedbyte = hardware_setting
    return data[:6] + chr(moddedbyte) + data[7:10] + chr(modbyte) + data[11:]
def dump(filename=None):
    '''
    dump out a clone file to stdout, in chunks of 32 characters
    '''
    data = rawdump(filename)
    length = len(data)
    for index in range(0, length, 32):
        print(('%04x: %s' % (index, data[index:index + 32].encode('utf8'))))
def rawdump(filename=None):
    '''
    direct translation of clone file to character set 0
    '''
    data = read(filename)
    translation_table = CHARACTERS['vx7r'][:256]
    return ''.join([translation_table[ord(l)] for l in data])
def vxwrite(filename=None, port=None, freeband=False, modded=False):
    '''
    write out clone file to radio
    '''
    if freeband:
        data = checksum(freeband_mod(read(filename), modded))
    else:
        data = checksum(read(filename))
    if len(data) != DATASIZE:
        logging.error('incorrect data length: %d', len(data))
        sys.exit(1)
    input('''Instructions:
        1) While holding MON-F, power on VX-7R
        2) Hit V/M key on VX-7R
        3) Within 30 seconds, hit <Enter> key on computer keyboard ''')
    port.flushInput()
    port.flushOutput()
    serialwrite(port, data[:10])
    serialwrite(port, data[10:10 + 8])
    serialwrite(port, data[10 + 8:], final_block=True)
    port.close()
def vxread(filename=None, port=None):
    '''
    read data from radio and write to file or stdout
    '''
    input('''Instructions:
        1) While holding MON-F, power on VX-7R
        2) Hit <Enter> on computer keyboard
        3) Within 30 seconds, hit BAND key on VX-7R ''')
    port.flushInput()
    port.flushOutput()
    data = serialread(port, 10)
    data += serialread(port, 8)
    data += serialread(port, DATASIZE - 10 - 8, check=True)
    port.close()
    write(filename, checksum(data))
def chardump():
    '''
    display characters in same layout as graphic at hse.dyndns.org

    ASCII characters will be converted herein to fullwidth characters:

    "Range U+FF01–FF5E reproduces the characters of ASCII 21 to 7E as
     fullwidth forms. U+FF00 does not correspond to a fullwidth ASCII 20
     (space character), since that role is already fulfilled by
     U+3000 'ideographic space'.", from
    https://en.wikipedia.org/wiki/Halfwidth_and_Fullwidth_Forms_(Unicode_block)
    '''
    def transform(row):
        '''
        inner function to change row of characters to match as close as
        possible the form in Heian's chart

        the "C1", "C2", ... placeholders for programmable Kanji will show
        correctly for the expected 5 slots, and should work for up to 9.
        '''
        fullwidth = 0xff01 - 0x21
        placeholder = 0
        for index, character in enumerate(row):
            if character == '\0':
                row[index] = 'C%d' % (placeholder + 1)
                placeholder += 1
            elif character == ' ':
                row[index] = '\u3000'
            elif ord(character) < 0x7f:
                row[index] = chr(ord(character) + fullwidth)
            elif character == '\u221a':  # square root radical
                row[index] = character + ' ' + '\u0305'  # add overline
            elif ord(character) < 0x3000:
                row[index] = ' ' + character  # pad with a space
        return row
    columnheaders = '      +0 +1 +2 +3 +4 +5 +6 +7 +8 +9 +A +B +C +D +E +F'
    rowheaders = [' %02X : ' % n for n in range(0, 0x100, 0x10)]
    for character_set in (0, 1):
        print('character set %s' % character_set)
        print()
        print(columnheaders)
        offset = character_set * 256
        characters = CHARACTERS['vx7r'][offset:offset + 256].ljust(256, '\0')
        for row_number in range(16):
            row = list(characters[row_number * 16:(row_number * 16) + 16])
            print(rowheaders[row_number] + ' '.join(transform(row)))
        print()
if __name__ == '__main__':
    clone(*sys.argv[1:])
