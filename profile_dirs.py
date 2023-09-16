#!/usr/bin/env python3

from __future__ import print_function

import os
import sys
import argparse
from collections import namedtuple
import json

try:
    import ntfsutils.junction
    NTFS = True
except ImportError:
    NTFS = False


def islink_or_isjunction(path):
    return os.path.islink(path) or (NTFS and ntfsutils.junction.isjunction(path))


def dir_list(base):
    directories = []
    with os.scandir(base) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_dir():
                directories.append(entry.name)
    return directories

def humanize_sizes(sizes, h):
    if h:
        for size in sizes:
            size["size"] = humanize(size["size"])
    return sizes

def sort_sizes(sizes, sort_by_size):
    if sort_by_size:
        sizes_sorted = sorted(sizes, key=lambda f: f["size"])
    else:
        sizes_sorted = sorted(sizes, key=lambda f: f["path"].lower())
    return sizes_sorted
        

def file_list(base, sort):
    files = []
    with os.scandir(base) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file():
                files.append(entry.name)
    return files


def file_size(path, skiplinks=True):
    if skiplinks and islink_or_isjunction(path):
        return 0

    size = 0
    if not NTFS:
        try:
            size = os.path.getsize(path)
        except OSError:
            pass
    else:
        try:
            size = os.path.getsize(path)
        except (WindowsError, OSError):
            pass

    return {"size": size, "path": path}


def dir_size(base, skiplinks, sort, h, j):
    size = 0
    subs = []
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
            file_profile = file_size(fp, skiplinks)
            subs.append(file_profile)
            size += file_profile["size"]
    return {"size": size, "path": base, "subs": humanize_sizes(sort_sizes(subs, sort) if j else [], h)}


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
            v //= 1024
        else:
            break
    return str(v) + sufs[sufi]



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    parser.add_argument("-s", action="store_true", help="sort results by size")
    parser.add_argument("-H", action="store_true", help="print sizes in human readable format")
    parser.add_argument("-l", action="store_true", help="follow links (symlinks and junctions)")
    parser.add_argument("-j", action="store_true", help="print json")
    parser.add_argument("PATH", nargs="?", default=".")

    args = parser.parse_args()

    sizes = []

    # base files
    for f in file_list(args.PATH, args.s):
        fp = os.path.join(args.PATH, f)
        sizes.append(file_size(fp, not args.l))

    # recurse subdirectories
    for d in dir_list(args.PATH):
        sizes.append(dir_size(os.path.join(args.PATH, d), not args.l, args.s, args.H, args.j))

    sort_sizes(sizes, args.s)
    humanize_sizes(sizes, args.H)

    if args.j:
        print(json.dumps(sizes, indent=2))
    else:
        print_spaced_list([("*" if "subs" in s else " ", s["size"], s["path"]) for s in sizes])


if __name__ == "__main__":
    sys.exit(main())
