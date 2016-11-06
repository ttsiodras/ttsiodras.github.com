#!/usr/bin/perl -w
use strict;

my $g_AudioBitrate = 96;

sub InitLOG {
    if ( ! -d "tmp") { system("mkdir tmp"); }
    open LOG, ">>tmp/log.txt";
    my $stamp = `date`;
    chomp $stamp;
    print LOG "$stamp: Encoding session starts\n";
    close LOG;
}

sub myLOG {
    my $cmd = $_[0];
    if ( ! -d "tmp") { system("mkdir tmp"); }
    open LOG, ">>tmp/log.txt";
    my $stamp = `date`;
    chomp $stamp;
    print LOG $stamp.": ".$cmd."\n";
    close LOG;
}

sub mySystem {
    my $cmd = $_[0];
    if ( ! -d "tmp") { system("mkdir tmp"); }
    open LOG, ">>tmp/log.txt";
    my $stamp = `date`;
    chomp $stamp;
    print LOG $stamp.": ".$cmd."\n";
    close LOG;
    system($cmd);
}

sub answerMe {
    my $prompt = $_[0];
    my $providedAnswers = $_[1];
    my %possibleAnswers;
    foreach my $ans (@$providedAnswers) {
	$possibleAnswers{uc($ans)}=1;
	$possibleAnswers{lc($ans)}=1;
    }
    while(1) {
	print $prompt;
	my $ans = <STDIN>;
	chomp $ans;
	if (defined($possibleAnswers{$ans})) {
	    return lc($ans);
	}
    }
}

sub ChooseDimensions {

    my $selectedHeight = undef;

    my $bitsPerSec = $_[0];
    my $srcFile = $_[1];
    my $encodeAsInterlaced = $_[2];
    my $selectedCodec = $_[3];

    my $inaspect = undef;
    my $aspect = undef;
    my $maxW = undef;
    my $maxH = undef;
    myLOG("mplayer -nosound -frames 10 $srcFile 2>&1 |");
    open ASPECT, "mplayer -nosound -frames 10 $srcFile 2>&1 |";
    while(<ASPECT>) {
	if (/^VO.*? (\d+)x(\d+) => (\d+)x(\d+)/) {
	    $inaspect = $1/$2;
	    $aspect = $3/$4;
	    $maxW = $3;
	    $maxH = $4;
	}
    }
    close ASPECT;
    die "Could not detect input MPEG2 aspect ratio\n" 
	unless defined($aspect);

    print "MPEG2 Aspect Ratio: ".sprintf("%5.2f", $aspect)."\n"; 

    my $cropW = undef;
    my $cropH = undef;
    my $fps = undef;
    if (open SETTINGS, "tmp/videoCropDeinterAndScale") {
	my $line = <SETTINGS>;
	chomp $line;
	if ($line =~ /detc/) {
	    $fps = 23.976;
	}
	if ($line =~ /-vf crop=(\d+):(\d+)/) {
	    $cropW = $1;
	    $cropH = $2;
	}
	close SETTINGS;
    }
    die "No crop settings found!\n"
	unless defined $cropW;

    if (!defined($fps)) {
	myLOG("mplayer -nosound -frames 10 -vo null $srcFile 2>&1 |");
	open FPS, "mplayer -nosound -frames 10 -vo null $srcFile 2>&1 |";
	while(<FPS>) {
	    if (/(\d+)[,\.](\d+)\s+fps/) {
		$fps = $1 + $2/1000.0;
	    }
	}
	close FPS;
	
    }
    while(!defined($fps)) {
	print "Could not detect, please provide FPS: "; $fps = <STDIN>;
    }
    print "FPS: ".sprintf("%6.3f", $fps)."\n"; 

    $aspect = $cropW*($aspect/$inaspect)/$cropH;
    my $cropDeinterAndScale;
    while(1) {

	my $height = undef;
	while(!defined($height)) {
	    my %options;
	    my $idx=1;
	    for(my $y = 160; $y<=$maxH; $y += 8) {
		my $x = 16 * sprintf("%d", ($aspect * $y + 9)/16);
		#if ($x > $maxW) {
		#    next;
		#}
		my $bpp = $bitsPerSec/($fps * $x * $y);
		if ($bpp < 0.1) { next; }

		if ($selectedCodec eq "2" and ($y % 16)) {
		    next;
		}
		$options{$idx}=$y;
		print $idx++;
		print ". $x x $y ($bpp)\n";
	    }
	    $idx--;
	    print "Choose a number (1 - $idx) : ";
	    my $ans = <STDIN>; chomp $ans;
	    $height = $options{$ans};
	}
	my $width = 16 * sprintf("%d", ($aspect * $height + 9)/16);

	$cropDeinterAndScale = `cat tmp/videoCropDeinterAndScale`;
	chomp $cropDeinterAndScale;
	
	if ($encodeAsInterlaced == 1) {
	    if ($cropDeinterAndScale =~ s/scale=\d+:\d+/scale=$width:$height:1/ ) {
		;
	    } else {
		$cropDeinterAndScale =~ s/(-vf \S+)(.*)/$1,scale=$width:$height:1$2/ ;
	    }
	} else {
	    if ($cropDeinterAndScale =~ s/scale=\d+:\d+/scale=$width:$height/ ) {
		;
	    } else {
		$cropDeinterAndScale =~ s/(-vf \S+)(.*)/$1,scale=$width:$height$2/ ;
	    }
	}
	my $tempSettings = $cropDeinterAndScale;
	$tempSettings =~ s/-ofps [\d\.]+//;
	print "Will now spawn mplayer so that you can check your frame settings\nPress ENTER when ready...";
	my $dum = <STDIN>;
	#print "Spawning mplayer -nosound -really-quiet $tempSettings $srcFile\n";
	mySystem("mplayer -nosound -really-quiet $tempSettings $srcFile >/dev/null 2>&1");

	if ("y" eq answerMe( "Did you like your frame settings (Y/N) ? ", [ "Y", "N" ])) {
	    $selectedHeight = $height;
	    last;
	}
    }

    mySystem("mv tmp/videoCropDeinterAndScale tmp/videoCropDeinterAndScale.old");
    open NEWCONF, ">tmp/videoCropDeinterAndScale";
    print NEWCONF $cropDeinterAndScale;
    close NEWCONF;

    return $selectedHeight;
}

