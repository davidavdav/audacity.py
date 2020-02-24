#!/usr/bin/env python
# (c) 2016 David A. van Leeuwen
##
## audacity/__init__.py .  Main routines for reading Audacity .aup files

from __future__ import annotations

import xml.etree.ElementTree as ET
import wave, os, numpy, struct


class Channel:
    def __init__(self, aup:Aup, channel_no:int) -> None:
        self.aup = aup
        self.channel_no = channel_no
        self.aunr = 0
        self.offset = 0

    def close(self):
        self.aunr = -1

    ## a linear search (not great)
    def seek(self, pos):
        if self.aunr < 0:
            raise IOError("File not opened")
        s = 0
        i = 0
        length = 0
        for i, f in enumerate(self.aup.files[self.channel_no]):
            s += f[1]
            if s > pos:
                length = f[1]
                break
        if pos >= s:
            raise EOFError("Seek past end of file")
        self.aunr = i
        self.offset = pos - s + length

    def read(self):
        if self.aunr < 0:
            raise IOError("File not opened")
        while self.aunr < len(self.aup.files[self.channel_no]):
            current_chunk = self.aup.files[self.channel_no][self.aunr]
            with open(current_chunk[0], 'rb') as fd:
                fd.seek((self.offset - current_chunk[1]) * 4, 2)
                data = fd.read()
                yield data
            self.aunr += 1
            self.offset = 0

    def towav(self, filename, start=0, stop=None, bit_depth=16) -> None:
        """Allowed bit_depth values: 16 or 32."""
        # The reason for not supporting 24-bit depth is there's no struct.pack format that supports
        # 3-byte-wide integers and one can easily down-convert afterwards.
        assert bit_depth in {16, 32}
        wav = wave.open(filename, "w")
        wav.setnchannels(1)
        wav.setsampwidth(bit_depth // 8)
        wav.setframerate(self.aup.rate)
        scale = 1 << (bit_depth - 1)
        numpy_type = numpy.short if bit_depth == 16 else numpy.intc
        if stop:
            length = int(self.aup.rate * (stop - start)) ## number of samples to extract

        self.seek(int(self.aup.rate * start))

        for data in self.read():
            values = numpy_type(numpy.clip(numpy.frombuffer(data, numpy.float32) * scale, -scale, scale-1))
            if stop and len(values) > length:
                values = values[range(length)]
            format = "<" + str(len(values)) + ("h" if bit_depth == 16 else "i")
            wav.writeframesraw(struct.pack(format, *values))
            if stop:
                length -= len(values)
                if length <= 0:
                    break
        wav.writeframes(b'') ## sets length in wavfile
        wav.close()


class Aup:
    def __init__(self, aupfile):
        fqpath = os.path.join(os.path.curdir, aupfile)
        dir = os.path.dirname(fqpath)
        xml = open(aupfile)
        self.tree = ET.parse(xml)
        self.root = self.tree.getroot()
        self.rate = int(float(self.root.attrib["rate"]))
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
                    raise IOError("File missing in %s: %s" % (self.project, file))
                else:
                    aufiles.append((file, int(b.attrib["len"])))
            self.files.append(aufiles)
        self.nchannels = len(self.files)
        self.aunr = -1

    def open(self, channel):
        if not (0 <= channel < self.nchannels):
            raise ValueError("Channel number out of bounds")
        return Channel(self, channel)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def towav(self, filename, channel, start=0, stop=None, bit_depth=16):
        """for backwards compatibility
        """
        return self.open(channel).towav(filename, start, stop, bit_depth)