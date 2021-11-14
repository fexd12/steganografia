import sys,logging

from PIL import Image
from utils import (
    lsb_deinterleave_list,
    lsb_interleave_list,
    roundup,
    str_to_bytes
)
from crypto import Crypto

log = logging.getLogger(__name__)

class Steg():
    def __init__(self,passwd,input_image_path,output_file_path,num_lsb=None,compression_level=None) -> None:
        self.cry = Crypto(passwd)
        
        self.input_image_path = input_image_path
        
        self.output_file_path = output_file_path
        
        self.num_lsb = num_lsb or 2
        self.compression_level = compression_level or 1
        
    def prepare_hide(self):
        """Prepare files for reading and writing for hiding data."""
        image = Image.open(self.input_image_path)
        input_file = open(self.input_file_path, "rb")
        return image, input_file
        
    def prepare_recover(self):
        """Prepare files for reading and writing for recovering data."""
        steg_image = Image.open(self.input_image_path)
        # output_file = open('', "wb+")
        return steg_image

    def max_bits_to_hide(self,image):
        """Returns the number of bits we're able to hide in the image using
        num_lsb least significant bits."""
        # 3 color channels per pixel, num_lsb bits per color channel.
        return int(3 * image.size[0] * image.size[1] * self.num_lsb)

    def bytes_in_max_file_size(self,image):
        """Returns the number of bits needed to store the size of the file."""
        return roundup(self.max_bits_to_hide(image).bit_length() / 8)

    def hide_message_in_image(self,message):
        """Hides the message in the input image and returns the modified
        image object.
        """
        # start = time()
        # in some cases the image might already be opened
        image = Image.open(self.input_image_path)
        # if isinstance(input_image, Image.Image):
        #     image = input_image
        # else:
        #     image = Image.open(input_image)

        num_channels = len(image.getdata()[0])
        flattened_color_data = [v for t in image.getdata() for v in t]

        # We add the size of the input file to the beginning of the payload.

        data_encry_before = message

        data_encry_after = self.cry.encrypt(data_encry_before)

        message_size = len(data_encry_after)

        file_size_tag = message_size.to_bytes(
            self.bytes_in_max_file_size(image), byteorder=sys.byteorder
        )
        
        data = file_size_tag + data_encry_after

        # log.debug("Files read".ljust(30) + f" in {time() - start:.2f}s")

        max_bits = self.max_bits_to_hide(image)
        
        if 8 * len(data) > max_bits:
            raise ValueError(
                f"Only able to hide {max_bits // 8} bytes "
                + f"in this image with {self.num_lsb} LSBs, but {len(data)} bytes were requested"
            )

        # start = time()
        flattened_color_data = lsb_interleave_list(flattened_color_data, data, self.num_lsb)
        # log.debug(f"{message_size} bytes hidden".ljust(30) + f" in {time() - start:.2f}s")

        # start = time()
        image.putdata(list(zip(*[iter(flattened_color_data)] * num_channels)))
        # log.debug("Image overwritten".ljust(30) + f" in {time() - start:.2f}s")
        image.save(self.input_image_path, compress_level=self.compression_level)

        return image


    def recover_message_from_image(self,input_image):
        """Returns the message from the steganographed image"""
        # start = time()
        if isinstance(input_image, Image.Image):
            steg_image = input_image
        else:
            steg_image = Image.open(input_image)

        color_data = [v for t in steg_image.getdata() for v in t]

        file_size_tag_size = self.bytes_in_max_file_size(steg_image)
        tag_bit_height = roundup(8 * file_size_tag_size / self.num_lsb)

        bytes_to_recover = int.from_bytes(
            lsb_deinterleave_list(
                color_data[:tag_bit_height], 8 * file_size_tag_size, self.num_lsb
            ),
            byteorder=sys.byteorder,
        )

        maximum_bytes_in_image = (
                self.max_bits_to_hide(steg_image) // 8 - file_size_tag_size
        )
        if bytes_to_recover > maximum_bytes_in_image:
            print(
                "This image appears to be corrupted.\n"
                + f"It claims to hold {bytes_to_recover} B, "
                + f"but can only hold {maximum_bytes_in_image} B with {self.num_lsb} LSBs"
            )
            # raise
        # log.debug("Files read".ljust(30) + f" in {time() - start:.2f}s")

        # start = time()
        data = lsb_deinterleave_list(
            color_data, 8 * (bytes_to_recover + file_size_tag_size), self.num_lsb
        )[file_size_tag_size:]
        # log.debug(
        #     f"{bytes_to_recover} bytes recovered".ljust(30) + f" in {time() - start:.2f}s"
        # )
        return data

