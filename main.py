import logging

import click

import steganography as LSBSteg

# enable logging output
logging.basicConfig(format="%(message)s", level=logging.INFO)
log = logging.getLogger("stego_lsb")
log.setLevel(logging.DEBUG)


# @click.group()
# @click.version_option()
# def main(args=None):
#     """Console script for stegolsb."""


# @main.command(context_settings=dict(max_content_width=120))
# @click.option("--hide", "-h", is_flag=True, help="To hide data in an image file")
# @click.option(
#     "--recover", "-r", is_flag=True, help="To recover data from an image file"
# )
# @click.option(
#     "--analyze",
#     "-a",
#     is_flag=True,
#     default=False,
#     show_default=True,
#     help="Print how much data can be hidden within an image",
# )
# @click.option(
#     "--input", "-i", "input_fp", help="Path to an bitmap (.bmp or .png) image"
# )
# @click.option("--secret", "-s", "secret_fp", help="Path to a file to hide in the image")
# @click.option("--output", "-o", "output_fp", help="Path to an output file")
# @click.option(
#     "--lsb-count",
#     "-n",
#     default=2,
#     show_default=True,
#     help="How many LSBs to use",
#     type=int,
# )
# @click.option(
#     "--compression",
#     "-c",
#     help="1 (best speed) to 9 (smallest file size)",
#     default=1,
#     show_default=True,
#     type=click.IntRange(1, 9),
# )
# @click.pass_context
# def steglsb(
#         ctx, hide, recover, analyze, input_fp, secret_fp, output_fp, lsb_count, compression
# ):
#     """Hides or recovers data in and from an image"""
#     try:

#         if hide:
#         elif recover:
#             LSBSteg.recover_data(input_fp, output_fp, lsb_count)

#         if not hide and not recover and not analyze:
#             click.echo(ctx.get_help())
#     except ValueError as e:
#         log.debug(e)
#         click.echo(ctx.get_help())

LSBSteg.hide_data('/home/felipe/Pictures/download_original.bmp', '/home/felipe/Pictures/encrypt.txt', '/home/felipe/Pictures/teste.bmp', 2, 1)
LSBSteg.recover_data('/home/felipe/Pictures/teste.bmp', '/home/felipe/Pictures/', 2)