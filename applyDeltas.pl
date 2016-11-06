#!/usr/bin/perl
use POSIX;
use File::Basename;
use Digest::MD5;

sub md5 {
    my $filename = $_[0];
    open FILE, $filename;
    binmode(FILE);
    my $ctx = Digest::MD5->new;
    $ctx->addfile(*FILE);
    close FILE;
    return $ctx->hexdigest;
}

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

die "Usage: $0 deltas.tar.bz2 directoryToPatch\n"
	unless $#ARGV == 1;
die "\"$ARGV[0]\" is not a directory!\nUsage: $0 deltas.tar.bz2 directoryToPatch\n"
	unless -d "$ARGV[1]";
die "\"$ARGV[1]\" is not a file!\nUsage: $0 deltas.tar.bz2 directoryToPatch\n"
	unless -e "$ARGV[0]";
my $workDirDeltas = POSIX::tmpnam();
mkdir "$workDirDeltas" or die "Couldn't create $workDirDeltas ...";
my $dataDir = $ARGV[1];
$dataDir =~ s,/$,,;
my @dirs = split /\//, $dataDir;

my $currentDir = POSIX::getcwd();
chdir "$dataDir";
$dataDir = POSIX::getcwd();
chdir $currentDir;

mysystem("tar jxf \"$ARGV[0]\" -C \"$workDirDeltas\"");

chdir $workDirDeltas;
open DIRS, "find . -type d |";
while(<DIRS>) {
    chomp;
    next if /^\.$/ or /^\.\.$/;
    if ( ! -d "$dataDir/$_" ) {
	mkdir "$dataDir/$_" or die "Failed to create \"$dataDir/$_\"\n";
    }
}
close DIRS;

open FILES, "find . -type f |";
while(<FILES>) {
    chomp;
    if (/deltaRdiff@#$/) {
	my $targetName = $_;
	$targetName =~ s/\.deltaRdiff@#$//;
	die "Missing BASIS file \"$dataDir/$targetName\"\n"
	    unless -e "$dataDir/$targetName";
	rename "$dataDir/$targetName", "$dataDir/$targetName.rdiff_oldVersion";
	mysystem("rdiff patch \"$dataDir/$targetName.rdiff_oldVersion\" \"$_\" \"$dataDir/$targetName\"");
	my $md1 = md5("$dataDir/$targetName.rdiff_oldVersion");
	my $md2 = md5("$dataDir/$targetName");
	if ( $md1 eq $md2) {
	    unlink "$dataDir/$targetName.rdiff_oldVersion";
	}
    } else {
	# new file
	mysystem("mv \"$_\" \"$dataDir/$_\"");
    }
}
close FILES;

mysystem("rm -rf \"$workDirDeltas\"");
