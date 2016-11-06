#!/usr/bin/env python
#
# Utility to detect recursive calls and calculate total stack usage per function
# (via following the call graph). Works for x86 and SPARC/Leon binaries.
#
# Published under the GPL, (C) 2011 Thanassis Tsiodras
# Suggestions/comments: ttsiodras@gmail.com

import sys, os, re, operator

# regexp helper
class Matcher:
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

# Detect cycles in function call graphs
def CheckForCycles(callGraph, badNodes):
    def journey(path):
        node = path[-1]
        if not callGraph.has_key(node):
            return
        if callGraph[node] == None: # has been marked as recursive - propagate marking
            badNodes[:] = path[:]
            return
        neighbours = callGraph[node]
        for neighbour in neighbours:
            if neighbour in path:
                badNodes[:] = path[path.index(neighbour):] + [neighbour]
                return
            journey(path + [neighbour])
    for node, v in callGraph.items():
        if v: # if not marked as recursive...
            journey([node])
            if badNodes:
                return

# Calculate the total stack usage of each function, taking into account who it calls
def findStackUsage(foo, stackUsagePerFunction, callGraph, cache={}):
    if cache.has_key(foo): # memoization
        return cache[foo]
    if not stackUsagePerFunction.has_key(foo):
        return 0
    if not callGraph.has_key(foo) or not callGraph[foo]:
        cache[foo] = stackUsagePerFunction[foo]
        return stackUsagePerFunction[foo]
    totalStackUsage = max( # the largest of the possible call chains
        ((stackUsagePerFunction[foo] + findStackUsage(x, stackUsagePerFunction, callGraph))
         for x in callGraph[foo]))
    cache[foo] = totalStackUsage
    return totalStackUsage

def main():
    if len(sys.argv)<2 or not os.path.exists(sys.argv[1]):
        print "Usage: %s ELFbinary" % sys.argv[0]
        sys.exit(1)
    binarySignature = os.popen("file \"%s\"" % sys.argv[1]).readlines()[0]
    x86  = Matcher(r'ELF 32-bit LSB.*80.86')
    x64  = Matcher(r'ELF 64-bit LSB.*x86-64')
    leon = Matcher(r'ELF 32-bit MSB.*SPARC')
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
        stackUsagePattern = Matcher(r'^.*save.*%sp, (-([0-9]{1,})), %sp')
    else:
        print "Unknown signature:", binarySignature
        sys.exit(1)

    # Store .text symbol offsets and sizes (use nm)
    offsetOfSymbol = {}
    for line in os.popen(nm + " \"" + sys.argv[1] + "\" | grep ' [Tt] '").readlines():
        offset, _, symbol = line.split()
        offsetOfSymbol[symbol] = int(offset, 16)
    sizeOfSymbol = {}
    lastOffset = 0
    lastSymbol = None
    for symbol, offset in sorted(offsetOfSymbol.iteritems(), key=operator.itemgetter(1)):
        if lastSymbol:
            sizeOfSymbol[lastSymbol] = offset-lastOffset
        lastSymbol = symbol
        lastOffset = offset
    sizeOfSymbol[lastSymbol] = 2**31 # allow last .text symbol to roam free

    # Parse disassembly to create callgraph (use objdump -d)
    foundStack = False
    functionName = ""
    stackUsagePerFunction = {}
    callGraph = {}
    insideFunctionBody = False

    offsetPattern = Matcher(r'^([0-9A-Za-z]+):')
    for line in os.popen(objdump + " -d \"" + sys.argv[1] + "\"").readlines():
        # Have we matched a function name yet?
        if functionName != "":
            # Yes, update "insideFunctionBody" boolean by checking the current offset
            # against the length of this symbol, stored in sizeOfSymbol[functionName]
            offset = offsetPattern.match(line)
            if offset:
                offset = int(offset.group(1), 16)
                if offsetOfSymbol.has_key(functionName):
                    insideFunctionBody = insideFunctionBody and (offset-offsetOfSymbol[functionName])<sizeOfSymbol[functionName]

        # Check to see if we see a new function:
        # 08048be8 <_functionName>:
        foo = functionNamePattern.match(line)
        if foo:
            offset = int(foo.group(1), 16)
            functionName = foo.group(2)
            callGraph.setdefault(functionName, set())
            # make sure this is the function we found with nm
            if offsetOfSymbol.has_key(functionName):
                if offsetOfSymbol[functionName] != offset:
                    print "Weird,", functionName, "is not at offset reported by", nm
                    print hex(offsetOfSymbol[functionName]), hex(offset)
            insideFunctionBody = True
            foundStack = False

        # If we're inside a function body (i.e. offset is not out of symbol size range)
        if insideFunctionBody:
            # Check to see if we have a call
            #  8048c0a:       e8 a1 03 00 00          call   8048fb0 <frame_dummy>
            call = callPattern.match(line)
            if functionName != "" and call:
                calledFunction = call.group(1)
                callGraph[functionName].add(calledFunction)
            
            # Check to see if we have the first stack reduction opcode
            #  8048bec:       83 ec 04                sub    $0x46,%esp
            if not foundStack and functionName != "":
                stackMatch = stackUsagePattern.match(line)
                if stackMatch:
                    # make sure we dont re-update the stackusage for this function
                    foundStack = True 
                    value = stackMatch.group(1)
                    if value.startswith("0x"):
                        # sub    $0x46,%esp
                        value = int(stackMatch.group(1), 16)
                        if value > 2147483647:
                            # unfortunately, GCC may also write:
                            # add    $0xFFFFFF86,%esp
                            value = 4294967296-value
                    else:
                        # save  %sp, -104, %sp
                        value = -int(value)
                    stackUsagePerFunction[functionName] = value

    #for foo,v in stackUsagePerFunction.items():
    #   print foo,v
    #   print "CALLS:", callGraph[foo]

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
        print "Detected cycle and will ignore these functions:\n\t", "\n\t".join(badNodes)
        for n in set(badNodes):
            stackUsagePerFunction[n] = None     #  marked as recursive
            callGraph[n] = None                 #  marked as recursive

    print "Cumulative stack usage per function:"
    # Then, navigate the graph to calculate stack needs per function
    results = []
    for foo, value in stackUsagePerFunction.items():
        if value != None:
            results.append((foo, findStackUsage(foo, stackUsagePerFunction, callGraph)))
        #else:
        #    results.append((foo, 'recursive'))
    for foo, value in sorted(results, key=operator.itemgetter(1)):
        print "%10s: %s" % (value, foo)
    
if __name__ == "__main__":
    main()
