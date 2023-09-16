#!/usr/bin/env python3

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



def humanize_size(size):
    sufs = ["", "K", "M", "G"]
    sufi = 0
    for i in range(3):
        if size > 1024:
            sufi += 1
            size //= 1024
        else:
            break
    return str(size) + sufs[sufi]


def humanize_sizes(sizes, humanize):
    if humanize:
        for size in sizes:
            size["size"] = humanize_size(size["size"])
    return sizes


def sort_sizes(sizes, sort_by_size):
    if sort_by_size:
        sizes = sorted(sizes, key=lambda f: f["size"])
    else:
        sizes = sorted(sizes, key=lambda f: f["path"].lower())
    return sizes


def islink_or_isjunction(path):
    return os.path.islink(path) or (NTFS and ntfsutils.junction.isjunction(path))


def list_dirs(path):
    directories = []
    with os.scandir(path) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_dir():
                directories.append(entry.name)
    return directories


def list_files(path):
    files = []
    with os.scandir(path) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file():
                files.append(entry.name)
    return files


def file_size(path, skiplinks):
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


def dir_size(path, skiplinks, sort_by_size, humanize, save_subs):
    size = 0
    subs = []
    linkpath = ""
    for dirpath, dirnames, filenames in os.walk(path):
        # if we are skipping links, skip everything that starts with dirpath
        if skiplinks:
            if islink_or_isjunction(dirpath):
                linkpath = dirpath
            if linkpath and dirpath.startswith(linkpath):
                continue
        for f in filenames:
            fp = os.path.join(dirpath, f)
            subs.append(file_size(fp, skiplinks))
            size += subs[-1]["size"]
    return {"size": size, "path": path, "subs": humanize_sizes(sort_sizes(subs, sort_by_size) if save_subs else [], humanize)}


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



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version="%(prog)s 1.1")
    parser.add_argument("-s", action="store_true", help="sort results by size")
    parser.add_argument("-H", action="store_true", help="print sizes in human readable format")
    parser.add_argument("-l", action="store_true", help="follow links (symlinks and junctions)")
    parser.add_argument("-j", action="store_true", help="print json")
    parser.add_argument("PATH", nargs="?", default=".")

    args = parser.parse_args()

    sizes = []

    # base files
    for f in list_files(args.PATH):
        fp = os.path.join(args.PATH, f)
        sizes.append(file_size(fp, not args.l))

    # recurse subdirectories
    for d in list_dirs(args.PATH):
        sizes.append(dir_size(os.path.join(args.PATH, d), not args.l, args.s, args.H, args.j))

    sort_sizes(sizes, args.s)
    humanize_sizes(sizes, args.H)

    if args.j:
        print(json.dumps(sizes, indent=2))
    else:
        print_spaced_list([("*" if "subs" in s else " ", s["size"], s["path"]) for s in sizes])


if __name__ == "__main__":
    sys.exit(main())
