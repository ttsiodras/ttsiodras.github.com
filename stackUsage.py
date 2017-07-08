#!/usr/bin/env python2
"""
Utility to detect recursive calls and calculate total stack usage per function
(via following the call graph). Works for x86 and SPARC/Leon binaries.

Published under the GPL, (C) 2011 Thanassis Tsiodras
Suggestions/comments: ttsiodras@gmail.com
"""

import os
import re
import sys
import operator


class Matcher:
    """regexp helper"""
    def __init__(self, pattern, flags=0):
        self._pattern = re.compile(pattern, flags)
        self._hit = None

    def match(self, line):
        self._hit = re.match(self._pattern, line)
        return self._hit

    def search(self, line):
        self._hit = re.search(self._pattern, line)
        return self._hit

    def group(self, idx):
        return self._hit.group(idx)


def CheckForCycles(callGraph, badNodes):
    """Detect cycles in function call graphs"""
    def journey(path):
        node = path[-1]
        if node not in callGraph:
            return
        if callGraph[node] is None:  # has been marked as recursive,
                                     # so propagate the marking
            badNodes[:] = path[:]
            return
        neighbours = callGraph[node]
        for neighbour in neighbours:
            if neighbour in path:
                badNodes[:] = path[path.index(neighbour):] + [neighbour]
                return
            journey(path + [neighbour])
    for node, v in callGraph.items():
        if v:  # if not marked as recursive...
            journey([node])
            if badNodes:
                return


def findStackUsage(fn, stackUsagePerFunction, callGraph, cache={}):
    """
    Calculate the total stack usage of each function,
    taking into account who it calls
    """
    #  pylint: disable=W0102
    if fn in cache:  # memoization
        return cache[fn]
    if fn not in stackUsagePerFunction:
        return 0
    if fn not in callGraph or not callGraph[fn]:
        cache[fn] = stackUsagePerFunction[fn]
        return stackUsagePerFunction[fn]
    totalStackUsage = max(  # the largest of the possible call chains
        ((stackUsagePerFunction[fn] +
            findStackUsage(x, stackUsagePerFunction, callGraph))
         for x in callGraph[fn]))
    cache[fn] = totalStackUsage
    return totalStackUsage


