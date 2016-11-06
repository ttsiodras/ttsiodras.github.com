#!/usr/bin/env python
import os
import sys
import shutil
import tarfile
import tempfile

def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s directory\n" % sys.argv[0])
        sys.exit(1)
    if not os.path.isdir(sys.argv[1]):
        sys.stderr.write("\"%s\" is not a directory!\nUsage: %s directory\n" \
            (sys.argv[1], sys.argv[0]))
    workDir = tempfile.mkdtemp()
    dataDir = sys.argv[1]
    dataDir = os.path.abspath(sys.argv[1])
    finalName = os.path.abspath(dataDir).split(os.sep)[-1] + ".signatures.tar.bz2"
    tar = tarfile.open(finalName, "w:bz2")

    for direntry in os.walk(dataDir):
        dirpath, dirnames, filenames = direntry
        common = os.path.commonprefix([dirpath, dataDir])
        srcPrefix  = dirpath + os.sep
        destPrefix = workDir + os.sep + dirpath[len(common):] + os.sep
        for dirname in dirnames:
            os.mkdir(destPrefix + dirname)
        for filename in filenames:
            if not os.path.islink(srcPrefix + filename):
                if 0 != os.system("rdiff signature \"%s\" \"%s\"" % \
                        (srcPrefix + filename, destPrefix + filename + ".signature")):
                    sys.exit(1)
                tar.add(\
                    destPrefix + filename + ".signature", \
                    "." + dirpath[len(common):] + os.sep + filename + ".signature")
                print "." + dirpath[len(common):] + os.sep + filename
    tar.close()
    #if 0 != os.system("tar jcf \"%s\" -C \"%s\" ." % (finalName, workDir)):
    #   sys.exit(1)
    shutil.rmtree(workDir, True) # ignore errors in removing

if __name__ == "__main__":
    if sys.argv.count("-pdb") != 0:
        sys.argv.remove("-pdb")
        import pdb
        pdb.run('main()')
    else:
        main()
