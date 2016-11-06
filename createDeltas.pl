#!/usr/bin/perl
use POSIX;
use File::Basename;

sub mysystem {
    my $cmd = $_[0];
    system($cmd);
    if ($? == -1) {
        die "Failed to execute:\n$cmd\n";
    }
    elsif ($? & 127) {
        die "Failed to execute:\n$cmd\n";
    }
    else {
        if ($? >> 8) {
	    die "Failed to execute:\n$cmd\n";
	}
    }
}

die "Usage: $0 directory snapShotOfOldDir.tar.bz2\n"
	unless $#ARGV == 1;
die "\"$ARGV[0]\" is not a directory!\nUsage: $0 directory snapShotOfOldDir.tar.bz2\n"
	unless -d "$ARGV[0]";
die "\"$ARGV[1]\" is not a file!\nUsage: $0 directory snapShotOfOldDir.tar.bz2\n"
	unless -e "$ARGV[1]";
my $workDirSignatures = POSIX::tmpnam();
mkdir "$workDirSignatures" or die "Couldn't create $workDirSignatures ...";
my $workDirDeltas = POSIX::tmpnam();
mkdir "$workDirDeltas" or die "Couldn't create $workDirDeltas ...";
my $dataDir = $ARGV[0];
$dataDir =~ s,/$,,;
my @dirs = split /\//, $dataDir;
my $finalName = $dirs[$#dirs].".deltas.tar.bz2";

my $currentDir = POSIX::getcwd();

mysystem("tar jxf \"$ARGV[1]\" -C \"$workDirSignatures\"");

chdir $dataDir;
open DIRS, "find . -type d |";
while(<DIRS>) {
    chomp;
    next if /^\.$/ or /^\.\.$/;
    mkdir "$workDirDeltas/$_" or die "Failed to create \"$workDir/$_\"\n";
}
close DIRS;

open FILES, "find . -type f |";
while(<FILES>) {
    chomp;
    if ( ! -e "$workDirSignatures/$_.signature" ) {
	# new file
	mysystem("cp \"$_\" \"$workDirDeltas/$_\"");
    } else {
	mysystem("rdiff delta \"$workDirSignatures/$_.signature\" \"$_\" \"$workDirDeltas/$_.deltaRdiff@#\"");
    }
}
close FILES;

chdir "$workDirDeltas";
my $compressedDelts = POSIX::tmpnam().".tar.bz2";
mysystem("tar jcf \"$compressedDelts\" ./");
chdir $currentDir;
mysystem("rm -rf \"$workDirDeltas\"");
mysystem("rm -rf \"$workDirSignatures\"");
mysystem("mv \"$compressedDelts\" \"$currentDir/$finalName\"");
