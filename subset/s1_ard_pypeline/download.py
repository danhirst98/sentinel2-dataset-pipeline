import argparse
import json
import logging
import posixpath
import urllib
from queue import Queue
from threading import Thread

from s1_ard_pypeline import get_config
from s1_ard_pypeline.utils import s3_utils


def parse_args():
    parser = argparse.ArgumentParser(description='download a list of un-authenticated urls and put them in s3')
    parser.add_argument("-input", help="file containing json list of urls to fetch", required=True)
    parser.add_argument("-output", help="path to output files in s3", required=True)
    parser.add_argument("-threads", help="number of download threads to use.", default="4")

    _args = parser.parse_args()

    return _args


def read_url_list(path):
    with open(path, 'r') as f:
        return json.load(f)


def create_destination_url(target_path, in_url):
    filename = posixpath.basename(urllib.parse.urlparse(in_url).path)

    return posixpath.join(target_path, filename)


def download_file(source_url, destination_url, _client):
    response = urllib.request.urlopen(source_url)
    _client.s3_client.put_object(Body=response.read(), Bucket=get_config("S3", "bucket"), Key=destination_url)


def worker():
    client = s3_utils.S3Utils()
    while True:
        item = q.get()
        dest = create_destination_url(args.output, item)

        if not client.list_files(dest):
            logging.info(f"~{q.qsize()} remaining. downloading {item} to {dest}")
            download_file(item, dest, client)
        else:
            logging.info(f"~{q.qsize()} remaining. Skipping due to existence {item} at {dest}")
        q.task_done()


if __name__ == '__main__':
    args = parse_args()

    entries = read_url_list(args.input)
    logging.info(f"found {len(entries)} to download...")

    q = Queue()
    for i in range(int(args.threads)):
        t = Thread(target=worker)
        t.daemon = True
        t.start()

    for url in entries:
        q.put(url)

    q.join()
