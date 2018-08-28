#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import argparse


def dir_list(base):
    try:
        directories = os.walk(base).next()[1]
    except StopIteration:
        directories = []
    return directories


def file_list(base):
    try:
        files = os.walk(base).next()[2]
    except StopIteration:
        files = []
    return files

def dir_size(base):
    size = 0
    for dirpath, dirnames, filenames in os.walk(base):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            size += os.path.getsize(fp)
    return size


def print_spaced_list(l):
    """
    prints a list of lists in columns
    assumes constant number of columns
    """

    # calculate widths first
    widths = [0] * len(l[0])
    for v in l:
        for i, c in enumerate(v):
            c = str(c)
            if widths[i] < len(c):
                widths[i] = len(c)

    # hacky way to create format string
    fstr = ""
    for w in widths:
        fstr += "{{:<{}}} ".format(w)
    fstr = fstr.strip()

    for v in l:
        print(fstr.format(*v))

def humanize(v):
    sufs = ["", "K", "M", "G"]
    sufi = 0
    for i in range(3):
        if v > 1024:
            sufi += 1
            v /= 1024
        else:
            break
    return str(v) + sufs[sufi]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", action="store_true", help="sort results by size")
    parser.add_argument("-H", action="store_true", help="print sizes in human readable format")
    parser.add_argument("PATH", nargs="?", default=".")

    args = parser.parse_args()

    sizes = []

    # base files
    for f in file_list(args.PATH):
        sizes.append((os.path.getsize(os.path.join(args.PATH, f)), f))

    # recurse subdirectories
    for d in dir_list(args.PATH):
        sizes.append((dir_size(os.path.join(args.PATH, d)), d))

    if args.s:
        sizes_sorted = sorted(sizes, key=lambda f: f[0])
    else:
        sizes_sorted = sorted(sizes, key=lambda f: f[1])

    if args.H:
        sso = sizes_sorted
        sizes_sorted = []
        for i, v in enumerate(sso):
            sizes_sorted.append((humanize(sso[i][0]), sso[i][1]))

    print_spaced_list(sizes_sorted)


if __name__ == "__main__":
    sys.exit(main())
