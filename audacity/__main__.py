#!/usr/bin/env python

import argparse
from . import aup

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--channel", type=int, default=1)
    p.add_argument("aupfile")
    p.add_argument("wavfile")
    args = p.parse_args()
    a = aup(args.aupfile)
    a.towav(args.wavfile, args.channel-1)
