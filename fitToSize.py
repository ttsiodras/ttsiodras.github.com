#!/usr/bin/env python
import sys
import os
import shutil

def panic(msg):
    sys.stderr.write(msg)
    sys.exit(1)

def main():
    if len(sys.argv) != 4:
        panic('Usage: %s <inputDir> <outputDir> <sizeInMB>\n' % sys.argv[0])

    for workDir in sys.argv[1:3]:
        if not os.path.isdir(workDir):
            panic("'%s' is not a directory!\n" % workDir)

    try:
        g_maxSize = int(sys.argv[3])
    except:
        panic("Last parameter must be the size in MB, not '%s'!\n" % sys.argv[2])
        
    candidates = []
    fileSizes = []
    for name in os.listdir(sys.argv[1]):
        try:
            name = os.path.dirname(sys.argv[1]) + os.sep + name
            if os.path.isfile(name):
                sizeRoundedUPInMB = (os.path.getsize(name) + 1048575) / 1048576
                fileSizes.append(sizeRoundedUPInMB)
                candidates.append([sizeRoundedUPInMB, name])
        except:
            print "Ignoring ", name
            continue
    
    print "Directory contained", len(fileSizes), "items..."
    print "File sizes to fit in", g_maxSize, "MB were:", fileSizes

    optimalResult = {}
    lastStep = {}
    for containerSize in xrange(0, g_maxSize+1):  # containerSize takes values 0 .. g_maxSize
	for idx,fileSize in enumerate(fileSizes):
	    cellCurrent = (containerSize, idx)
	    cellOnTheLeftOfCurrent = (containerSize, idx-1)
	    if containerSize<fileSize: 
		optimalResult[cellCurrent] = optimalResult.get(cellOnTheLeftOfCurrent,0)
		lastStep[cellCurrent] = lastStep.get(cellOnTheLeftOfCurrent,0)
	    else:
		# If I use file of column "idx", then the remaining space is...
		remainingSpace = containerSize - fileSize
		# ...and for that remaining space, the optimal result using the first idx-1 columns was:
		optimalResultOfRemainingSpace = optimalResult.get((remainingSpace, idx-1),0)
		if optimalResultOfRemainingSpace + fileSize > optimalResult.get(cellOnTheLeftOfCurrent,0):
		    # we improved the best result, using the column "idx"!
		    optimalResult[cellCurrent] = optimalResultOfRemainingSpace + fileSize
		    lastStep[cellCurrent] = fileSize
		else:
		    # no improvement...
		    optimalResult[cellCurrent] = optimalResult[cellOnTheLeftOfCurrent]
		    lastStep[cellCurrent] = lastStep.get(cellOnTheLeftOfCurrent,0)

    finalChosenList = []
    print "Attainable:", optimalResult[(g_maxSize, len(fileSizes)-1)]
    total = optimalResult[(g_maxSize, len(fileSizes)-1)]
    countingUp = 0
    while total>0:
	lastFileSize = lastStep[(total, len(fileSizes)-1)]
	# print total, "removing", lastFileSize
        if lastFileSize != 0:
            for pair in candidates:
                if pair[0] == lastFileSize:
                    finalChosenList.append(pair[1])
		    countingUp += lastFileSize
                    print "+ %9d MB = %9d MB (%s)" % (lastFileSize, countingUp, pair[1])
                    candidates.remove(pair)
                    break
            else:
		assert(False) # we should have found the file
	total -= lastFileSize
    for final in finalChosenList:
        shutil.move(final, os.path.dirname(sys.argv[2]))

if __name__ == "__main__":
    main()
