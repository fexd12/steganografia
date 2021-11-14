
from threading import Thread
from steganography import Steg
from filesystem import Operations
from argparse import ArgumentParser

import trio,logging,sys,pyfuse3

# enable logging output
logging.basicConfig(format="%(message)s", level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def init_logging(debug=False):
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(threadName)s: '
                                  '[%(name)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    if debug:
        handler.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

def parse_args(args):
    '''Parse command line'''

    parser = ArgumentParser()

    parser.add_argument('source', type=str,
                        help='Directory tree to mirror')
    parser.add_argument('mountpoint', type=str,
                        help='Where to mount the file system')
    parser.add_argument('password', type=str,
                        help='password to enc/dec')
    parser.add_argument('picture', type=str,
                        help='picture"s path to embed')
    # parser.add_argument('--debug', action='store_true', default=False,
    #                     help='Enable debugging output')
    # parser.add_argument('--debug-fuse', action='store_true', default=False,
    #                     help='Enable FUSE debugging output')

    return parser.parse_args(args)

def main():
    options = parse_args(sys.argv[1:])
    # init_logging(options.debug)
    operations = Operations(options.source,options.password,options.picture,options.source)

    log.debug('Mounting...')
    fuse_options = set(pyfuse3.default_options)
    fuse_options.add('fsname=operations')
    # if options.debug_fuse:
    #     fuse_options.add('debug')
    pyfuse3.init(operations, options.mountpoint, fuse_options)
    
    # Steg(options.password,options.picture,options.mountpoint)
      
    try:
        log.debug('Entering main loop..')

        trio.run(pyfuse3.main)
    except Exception as e:
        print(e)
        log.exception('main raised exception: %s', e)
        
    finally:
        log.debug('hiding data')
        
        operations.hide_data()

        log.debug('Unmounting..')

        pyfuse3.close(unmount=True)

if __name__ == '__main__':
    main()

    # steg = Steg('password','/home/felipe/Pictures/download_original.bmp', '/home/felipe/Pictures/encrypt.txt','/home/felipe/Pictures/teste.bmp','/home/felipe/Pictures/')

    # steg.hide_data()
    # steg.recover_data()
