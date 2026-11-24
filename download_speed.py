#!/bin/python3

import argparse
import http.client
import math
import sys
import time
from urllib.parse import urlsplit
from urllib.request import urlopen


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT = 30


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure HTTP download speed.")
    parser.add_argument("url", help="HTTP or HTTPS URL to download")
    parser.add_argument("--count", type=int, default=REQUEST_COUNT,
                        help="number of downloads (default: %(default)s)")
    parser.add_argument("--timeout", type=float, default=TIMEOUT,
                        help="network operation timeout in seconds (default: %(default)s)")
    parser.add_argument("--delay", type=float, default=0,
                        help="pause between downloads in seconds (default: %(default)s)")
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be a positive integer")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")
    if not math.isfinite(args.delay) or args.delay < 0:
        parser.error("--delay must be a finite non-negative number")

    try:
        url = urlsplit(args.url)
        if url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError
    except ValueError:
        parser.error("expected an HTTP or HTTPS URL with a hostname")

    total_bytes = 0
    total_time = 0.0

    for number in range(1, args.count + 1):
        started = time.perf_counter()
        try:
            with urlopen(args.url, timeout=args.timeout) as response:
                remaining = response.length
                while chunk := response.read(CHUNK_SIZE):
                    total_bytes += len(chunk)
                    if remaining is not None:
                        remaining -= len(chunk)
                if remaining:
                    raise OSError(f"response ended {remaining} bytes early")
        except (OSError, http.client.HTTPException, ValueError) as error:
            print(f"Request {number}/{args.count} failed: {error}", file=sys.stderr)
            return 1

        total_time += time.perf_counter() - started
        if number < args.count and args.delay:
            time.sleep(args.delay)

    print(f"Average request time: {total_time / args.count:.3f} s")
    print(f"Total downloaded: {total_bytes} bytes")
    print(f"Download speed: {total_bytes / total_time / 1_000_000:.3f} MB/s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
