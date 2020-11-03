#!/usr/bin/perl

$usage="$0 [-s FILE] [-t FILE] [-a FILE]
    -s FILE : training source file
    -t FILE : training target file
    -a FILE : s2t alignment file
    -o FILE : output pattern file
Moses-like lexical scores are written in [o].lex-{t2s,s2t}
";

while ($#ARGV>=0){
    $tok=shift @ARGV;
    if ($tok eq "-s"         && $#ARGV>=0) {$fsrc=shift @ARGV; next;}
    if ($tok eq "-t"         && $#ARGV>=0) {$ftgt=shift @ARGV; next;}
    if ($tok eq "-a"         && $#ARGV>=0) {$fali=shift @ARGV; next;}
    if ($tok eq "-o"         && $#ARGV>=0) {$fout=shift @ARGV; next;}
    die "error: unparsed option $tok\n$usage";
}

die "error: missing -s option\n$usage" unless (defined $fsrc);
die "error: missing -t option\n$usage" unless (defined $ftgt);
die "error: missing -a option\n$usage" unless (defined $fali);
$fout=$fali unless (defined $fout);

&get_lexical;

sub get_lexical {
    open(T,"<$ftgt") or die "ERROR: Can't read $ftgt"; ### target is E:english
    open(S,"<$fsrc") or die "ERROR: Can't read $fsrc"; ### source is F:french
    open(A,"<$fali") or die "ERROR: Can't read $fali";
    $alignment_id = 0;
    while($t = <T>,$s = <S>,$a = <A>) {
        if (($alignment_id++ % 1000) == 0) { print STDERR "!"; }
        chomp($t); $t=~s/^ +//; $t=~s/ +$//; $t=~s/ +/ /g;
        chomp($s); $s=~s/^ +//; $s=~s/ +$//; $s=~s/ +/ /g;
        chomp($a); $a=~s/^ +//; $a=~s/ +$//; $a=~s/ +/ /g;
        @TARGET = split(/ /,$t);
        @SOURCE = split(/ /,$s);
        (%SOURCE_ALIGNED,%TARGET_ALIGNED);
        foreach (split(/ /,$a)) {
            ($si,$ti) = split(/\-/);
            if ($si >= scalar(@SOURCE) || $ti >= scalar(@TARGET)) {
                print STDERR "alignment point ($si,$ti) out of range (0-$#SOURCE,0-$#TARGET) in line $alignment_id, ignoring\n";
            }
            else {
                $SOURCE_ALIGNED{$si}++;
                $TARGET_ALIGNED{$ti}++;
                $WORD_TRANSLATION{$SOURCE[$si]}{$TARGET[$ti]}++;
                $TOTAL_SOURCE{$SOURCE[$si]}++;
                $TOTAL_TARGET{$TARGET[$ti]}++;
            }
        }
        for($ti=0;$ti<scalar(@TARGET);$ti++) {
	    next if defined($TARGET_ALIGNED{$ti});
	    $WORD_TRANSLATION{"NULL"}{$TARGET[$ti]}++;
	    $TOTAL_TARGET{$TARGET[$ti]}++;
	    $TOTAL_SOURCE{"NULL"}++;
        }
        for($si=0;$si<scalar(@SOURCE);$si++) {
	    next if defined($SOURCE_ALIGNED{$si});
	    $WORD_TRANSLATION{$SOURCE[$si]}{"NULL"}++;
	    $TOTAL_SOURCE{$SOURCE[$si]}++;
	    $TOTAL_TARGET{"NULL"}++;
        }
    }
    print STDERR "\n";
    close(A);
    close(S);
    close(T);
    open(S2T,">$fout.lex-s2t") or die "ERROR: Can't write $fout.lex-t2s";
    open(T2S,">$fout.lex-t2s") or die "ERROR: Can't write $fout.lex-t2s";
    foreach $s (keys %WORD_TRANSLATION) {
        foreach $t (keys %{$WORD_TRANSLATION{$s}}) {
            printf T2S "%s %s %.7f\n",$t,$s,$WORD_TRANSLATION{$s}{$t}/$TOTAL_SOURCE{$s};
            printf S2T "%s %s %.7f\n",$s,$t,$WORD_TRANSLATION{$s}{$t}/$TOTAL_TARGET{$t};
        }
    }
    close(T2S);
    close(S2T);
    print STDERR "Saved: $fout.lex-s2t and $fout.lex-t2s\n";
}
