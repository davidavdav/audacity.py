#!/usr/bin/env python
# (c) 2016 David A. van Leeuwen
##
## audacity/__init__.py .  Main routines for reading Audacity .aup files

import xml.etree.ElementTree as ET
import wave, os, numpy, struct

class aup:
    def __init__(self, aupfile):
        fqpath = os.path.join(os.path.curdir, aupfile)
        dir = os.path.dirname(fqpath)
        xml = open(aupfile)
        self.tree = ET.parse(xml)
        self.root = self.tree.getroot()
        self.rate = int(self.root.attrib["rate"])
        ns = {"ns":"http://audacity.sourceforge.net/xml/"}
        self.project = self.root.attrib["projname"]
        self.files = []
        for channel, wavetrack in enumerate(self.root.findall("ns:wavetrack", ns)):
            aufiles = []
            for b in wavetrack.iter("{%s}simpleblockfile" % ns["ns"]):
                filename = b.attrib["filename"]
                d1 = filename[0:3]
                d2 = "d" + filename[3:5]
                file = os.path.join(dir, self.project, d1, d2, filename)
                if not os.path.exists(file):
                    raise Warning("File missing in %s: %s" % (self.project, file))
                else:
                    aufiles.append((file, int(b.attrib["len"])))
            self.files.append(aufiles)
        self.nchannels = len(self.files)
        self.aunr = -1

    def open(self, channel):
        if not (0 <= channel < self.nchannels):
            raise ValueError("Channel number out of bounds")
        self.channel = channel
        self.aunr = 0
        return self

    def close(self):
        self.aunr = -1

    def read(self):
        if self.aunr < 0:
            raise IOError("File not opened")
        while self.aunr < len(self.files[self.channel]):
            with open(self.files[self.channel][self.aunr][0]) as fd:
                fd.seek(-self.files[self.channel][self.aunr][1] * 4, 2)
                data = fd.read()
                yield data
            self.aunr += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def towav(self, filename, channel):
        wav = wave.open(filename, "w")
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(self.rate)
        scale = 1 << 15
        with self.open(channel) as fd:
            for data in fd.read():
                shorts = numpy.short(numpy.clip(numpy.frombuffer(data, numpy.float32) * scale, -scale, scale-1))
                format = "<" + str(len(shorts)) + "h"
                wav.writeframesraw(struct.pack(format, *shorts))
            wav.writeframes("") ## sets length in wavfile
        wav.close()
