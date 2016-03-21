#!/usr/bin/env python
# (c) 2016 David A. van Leeuwen
## extract .wav channel from .aup file
##
## usage: python -m audacity --channel 1 file.aup file.wav


import argparse
from . import Aup

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--channel", type=int, default=1)
    p.add_argument("aupfile")
    p.add_argument("wavfile")
    args = p.parse_args()
    a = Aup(args.aupfile)
    a.towav(args.wavfile, args.channel-1)