sub ChooseAID {
    my $srcFile = $_[0];
    my $aid;
    while(1) {
	$aid = undef;
	while(!defined($aid)) {
	    my $idx = 1;
	    my %audioList;
	    myLOG("mplayer -v -frames 0 $srcFile 2>&1 |");
	    open AIDSLIST, "mplayer -v -frames 0 $srcFile 2>&1 |";
	    print "Available audio channels:\n";
	    while(<AIDSLIST>) {
		if (/audio stream: (\d+)/) {
		    $audioList{$idx} = $1;
		    print "  $idx. $1\n";
		    $idx++;
		}
	    }
	    close AIDSLIST;
	    $idx--;
	    if ($idx == 1) {
		print "Automatically choosing audio channel ".$audioList{(keys %audioList)[0]}."\n";
		return $audioList{(keys %audioList)[0]};
	    } elsif ($idx == 0) {
		die "No audio found!\nAre you sure $srcFile exists?\n";
	    }
	    print "Choose a number (1 - $idx) : ";
	    my $ans = <STDIN>; chomp $ans;
	    $aid = $audioList{$ans};
	}
	mySystem("mplayer -aid $aid $srcFile");
	if ("y" eq answerMe( "Was this the audio channel you wanted? (Y/N) ", [ "Y", "N" ])) {
	    last;
	}
    }
    return $aid;
}

