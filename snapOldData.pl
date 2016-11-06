#!/usr/bin/perl
use POSIX;
use File::Basename;

sub mysystem {
    my $cmd = $_[0];
    system($cmd);
    if ($? == -1) {
        return -1;
    }
    elsif ($? & 127) {
        return -1;
    }
    else {
        return ($? >> 8);
    }
}

die "Usage: $0 directory\n"
	unless $#ARGV == 0;
die "\"$ARGV[0]\" is not a directory!\nUsage: $0 directory\n"
	unless -d "$ARGV[0]";
my $workDir = POSIX::tmpnam();
mkdir "$workDir" or die "Couldn't create $workDir ...";
my $dataDir = $ARGV[0];
$dataDir =~ s,/$,,;
my @dirs = split /\//, $dataDir;
my $finalName = $dirs[$#dirs].".signatures.tar.bz2";

my $currentDir = POSIX::getcwd();
chdir $dataDir;
open DIRS, "find . -type d |";
while(<DIRS>) {
    chomp;
    next if /^\.$/ or /^\.\.$/;
    mkdir "$workDir/$_" or die "Failed to create \"$workDir/$_\"\n";
}
close DIRS;
open FILES, "find . -type f |";
while(<FILES>) {
    chomp;
    mysystem("rdiff signature \"$_\" \"$workDir/$_.signature\"");
}
close FILES;
chdir "$workDir";
my $compressedSignatures = POSIX::tmpnam().".tar.bz2";
mysystem("tar jcf \"$compressedSignatures\" ./");
chdir $currentDir;
mysystem("rm -rf \"$workDir\"");
mysystem("mv \"$compressedSignatures\" \"$currentDir/$finalName\"");
