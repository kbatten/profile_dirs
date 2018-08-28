#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import argparse

try:
    import ntfsutils.junction
    NTFS = True
except ImportError:
    NTFS = False



def islink_or_isjunction(path):
    return os.path.islink(path) or (NTFS and ntfsutils.junction.isjunction(path))


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


def file_size(path, skiplinks=True):
    if skiplinks and islink_or_isjunction(path):
        return 0

    if not NTFS:
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    try:
        return os.path.getsize(path)
    except WindowsError:
        return 0
    except OSError:
        return 0


def dir_size(base, skiplinks=True):
    size = 0
    linkpath = ""
    for dirpath, dirnames, filenames in os.walk(base):
        # if we are skipping links, skip everything that starts with dirpath
        if skiplinks:
            if islink_or_isjunction(dirpath):
                linkpath = dirpath
            if linkpath and dirpath.startswith(linkpath):
                continue
        for f in filenames:
            fp = os.path.join(dirpath, f)
            size += file_size(fp, skiplinks)
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
    parser.add_argument("-l", action="store_true", help="follow links (symlinks and junctions)")
    parser.add_argument("PATH", nargs="?", default=".")

    args = parser.parse_args()

    sizes = []

    # base files
    for f in file_list(args.PATH):
        fp = os.path.join(args.PATH, f)
        sizes.append((file_size(fp, not args.l), f))

    # recurse subdirectories
    for d in dir_list(args.PATH):
        sizes.append((dir_size(os.path.join(args.PATH, d), not args.l), d))

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