sub main {
    die "Usage: $0 <inputFile> <sizeInMBytes> <outputName>\n"
	unless ((@ARGV == 3) and (-f $ARGV[0]));

    for my $prg ('mplayer', 'mencoder', 'tcscan', 'mpegdemux', 'oggenc', 'ogginfo', 'mkvmerge') {
	die "Missing '$prg' from PATH!\n"
	    unless system("which $prg >/dev/null 2>&1 ") == 0;
	print "Successfully located $prg\n"
    }

    my $srcFile = $ARGV[0];
    my $aid = ChooseAID($srcFile);
    my $totalSize = $ARGV[1]*1048576;
    my $outputName = $ARGV[2];
    my $baseSubtitle = $outputName;
    $baseSubtitle =~ s/\.mkv$//;
    if ($baseSubtitle eq $outputName) {
	print "Output filename must end in .mkv\n";
	exit(1);
    }

    my $selectedCodec = answerMe("What codec should I utilize:\n 1. XVID\n 2. X264\nChoose: ", [ "1", "2" ]);

    InitLOG;

    # Verify that specified AID exists
    my %aids;
    myLOG("dd if=$srcFile bs=1M count=2 2>/dev/null | mpegdemux -c|");
    open VERIFY, "dd if=$srcFile bs=1M count=2 2>/dev/null | mpegdemux -c|";
    while(<VERIFY>) {
	if (/sid=\w+\[(\w+)\]\s+MPEG2\s+pts=\d+\[([\d\.]+)\]$/) {
	    $aids{lc($1)} = $2;
	    print "Identified AID 0x$1 successfully\n";
	} elsif (/sid=e0\s+MPEG2\s+pts=\d+\[([\d\.]+)\]$/) {
	    $aids{"e0"} = $1;
	    print "Identified Video stream successfully\n";
	}
    }
    close VERIFY;
    my $hexAid = lc(sprintf("%x", $aid));
    if (!defined($aids{$hexAid})) {
	die "Couldn't find specified AID ($aid)!\n";
    }
    if (!defined($aids{"e0"})) {
	#die "Couldn't find video stream (0xe0)!\n";
	$aids{"e0"}=$aids{$hexAid};
	print "Warning: Video stream PTS'ed at 0x$hexAid ...\n";
    }

    if (! -e "tmp" ) { mySystem("mkdir tmp"); }

    # Determine movie duration, through subtitle extraction or plain playback
    print "\nWill now spawn mplayer to detect subtitle streams...\n";
    print "Navigate with PgUp/PgDown to movie parts with subtitles...\n";
    print "Hit ENTER when ready... and ESC to quit movie playback...";
    my $ans=<STDIN>;
    myLOG("mplayer -sid 0 -v -quiet $srcFile 2>/dev/null |");
    my %subtitleIDs;
    open SUBTITLES, "mplayer -sid 0 -v -quiet $srcFile 2>/dev/null |";
    while(<SUBTITLES>) {
	chomp;
	if (/Found subtitle:\s*(\d+)/) {
	    $subtitleIDs{$1}=(scalar keys %subtitleIDs) + 1;
	    print "Found a subtitle!\n";
	}
    }
    close SUBTITLES;
    my $seconds = undef;
    print "\n";
    if ((scalar keys %subtitleIDs) > 0) {
	my @selections;
	while(1) {
	    my $cnt = 0;
	    my %availableSelections;
	    foreach my $subID (sort keys %subtitleIDs) {
		$cnt++; 
		print sprintf("%2d. Subtitle %s\n", $cnt, $subID);
		$availableSelections{$cnt} = $subID;
	    }
	    print "Selected so far: ", @selections, "\n";
	    print "Choose a subtitle (1-$cnt, 0 to abort): ";
	    my $ans = <STDIN>;
	    chomp $ans;
	    if ($ans == 0) {
		last;
	    }
	    my $sid = $availableSelections{$ans};
	    if (defined $sid) {
		system("mplayer -sid $sid $srcFile >/dev/null 2>&1");
		my $ans = answerMe("Do you really want this subtitle (Y/N) ? ", ["Y", "N"]);
		if ($ans eq "y") {
		    push @selections, $sid;
		} 
	    }
	}
	my $subidx = 0;
	if (scalar @selections) {
	    print "Extracting subtitles...\n";
	    for my $sid (@selections) {
		myLOG("mencoder -ovc frameno -nosound -vobsubout $baseSubtitle -vobsuboutindex $subidx -sid $sid -o /dev/null $srcFile |");
		open MOVIELENGTHSUB, "mencoder -ovc frameno -nosound -vobsubout $baseSubtitle -vobsuboutindex $subidx -sid $sid -o /dev/null $srcFile |";
		while(<MOVIELENGTHSUB>) {
		    if (/(\d+)\.\d+\s+secs/) {
			$seconds = $1 + 1;
			print "Detected movie length (through subtitles) of $seconds seconds.\n";
		    }
		}
		close MOVIELENGTHSUB;
		$subidx++;
	    }
	}
    } 
    if (!defined $seconds) {
	print "No subtitles detected.\n";
	myLOG("mencoder -ovc copy   -nosound -o /dev/null -frameno-file /dev/null $srcFile 2>/dev/null |");
	open MOVIELENGTH, "mencoder -ovc copy   -nosound -frameno-file /dev/null -o /dev/null $srcFile 2>/dev/null |";
	while(<MOVIELENGTH>) {
	    if (/^Video stream:.*? (\d+)\.\d+ secs/) {
		$seconds = $1 + 1;
		print "Detected movie length of $seconds seconds.\n";
	    }
	}
	close MOVIELENGTH;
	if (!defined($seconds)) {
	    print "Failed to identify movie length. Aborting....\n";
	    exit(1);
	}
    }

    my $encodeAsInterlaced = 0;
    if (! -e "tmp/videoCropDeinterAndScale") {
	# Detecting crop settings
	print "Will now spawn mplayer to detect crop settings...\n";
	print "Use the DOT key (.) to check for interlacing also...\n";
	print "Hit ENTER when ready...";
	my $ans=<STDIN>;
	my $crops = undef;
	myLOG( "mplayer -nosound -vf cropdetect -quiet $srcFile |");
	open CROP, "mplayer -nosound -vf cropdetect -quiet $srcFile |";
	while(<CROP>) {
	    if (/-vf crop=(\S+)\)/) {
		$crops = "-vf crop=$1";
	    }
	}
	close CROP;
	if (!defined($crops)) {
	    die "Failed to detect crop settings!\n";
	}

	$ans = answerMe("Do you want the codec to encode as interlaced (Y/N) ? ", ["Y", "N"]);
	if ($ans eq "y") {
	    $encodeAsInterlaced = 1;
	} else {
	    $ans = answerMe("Do you need NTSC inverse telecine (Y/N) ? ", ["Y", "N"]);
	    if ($ans eq "y") {
		$crops =~ s/^/-ofps 23.976 /;
		$crops =~ s/$/,detc/;
	    } else {
		$ans = answerMe("Do you need linear blend deinterlace (Y/N) ? ", ["Y", "N"]);
		if ($ans eq "y") {
		    $crops =~ s/$/,pp=lb/;
		}
	    }
	}
	open SETTINGS, ">tmp/videoCropDeinterAndScale";
	print SETTINGS $crops;
	close SETTINGS;
    }
    
    my $audioSize = $seconds * $g_AudioBitrate*1000/8;
    my $multiplexingOverhead = 0.0025*$totalSize;
    my $videoSize = $totalSize - $multiplexingOverhead - $audioSize;
    my $intRate = sprintf("%d", (8*$videoSize/$seconds)/1000);
    $intRate--;
    print "Expected Video bitrate: ".(1000*$intRate)." bits per sec\n";
    my $selectedHeight = ChooseDimensions(1000*$intRate, $srcFile, $encodeAsInterlaced, $selectedCodec);

    # Encoding sound

    my $audioEncoded = undef;
    if ( -e "tmp/audio.ogg" ) {
	my $ans = answerMe("Found 'tmp/audio.ogg'. (U)se it or (R)emove it? ", [ "R", "U" ]);
	if ($ans eq "u") {
	    $audioEncoded = 1;
	    print "Using previously existing tmp/audio.ogg\n";
	}
    }

    if (!defined($audioEncoded)) {

	print "Scaning to find amplification factor... Please wait...\n";
	my $rescale = undef;
	mySystem("rm -f tmp/fifo");
	mySystem("mkfifo tmp/fifo");
	mySystem("mplayer -really-quiet -aid $aid -ao pcm:file=tmp/fifo:nowaveheader -vo null -vc dummy $srcFile >/dev/null 2>&1 &");
	myLOG("tcscan -i tmp/fifo -x pcm 2>/dev/null |");
	open SCAN, "tcscan -i tmp/fifo -x pcm 2>/dev/null |";
	while(<SCAN>) {
	    if (/suggested volume rescale=([\d\.]+)/) {
		$rescale = $1;
	    }
	}
	close SCAN;

	if (!defined($rescale)) {
	    my $ans = answerMe("Attempting to find scale factor failed. Continue? (Y/N) ", [ "Y", "N" ]);
	    if ($ans eq "n") {
		exit(1);
	    }
	}
	my $decibel = 20*log($rescale)/log(10.0);
	print "Audio will be scaled by $rescale ($decibel db).\nEncoding to Ogg Vorbis ".$g_AudioBitrate."KBits/sec...\n";
	#mySystem("mpegdemux -d -s 0xbd -p 0x$hexAid --ac3 $srcFile | a52dec -o wav -g $decibel | oggenc -b $g_AudioBitrate -o tmp/audio.ogg - >/dev/null 2>&1");
	mySystem("mplayer -really-quiet -aid $aid -af volume=$decibel -ao pcm:file=tmp/fifo -vo null -vc dummy $srcFile >/dev/null 2>&1 &");
	mySystem("oggenc -s 123 -Q -b $g_AudioBitrate -o tmp/audio.ogg tmp/fifo");
    }

    my $frameNoMade = undef;
    if ( -e "frameno.avi" ) {
	my $ans = answerMe("Found 'frameno.avi'. (U)se it or (R)emove it? ", [ "R", "U" ]);
	if ($ans eq "u") {
	    $frameNoMade = 1;
	    print "Using previously existing frameno.avi\n";
	} else {
	    unlink "frameno.avi";
	}
    }

    if (!defined($frameNoMade)) {
	my $cmd = "mencoder -ovc frameno -oac pcm -aid $aid -o frameno.avi $srcFile";
	mySystem($cmd);
    }

    $audioSize = -s "tmp/audio.ogg";
    $multiplexingOverhead = 0.0025*$totalSize;
    $videoSize = $totalSize - $multiplexingOverhead - $audioSize;
    $seconds = undef;
    myLOG("ogginfo tmp/audio.ogg|");
    open INFO, "ogginfo tmp/audio.ogg|";
    while(<INFO>) {
	if (/Playback length: (\d+)m:(\d+)([\.,](\d+))?s/) {
	    if (defined($4)) { $seconds = 60*$1 + $2 + 0.001*$4; }
	    else { $seconds = 60*$1 + $2; }
	}
    }
    close INFO;
    if (!defined($seconds)) {
	print "Failed to read duration (in seconds) of tmp/audio.ogg\n";
	while(1) {
	    print "Movie duration in seconds: ";
	    $seconds = <STDIN>;
	    if (defined($seconds)) {
		last;
	    }
	}
    } else {
	$seconds++;
    }
    print "Audio length : $seconds seconds\n";
    print "Audio bitrate: ".(sprintf ("%d", ($audioSize*8/$seconds)))." bits per sec\n";
    $intRate = sprintf("%d", (8*$videoSize/$seconds)/1000);
    $intRate--;
    print "Video bitrate: ".(1000*$intRate)." bits per sec\n";

    # has been down earler...
    # my $selectedHeight = ChooseDimensions(1000*$intRate, $srcFile, $encodeAsInterlaced);
    
    # Video

    my $codec = undef;
    my $codecSettingsPass1 = undef;
    my $codecSettingsPass2 = undef;
    while(1) {
	my $ans = $selectedCodec;
	if ($ans eq "1") { 
	    $codec = "xvid";
	    my $interlacing = "nointerlacing";
	    if ($encodeAsInterlaced == 1) {
		$interlacing = "interlacing";
	    }
	    $codecSettingsPass1 = "-ovc xvid -oac copy -xvidencopts pass=1:bitrate=$intRate:quant_type=h263:me_quality=6:chroma_me:vhq=3:max_bframes=2:bquant_ratio=150:bquant_offset=100:bf_threshold=0:noqpel:nogmc:trellis:nopacked:closed_gop:$interlacing:nocartoon:hq_ac:frame_drop_ratio=0:keyframe_boost=0:overflow_control_strength=5:curve_compression_high=0:curve_compression_low=0:max_overflow_improvement=5:max_overflow_degradation=5:kfreduction=20:kfthreshold=1:container_frame_overhead=1";
	    $codecSettingsPass2 = "-ovc xvid -oac copy -xvidencopts pass=2:bitrate=$intRate:quant_type=h263:me_quality=6:chroma_me:vhq=3:max_bframes=2:bquant_ratio=150:bquant_offset=100:bf_threshold=0:noqpel:nogmc:trellis:nopacked:closed_gop:$interlacing:nocartoon:hq_ac:frame_drop_ratio=0:keyframe_boost=0:overflow_control_strength=5:curve_compression_high=0:curve_compression_low=0:max_overflow_improvement=5:max_overflow_degradation=5:kfreduction=20:kfthreshold=1:container_frame_overhead=1";
	    last; 
	}
	if ($ans eq "2") { 
	    $codec = "x264"; 
	    $codecSettingsPass1 = "-ovc x264 -oac copy -x264encopts bitrate=$intRate:pass=1:subq=6:4x4mv:8x8dct:me=3:frameref=5:bframes=3:b_pyramid=normal:weight_b";
	    $codecSettingsPass2 = "-ovc x264 -oac copy -x264encopts bitrate=$intRate:pass=2:subq=6:4x4mv:8x8dct:me=3:frameref=5:bframes=3:b_pyramid=normal:weight_b";
	    last; 
	}
    }
    my $outputVideoFile = "tmp/$codec.avi";
    
    my $videoEncoded = undef;
    if ( -e $outputVideoFile ) {
	my $ans = answerMe("Video file '$outputVideoFile' already exists. (U)se it or (R)emove it? ", ["U", "R"]);
	if ($ans eq "u") {
	    $videoEncoded = 1;
	    print "Using previously existing $outputVideoFile\n";
	}
    }

    if (!defined($videoEncoded)) {
	
	die "No known video settings. Please provide 'tmp/videoCropDeinterAndScale' file!\n"
	    unless -e "tmp/videoCropDeinterAndScale";

	my $cropDeinterAndScale = `cat tmp/videoCropDeinterAndScale`;
	chomp $cropDeinterAndScale;

	if (( -e "divx2pass.log" and $codec eq "x264") 
	    or 
	    ( -e "xvid-twopass.stats" and $codec eq "xvid")) 
	{
	    my $ans = answerMe("First pass statistics appear to exist. (U)se them or (R)emove them? ", ["U", "R"]);
	    if ($ans ne "u") {
		mySystem("mencoder $cropDeinterAndScale $codecSettingsPass1 -o /dev/null $srcFile");
	    }
	} else {
	    mySystem("mencoder $cropDeinterAndScale $codecSettingsPass1 -o /dev/null $srcFile");
	}
	mySystem("mencoder $cropDeinterAndScale $codecSettingsPass2 -o $outputVideoFile $srcFile");
    }

    my $cmd = "mkvmerge --engage allow_avc_in_vfw_mode -o $outputName -A $outputVideoFile tmp/audio.ogg\n";
    mySystem($cmd);

    print "\nIf you made subtitles, check them with IDXchecker.pl !\n";
}

main;
