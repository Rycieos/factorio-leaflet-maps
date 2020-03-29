#!/usr/bin/env python3

import argparse
import os
from glob import glob
import sys
import tarfile
import tempfile

from concurrent.futures import ProcessPoolExecutor, as_completed

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
        help="Disable printing the progress bar to stderr.",
    )
    parser.add_argument(
        "--no-progress-bar",
        "-q",
        action="store_true",
        help="Disable printing the progress bar to stderr.",
    )

    args = parser.parse_args(*argv)

    create_map(args.source, args.destination, args.threads, args.no_progress_bar)

def create_map(source, destination, threads=None, no_progress_bar=False):
    if os.path.isfile(source):
        archive = tarfile.open(source)
        tmpDir = tempfile.mkdtemp()
        archive.extractall(tmpDir)
        chunks = glob(tmpDir + '/chunk_*.jpg')
    else:
        chunks = glob(source + 'chunk_*.jpg')

    # Parallel Conversion of chunks into tiles
    with ProcessPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(chunk_to_tiles, destination, chunk) for chunk in chunks]

        kwargs = {
            'total': len(futures),
            'unit': 'tiles',
            'unit_scale': True,
            'disable': no_progress_bar,
        }
        for f in tqdm(as_completed(futures), **kwargs):
            pass

    for zoom in range(9, 0, -1):
        tiles = glob('{}{}/*/*.jpg'.format(destination, zoom+1))

        # Parallel processing of tiles to lower-zoom levels
        with ProcessPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(zoom_out, destination, tile, zoom) for tile in tiles]

            kwargs = {
                'total': len(futures),
                'unit': 'tiles',
                'unit_scale': True,
                'disable': no_progress_bar,
            }
            for f in tqdm(as_completed(futures), **kwargs):
                pass

def zoom_out(destination, filename, zoom):
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

def chunk_to_tiles(destination, chunk, chunkname=None):
    """Convert the chunk screenshot to Leaflet tiles at maximum zoom."""
    chunk_image = Image.open(chunk)
    if chunkname is None:
        chunk_x, chunk_y = chunk_coordinates(chunk)
    else:
        chunk_x, chunk_y = chunk_coordinates(chunkname)
    tile_x = chunk_x*4
    tile_y = chunk_y*4

    if not os.path.isfile(
            '{}{}/{}/{}.jpg'.format(destination, 10, tile_y, tile_x)):
        for x_adj in range(4):
            for y_adj in range(4):
                os.makedirs(
                    '{}{}/{}'.format(
                        sys.argv[2], 10, tile_y+y_adj),
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
    sys.exit(main(sys.argv))