def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print "Usage: %s ELFbinary" % sys.argv[0]
        sys.exit(1)
    binarySignature = os.popen("file \"%s\"" % sys.argv[1]).readlines()[0]
    x86 = Matcher(r'ELF 32-bit LSB.*80.86')
    x64  = Matcher(r'ELF 64-bit LSB.*x86-64')
    leon = Matcher(r'ELF 32-bit MSB.*SPARC')
    arm = Matcher(r'ELF 32-bit LSB.*ARM')
    if x86.search(binarySignature):
        objdump = 'objdump'
        nm = 'nm'
        functionNamePattern = Matcher(r'^(\S+) <([a-zA-Z0-9_]+?)>:')
        callPattern = Matcher(r'^.*call\s+\S+\s+<([a-zA-Z0-9_]+)>')
        stackUsagePattern = Matcher(r'^.*[add|sub]\s+\$(0x\S+),%esp')
    elif x64.search(binarySignature):
        objdump = 'objdump'
        nm = 'nm'
        functionNamePattern = Matcher(r'^(\S+) <([a-zA-Z0-9_]+?)>:')
        callPattern = Matcher(r'^.*callq\s+\S+\s+<([a-zA-Z0-9_]+)>')
        stackUsagePattern = Matcher(r'^.*[add|sub]\s+\$(0x\S+),%rsp')
    elif leon.search(binarySignature):
        objdump = 'sparc-elf-objdump'
        nm = 'sparc-elf-nm'
        functionNamePattern = Matcher(r'^(\S+) <([a-zA-Z0-9_]+?)>:')
        callPattern = Matcher(r'^.*call\s+\S+\s+<([a-zA-Z0-9_]+)>')
        stackUsagePattern = Matcher(
            r'^.*save.*%sp, (-([0-9]{2}|[3-9])[0-9]{2}), %sp')
    elif arm.search(binarySignature):
        objdump = 'arm-eabi-objdump'
        nm = 'arm-eabi-nm'
        functionNamePattern = Matcher(r'^(\S+) <([a-zA-Z0-9_]+?)>:')
        callPattern = Matcher(r'^.*bl\s+\S+\s+<([a-zA-Z0-9_]+)>')
        stackUsagePattern = Matcher(
            r'^.*sub.*sp, sp, (#[0-9][0-9]*)')
    else:
        print "Unknown signature:", binarySignature
        sys.exit(1)

    # Store .text symbol offsets and sizes (use nm)
    offsetOfSymbol = {}
    for line in os.popen(
            nm + " \"" + sys.argv[1] + "\" | grep ' [Tt] '").readlines():
        offset, unused, symbol = line.split()
        offsetOfSymbol[symbol] = int(offset, 16)
    sizeOfSymbol = {}
    lastOffset = 0
    lastSymbol = None
    for symbol, offset in sorted(
            offsetOfSymbol.iteritems(), key=operator.itemgetter(1)):
        if lastSymbol:
            sizeOfSymbol[lastSymbol] = offset-lastOffset
        lastSymbol = symbol
        lastOffset = offset
    sizeOfSymbol[lastSymbol] = 2**31  # allow last .text symbol to roam free

    # Parse disassembly to create callgraph (use objdump -d)
    functionName = ""
    stackUsagePerFunction = {}
    callGraph = {}
    insideFunctionBody = False
    currentFunctionStackSize = 0

    offsetPattern = Matcher(r'^([0-9A-Za-z]+):')
    for line in os.popen(objdump + " -d \"" + sys.argv[1] + "\"").readlines():
        # Have we matched a function name yet?
        if functionName != "":
            # Yes, update "insideFunctionBody" boolean by checking
            # the current offset against the length of this symbol,
            # stored in sizeOfSymbol[functionName]
            offset = offsetPattern.match(line)
            if offset:
                offset = int(offset.group(1), 16)
                if functionName in offsetOfSymbol:
                    startOffset = offsetOfSymbol[functionName]
                    insideFunctionBody = \
                        insideFunctionBody and \
                        (offset - startOffset) < sizeOfSymbol[functionName]

        # Check to see if we see a new function:
        # 08048be8 <_functionName>:
        fn = functionNamePattern.match(line)
        if fn:
            offset = int(fn.group(1), 16)
            functionName = fn.group(2)
            callGraph.setdefault(functionName, set())
            # make sure this is the function we found with nm
            # UPDATE: no, can't do - if a symbol is of local file scope
            # (i.e. if it was declared with 'static')
            # then it can appear in multiple places...
            #
            #if functionName in offsetOfSymbol:
            #    if offsetOfSymbol[functionName] != offset:
            #        print "Weird,", functionName, \
            #            "is not at offset reported by", nm
            #        print hex(offsetOfSymbol[functionName]), hex(offset)
            insideFunctionBody = True
            foundFirstCall = False
            stackUsagePerFunction[functionName] = 0

        # If we're inside a function body
        # (i.e. offset is not out of symbol size range)
        if insideFunctionBody:
            # Check to see if we have a call
            #  8048c0a:       e8 a1 03 00 00       call   8048fb0 <frame_dummy>
            call = callPattern.match(line)
            if functionName != "" and call:
                foundFirstCall = True
                calledFunction = call.group(1)
                callGraph[functionName].add(calledFunction)

            # Check to see if we have a stack reduction opcode
            #  8048bec:       83 ec 04                sub    $0x46,%esp
            if functionName != "" and not foundFirstCall:
                stackMatch = stackUsagePattern.match(line)
                if stackMatch:
                    value = stackMatch.group(1)
                    if value.startswith("0x"):
                        # sub    $0x46,%esp
                        value = int(stackMatch.group(1), 16)
                        if value > 2147483647:
                            # unfortunately, GCC may also write:
                            # add    $0xFFFFFF86,%esp
                            value = 4294967296-value
                    elif value.startswith("#"):
                        # sub sp, sp, #1024
                        value = int(value[1:])
                    else:
                        # save  %sp, -104, %sp
                        value = -int(value)
                    stackUsagePerFunction[functionName] += value

    #for fn,v in stackUsagePerFunction.items():
    #   print fn,v
    #   print "CALLS:", callGraph[fn]

    # First, detect cycles and remove "bad" nodes from calculations
    # (recursive calls would lead to infinite stack usage)
    while True:
        badNodes = []
        CheckForCycles(callGraph, badNodes)
        if not badNodes:
            break
        lastStep = badNodes[-1] + " (recursive)"
        badNodes.pop()
        badNodes.append(lastStep)
        print "Detected cycle and will ignore these functions:\n\t", \
              "\n\t".join(badNodes)
        for n in set(badNodes):
            stackUsagePerFunction[n] = None     # marked as recursive
            callGraph[n] = None                 # marked as recursive

    print "Cumulative stack usage per function:"
    # Then, navigate the graph to calculate stack needs per function
    results = []
    for fn, value in stackUsagePerFunction.items():
        if value is not None:
            results.append(
                (fn, findStackUsage(fn, stackUsagePerFunction, callGraph)))
        #else:
        #    results.append((fn, 'recursive'))
    for fn, value in sorted(results, key=operator.itemgetter(1)):
        print "%10s: %s" % (value, fn)

if __name__ == "__main__":
    main()
