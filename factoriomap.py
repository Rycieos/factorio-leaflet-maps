#!/usr/bin/env python3

import argparse
import os
from glob import glob
from functools import partial
import sys
import tarfile

from multiprocessing import Pool

from PIL import Image
from tqdm import tqdm

def main(*argv):

    parser = argparse.ArgumentParser(description="Convert a TAR file or directory of Factorio screenshots into Leaflet map tiles.")

    parser.add_argument(
        "source",
        type=str,
        help="Directory or tar file to read Factorio screenshots from.",
    )
    parser.add_argument(
        "destination",
        type=str,
        help="Directory to store results in.",
    )
    parser.add_argument(
        "--threads",
        "-t",
        type=int,
        help="Number of threads to multithread over. Default is the number of CPU processors."
    )
    parser.add_argument(
        "--chunk_size",
        "-c",
        type=int,
        default=5,
        help="Size of chunks to send to a thread at a time.",
    )
    parser.add_argument(
        "--no-progress-bar",
        "-q",
        action="store_true",
        help="Disable printing the progress bar to stderr.",
    )

    args = parser.parse_args(*argv)

    create_map(args.source, args.destination, args.threads, args.chunk_size, args.no_progress_bar)

def create_map(source, destination, threads=None, chunk_size=None, no_progress_bar=False):

    if destination[-1] != '/':
        destination += '/'

    if os.path.isfile(source):
        pool = Pool(processes=threads, initializer=get_archive, initargs=(source,))
        with tarfile.open(source) as archive:
            tar_objects = archive.getmembers()
            chunks = [tar_object.name for tar_object in tar_objects if tar_object.isfile()]
        jobs = pool.imap_unordered(partial(tar_chunk_to_tiles, destination=destination), chunks, chunk_size)
    else:
        pool = Pool(processes=threads)
        chunks = glob(source + 'chunk_*.jpg')
        jobs = pool.imap_unordered(partial(chunk_to_tiles, destination=destination), chunks, chunk_size)

    kwargs = {
        'total': len(chunks),
        'unit': 'tiles',
        'unit_scale': True,
        'disable': no_progress_bar,
        'desc': '10',
    }
    for f in tqdm(jobs, **kwargs):
        pass

    pool.close()

    for zoom in range(9, 0, -1):
        tiles = glob('{}{}/*/*.jpg'.format(destination, zoom+1))

        # Parallel processing of tiles to lower-zoom levels
        with Pool(processes=threads) as pool:
            jobs = pool.imap_unordered(partial(zoom_out, destination=destination, zoom=zoom), tiles, chunk_size)

            kwargs = {
                'total': len(tiles),
                'unit': 'tiles',
                'unit_scale': True,
                'disable': no_progress_bar,
                'desc': ' {}'.format(zoom),
            }
            for f in tqdm(jobs, **kwargs):
                pass

def get_archive(archive_filename):
    global archive
    archive = tarfile.open(archive_filename)

def zoom_out(filename, destination, zoom):
    """Shrink and combine tiles to zoom view out."""

    source_x, source_y = tile_coordinates(filename)
    tile_x = source_x // 2
    tile_y = source_y // 2
    origin_x = tile_x * 2
    origin_y = tile_y * 2

    if not os.path.isfile(
            '{}{}/{}/{}.jpg'.format(destination, zoom, tile_y, tile_x)):
        os.makedirs('{}{}/{}'.format(destination, zoom, tile_y), exist_ok=True)

        tile_image = Image.new('RGB', (512, 512))
        for x_adj in range(2):
            for y_adj in range(2):
                try:
                    paste_image = Image.open('{}{}/{}/{}.jpg'.format(
                        destination, zoom+1, origin_y+y_adj, origin_x+x_adj))
                except FileNotFoundError:
                    paste_image = Image.new('RGB', (256, 256))

                tile_image.paste(
                    paste_image,
                    (x_adj*256, y_adj*256))

        tile_image.resize((256, 256)).save('{}{}/{}/{}.jpg'.format(
            destination, zoom, tile_y, tile_x))

def chunk_coordinates(filename):
    """Extract chunk coordinates from filename."""
    _, chunk_x, chunk_y = os.path.splitext(filename)[0].rsplit('_', 2)
    return (int(chunk_x), int(chunk_y))

def tile_coordinates(path):
    """Compute tile coordinates."""
    explosion = os.path.splitext(path)[0].split('/')
    return (int(explosion[-1]), int(explosion[-2]))

def tar_chunk_to_tiles(chunk, destination):
    data = archive.extractfile(chunk)
    chunk_to_tiles(data, destination, chunk)

def chunk_to_tiles(chunk, destination, chunkname=None):
    """Convert the chunk screenshot to Leaflet tiles at maximum zoom."""

    chunk_image = Image.open(chunk)

    chunk_x, chunk_y = chunk_coordinates(chunkname if chunkname else chunk)
    tile_x = chunk_x*4
    tile_y = chunk_y*4

    if not os.path.isfile(
            '{}{}/{}/{}.jpg'.format(destination, 10, tile_y, tile_x)):
        for x_adj in range(4):
            for y_adj in range(4):
                os.makedirs(
                    '{}{}/{}'.format(
                        destination, 10, tile_y+y_adj),
                    exist_ok=True)

                chunk_image.crop(
                    (
                        x_adj*256,
                        y_adj*256,
                        (x_adj+1)*256,
                        (y_adj+1)*256)
                    ).save('{}{}/{}/{}.jpg'.format(
                        destination, 10, tile_y+y_adj, tile_x+x_adj))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
