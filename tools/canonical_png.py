"""Portable RGB PNG encoding: no-filter rows and deterministic fixed Huffman.

The format has no variable compressor decisions, timestamps or ancillary fields.
Pillow remains the rasterizer; this writer deliberately trades bytes for stable
cross-platform fixture hashes. It is not a production upload encoder.
"""
from collections import deque
import struct
import zlib


def deflate(raw):
    """RFC1951 fixed tree + deterministic bounded greedy LZ77, no native compressor."""
    output, pending, bits = bytearray(), 0, 0

    def write(value, count):
        nonlocal pending, bits
        pending |= value << bits
        bits += count
        while bits >= 8:
            output.append(pending & 255)
            pending >>= 8
            bits -= 8

    def reversed_bits(value, width):
        result = 0
        for _ in range(width):
            result = (result << 1) | (value & 1)
            value >>= 1
        return result

    def symbol(value):
        if value <= 143:
            code, width = 0x30 + value, 8
        elif value <= 255:
            code, width = 0x190 + value - 144, 9
        elif value <= 279:
            code, width = value - 256, 7
        else:
            code, width = 0xc0 + value - 280, 8
        write(reversed_bits(code, width), width)

    lengths = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258]
    length_bits = [0]*8 + [1]*4 + [2]*4 + [3]*4 + [4]*4 + [5]*4 + [0]
    distances = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577]
    distance_bits = [0]*4 + [i for i in range(1,14) for _ in range(2)]
    write(3,3)  # Final block; fixed Huffman tree.
    index, positions = 0, {}
    while index < len(raw):
        best, distance = 0, 0
        key = raw[index:index+3]
        for previous in reversed(positions.get(key, ())):
            if index - previous > 32768:
                break
            length = 0
            while length < 258 and index+length < len(raw) and raw[previous+length] == raw[index+length]:
                length += 1
            if length > best:
                best, distance = length, index-previous
                if best == 258:
                    break
        count = best if best >= 3 else 1
        if best >= 3:
            code = max(i for i, base in enumerate(lengths) if base <= best)
            symbol(257+code)
            write(best-lengths[code],length_bits[code])
            code = max(i for i, base in enumerate(distances) if base <= distance)
            write(reversed_bits(code,5),5)
            write(distance-distances[code],distance_bits[code])
        else:
            symbol(raw[index])
        for cursor in range(index,index+count):
            positions.setdefault(raw[cursor:cursor+3],deque(maxlen=24)).append(cursor)
        index += count
    symbol(256)
    if bits:
        output.append(pending)
    return bytes(output)


def encode(image):
    if image.mode != 'RGB':
        raise ValueError('rgb_fixture_required')
    width, height = image.size
    pixels = image.tobytes()
    stride = width * 3
    raw = b''.join(b'\0' + pixels[y * stride:(y + 1) * stride] for y in range(height))
    stream = bytearray(b'\x78\x01')  # RFC1950: DEFLATE, 32K window.
    stream.extend(deflate(raw))
    stream.extend(struct.pack('>I', zlib.adler32(raw) & 0xffffffff))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', bytes(stream)) + chunk(b'IEND', b''))
