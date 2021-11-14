from math import ceil

import numpy as np
import sys

byte_depth_to_dtype = {1: np.uint8, 2: np.uint16, 4: np.uint32, 8: np.uint64}

def roundup(x, base=1):
    return int(ceil(x / base)) * base

def str_to_bytes(x, charset=sys.getdefaultencoding(), errors="strict"):
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray, memoryview)):  # noqa
        return bytes(x)
    if isinstance(x, str):
        return x.encode(charset, errors)
    if isinstance(x, int):
        return str(x).encode(charset, errors)
    raise TypeError("Expected bytes")

def lsb_interleave_bytes(carrier, payload, num_lsb, truncate=False, byte_depth=1):
    """
    Interleave the bytes of payload into the num_lsb LSBs of carrier.
    :param carrier: carrier bytes
    :param payload: payload bytes
    :param num_lsb: number of least significant bits to use
    :param truncate: if True, will only return the interleaved part
    :param byte_depth: byte depth of carrier values
    :return: The interleaved bytes
    """

    plen = len(payload)
    payload_bits = np.zeros(shape=(plen, 8), dtype=np.uint8)
    payload_bits[:plen, :] = np.unpackbits(
        np.frombuffer(payload, dtype=np.uint8, count=plen)
    ).reshape(plen, 8)

    bit_height = roundup(plen * 8 / num_lsb)
    payload_bits.resize(bit_height * num_lsb)

    carrier_dtype = byte_depth_to_dtype[byte_depth]
    carrier_bits = np.unpackbits(
        np.frombuffer(carrier, dtype=carrier_dtype, count=bit_height).view(np.uint8)
    ).reshape(bit_height, 8 * byte_depth)

    carrier_bits[:, 8 * byte_depth - num_lsb: 8 * byte_depth] = payload_bits.reshape(
        bit_height, num_lsb
    )

    ret = np.packbits(carrier_bits).tobytes()
    return ret if truncate else ret + carrier[byte_depth * bit_height:]


def lsb_deinterleave_bytes(carrier, num_bits, num_lsb, byte_depth=1):
    """
    Deinterleave num_bits bits from the num_lsb LSBs of carrier.
    :param carrier: carrier bytes
    :param num_bits: number of num_bits to retrieve
    :param num_lsb: number of least significant bits to use
    :param byte_depth: byte depth of carrier values
    :return: The deinterleaved bytes
    """

    plen = roundup(num_bits / num_lsb)
    carrier_dtype = byte_depth_to_dtype[byte_depth]
    payload_bits = np.unpackbits(
        np.frombuffer(carrier, dtype=carrier_dtype, count=plen).view(np.uint8)
    ).reshape(plen, 8 * byte_depth)[:, 8 * byte_depth - num_lsb: 8 * byte_depth]
    return np.packbits(payload_bits).tobytes()[: num_bits // 8]


def lsb_interleave_list(carrier, payload, num_lsb):
    """Runs lsb_interleave_bytes with a List[uint8] carrier.
    This is slower than working with bytes directly, but is often
    unavoidable if working with libraries that require using lists."""
    bit_height = roundup(8 * len(payload) / num_lsb)
    carrier_bytes = np.array(carrier[:bit_height], dtype=np.uint8).tobytes()
    interleaved = lsb_interleave_bytes(carrier_bytes, payload, num_lsb, truncate=True)
    carrier[:bit_height] = np.frombuffer(interleaved, dtype=np.uint8).tolist()
    return carrier


def lsb_deinterleave_list(carrier, num_bits, num_lsb):
    """Runs lsb_deinterleave_bytes with a List[uint8] carrier.
    This is slower than working with bytes directly, but is often
    unavoidable if working with libraries that require using lists."""

    plen = roundup(num_bits / num_lsb)
    carrier_bytes = np.array(carrier[:plen], dtype=np.uint8).tobytes()
    deinterleaved = lsb_deinterleave_bytes(carrier_bytes, num_bits, num_lsb)
    return deinterleaved
