import os
import sys
# from time import time
import logging

from PIL import Image

from utils import (
    lsb_deinterleave_list,
    lsb_interleave_list,
    roundup,
)

from crypto import Crypto

cry = Crypto('password')

log = logging.getLogger(__name__)

def _str_to_bytes(x, charset=sys.getdefaultencoding(), errors="strict"):
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray, memoryview)):  # noqa
        return bytes(x)
    if isinstance(x, str):
        return x.encode(charset, errors)
    if isinstance(x, int):
        return str(x).encode(charset, errors)
    raise TypeError("Expected bytes")


def prepare_hide(input_image_path, input_file_path):
    """Prepare files for reading and writing for hiding data."""
    image = Image.open(input_image_path)
    input_file = open(input_file_path, "rb")
    return image, input_file


def prepare_recover(steg_image_path, output_file_path):
    """Prepare files for reading and writing for recovering data."""
    steg_image = Image.open(steg_image_path)
    # output_file = open('', "wb+")
    return steg_image


def get_filesize(path):
    """Returns the file size in bytes of the file at path"""
    return os.stat(path).st_size


def max_bits_to_hide(image, num_lsb):
    """Returns the number of bits we're able to hide in the image using
    num_lsb least significant bits."""
    # 3 color channels per pixel, num_lsb bits per color channel.
    return int(3 * image.size[0] * image.size[1] * num_lsb)


def bytes_in_max_file_size(image, num_lsb):
    """Returns the number of bits needed to store the size of the file."""
    return roundup(max_bits_to_hide(image, num_lsb).bit_length() / 8)


def hide_message_in_image(input_image, message,name, num_lsb):
    """Hides the message in the input image and returns the modified
    image object.
    """
    # start = time()
    # in some cases the image might already be opened
    if isinstance(input_image, Image.Image):
        image = input_image
    else:
        image = Image.open(input_image)

    num_channels = len(image.getdata()[0])
    flattened_color_data = [v for t in image.getdata() for v in t]

    # We add the size of the input file to the beginning of the payload.

    data_encry_before = _str_to_bytes(name) + _str_to_bytes('/000/') + _str_to_bytes(message)

    data_encry_after = cry.encrypt(data_encry_before)

    message_size = len(data_encry_after)

    file_size_tag = message_size.to_bytes(
        bytes_in_max_file_size(image, num_lsb), byteorder=sys.byteorder
    )
    
    data = file_size_tag + data_encry_after
    
    ######################################################
    #data_encrypted here.
    # data = cry.encrypt(data)
    ######################################################

    # log.debug("Files read".ljust(30) + f" in {time() - start:.2f}s")

    if 8 * len(data) > max_bits_to_hide(image, num_lsb):
        raise ValueError(
            f"Only able to hide {max_bits_to_hide(image, num_lsb) // 8} bytes "
            + f"in this image with {num_lsb} LSBs, but {len(data)} bytes were requested"
        )

    # start = time()
    flattened_color_data = lsb_interleave_list(flattened_color_data, data, num_lsb)
    # log.debug(f"{message_size} bytes hidden".ljust(30) + f" in {time() - start:.2f}s")

    # start = time()
    # PIL expects a sequence of tuples, one per pixel
    image.putdata(list(zip(*[iter(flattened_color_data)] * num_channels)))
    # log.debug("Image overwritten".ljust(30) + f" in {time() - start:.2f}s")
    return image


def hide_data(
        input_image_path, input_file_path, steg_image_path, num_lsb, compression_level
):
    """Hides the data from the input file in the input image."""
    if input_image_path is None:
        raise ValueError("LSBSteg hiding requires an input image file path")
    if input_file_path is None:
        raise ValueError("LSBSteg hiding requires a secret file path")
    if steg_image_path is None:
        raise ValueError("LSBSteg hiding requires an output image file path")

    image, input_file = prepare_hide(input_image_path, input_file_path)
    image = hide_message_in_image(image, input_file.read(),input_file.name.split('/')[-1], num_lsb)
    input_file.close()
    image.save(steg_image_path, compress_level=compression_level)


def recover_message_from_image(input_image, num_lsb):
    """Returns the message from the steganographed image"""
    # start = time()
    if isinstance(input_image, Image.Image):
        steg_image = input_image
    else:
        steg_image = Image.open(input_image)

    color_data = [v for t in steg_image.getdata() for v in t]

    file_size_tag_size = bytes_in_max_file_size(steg_image, num_lsb)
    tag_bit_height = roundup(8 * file_size_tag_size / num_lsb)

    bytes_to_recover = int.from_bytes(
        lsb_deinterleave_list(
            color_data[:tag_bit_height], 8 * file_size_tag_size, num_lsb
        ),
        byteorder=sys.byteorder,
    )

    maximum_bytes_in_image = (
            max_bits_to_hide(steg_image, num_lsb) // 8 - file_size_tag_size
    )
    if bytes_to_recover > maximum_bytes_in_image:
        raise ValueError(
            "This image appears to be corrupted.\n"
            + f"It claims to hold {bytes_to_recover} B, "
            + f"but can only hold {maximum_bytes_in_image} B with {num_lsb} LSBs"
        )

    # log.debug("Files read".ljust(30) + f" in {time() - start:.2f}s")

    # start = time()
    data = lsb_deinterleave_list(
        color_data, 8 * (bytes_to_recover + file_size_tag_size), num_lsb
    )[file_size_tag_size:]
    # log.debug(
    #     f"{bytes_to_recover} bytes recovered".ljust(30) + f" in {time() - start:.2f}s"
    # )
    return data


def recover_data(steg_image_path, output_file_path, num_lsb):
    """Writes the data from the steganographed image to the output file"""
    if steg_image_path is None:
        raise ValueError("LSBSteg recovery requires an input image file path")
    if output_file_path is None:
        raise ValueError("LSBSteg recovery requires an output file path")

    steg_image = prepare_recover(steg_image_path, output_file_path)
    data = recover_message_from_image(steg_image, num_lsb)
    # print(data)
    
    ########################################
    #data decrypted here
    data = cry.decrypt(data)
    ########################################
    
    # start = time()
    data_  = data.decode('utf-8').split('/000/')
    # print(data)

    output_file = open(output_file_path + data_[0]+'_decrypted', "wb+")
    output_file.write(_str_to_bytes(data_[1]))
    output_file.close()
    # log.debug("Output file written".ljust(30) + f" in {time() - start:.2f}s")