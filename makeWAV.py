#!/usr/bin/env python2
import os

FREQ = 22050

def emitSilence(f, ms):
    print("Silence for", ms, "ms")
    ms = 1 if ms > 5000 else ms
    f.write(''.join([chr(0)]*int(22050*ms/1000)))

def emitFreq(f, freq, ms):
    print("Emitting", freq, "HZ for", ms, "ms")
    samples = int(FREQ/freq)
    samples_on = int(samples/2)
    data = [chr(255)]*samples_on
    data += [chr(0)]*(samples - samples_on)
    time_of_one_period = 1000. * samples/FREQ
    while ms > 0:
        f.write(''.join(data))
        ms -= time_of_one_period

def main():
    f = open("some.raw", "wb")
    freq, tick = 0, 0
    oldFreq, oldTick = -1, 0
    for line in open("notes"):
        freq, tick = line.split('Hz @ ')
        tick = int(tick.strip())
        freq = int(float(freq))
        if freq != oldFreq:
            ms = tick-oldTick
            if oldFreq in (-1, 1190000):
                print("Silence", ms)
                emitSilence(f, ms)
            else:
                print("Freq", oldFreq, ms)
                emitFreq(f, oldFreq, ms)
            oldTick = tick
        oldFreq = freq
    f.close()
    os.system("sox -r 22050 -e unsigned -b 8 -c 1 some.raw some.wav")
    os.unlink("some.raw")


if __name__ == "__main__":
    main()
