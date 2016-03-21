# audacity.py
A Python tool to extract .wav files from Audacity .aup files

This package can read an Audacity `.aup` file, and can extract the audio for a given channel and save as a `.wav` file. 

## Command line usage

Extract the second channel from an `.aup` file
```sh
python -m audacity --channel 2 file.aup file-2.wav
```

On the command line, the first channel is `1`. 

## API

### `aup` class

```python
import audacity
aup = audacity.aup("file.aup")
```

### open file for reading, and read blocks of data:
```python 
channel=0
with aup.open(channel) as fd:
  data = fd.read()
  print len(data) ## float32 numbers
```

In the Python API, the first channel is `0`.  

### convert to `.wav`

```python
channel=0
aup.towav("file.wav", channel)
```
