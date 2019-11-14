#!/usr/bin/perl

use utf8;
use open qw(:std :encoding(utf8));
use Text::WordDiff;

$bgcolor="#dddddd";
$color="red";
$diffs=0;
$usage="usage: $0 -hyp FILE -ref FILE [-diffs] [-color COLOR] [-h] > output.html
   -hyp    FILE : parallel hyp file
   -ref    FILE : parallel ref file
   -add    FILE : additional file parallel to hyp and ref. Use as many as you want
   -diffs       : show sentences with diffs (default 0)
   -color COLOR : color used to highlight diffs (default 'red')
   -h           : help
";
while ($#ARGV>=0){
    $tok=shift @ARGV;
    if ($tok eq '-hyp' && $#ARGV>=0) {$fhyp=shift @ARGV; next;}
    if ($tok eq '-ref' && $#ARGV>=0) {$fref=shift @ARGV; next;}
    if ($tok eq '-add' && $#ARGV>=0) {push @fadd, shift @ARGV; next;}
    if ($tok eq '-color' && $#ARGV>=0) {$color=shift @ARGV; next;}
    if ($tok eq '-diffs') {$diffs=1; next;}
    if ($tok eq '-h') {die "$usage\n";}
    die "error: unparsed option '$tok'\n$usage\n";
}
die "error: missing -hyp option\n$usage" unless (defined $fhyp);
die "error: missing -ref option\n$usage" unless (defined $fref);

&heading;
open(HYP,"<$fhyp") or die "error: cannot open hyp file: $fhyp\n";
@HYP=<HYP>;
close HYP;
print STDERR "Reading $fhyp\n";

open(REF,"<$fref") or die "error: cannot open ref file: $fref\n";
@REF=<REF>;
close REF;
print STDERR "Reading $fref\n";

for ($a=0; $a<=$#fadd; $a++){
    open(F,"<$fadd[$a]") or die "error: cannot open add file: $fadd[$a]\n";
    $i=0;
    while (<F>){
	$ADD[$a][$i]=$_;
	$i++;
    }
    close F;
    print STDERR "Reading $fadd[$a]\n";
}

print STDERR "Processing...";
for ($Id=0; $Id<=$#HYP; $Id++){
    $lhyp=$HYP[$Id];
    chomp $lhyp; $lhyp =~ s/^\s+//; $lhyp =~ s/\s+$//; $lhyp =~ s/\s\s+/\s/g;
    $lref=$REF[$Id];
    chomp $lref; $lref =~ s/^\s+//; $lref =~ s/\s+$//; $lref =~ s/\s\s+/\s/g;
    @ladd=();
    for ($a=0; $a<=$#fadd; $a++){
	$l=$ADD[$a][$Id];
	chomp $l; $l =~ s/^\s+//; $l =~ s/\s+$//; $l =~ s/\s\s+/\s/g;
	push @ladd, $l;
    }
    my ($lhyp,$lref,$isdiff) = &diff($lhyp,$lref);
    next if ($diffs && !$isdiff);
    print "<tr>\n<td>$Id</td>\n<td>";
    print "$lhyp<hr>$lref";
    for ($a=0; $a<=$#ladd; $a++){
	print "<hr>$ladd[$a]";
    }
    print "</td>\n</tr>\n";
}
&ending;
print STDERR " Done! [$Id sentences]\n";

exit;

sub heading{
    print "<!DOCTYPE html>
<html>
<head>
<meta charset=\"UTF-8\">
<style>
table {
    font-family: arial, sans-serif;
    width: 100%;
    border-collapse: collapse;
}

td, th {
  border: 1px solid $bgcolor;
  text-align: left;
  padding: 8px;
}

tr:nth-child(even) {
    background-color: $bgcolor;
}
</style>
</head>
<body>

<table>
  <tr>
    <th>Id</th>
    <th>Hyp: <font size=\"2\">$fhyp</font><hr>Ref: <font size=\"2\">$fref</font>
";

for ($a=0; $a<=$#fadd; $a++){
    print "<hr>Add: <font size=\"2\">$fadd[$a]</font>"
}

print "</th>
  </tr>
";
}


sub ending{
    print "</table>
</body>
</html>
";
}

sub diff{
    my $str1 = shift @_;
    my $str2 = shift @_;    
    my $diff = word_diff \$str1,\$str2, { STYLE => 'HTML' };
    my $isdiff=0;
    #my @str1 = split /\s+/,shift @_;
    #my @str2 = split /\s+/,shift @_;
    #word_diff \@str1,\@str2, { STYLE => 'HTML', OUTPUT => \@diff };
    
    $diff =~ s/\<span class="hunk"\>/￭/g;
    $diff =~ s/\<\/span\>/￭/g;
    my $diff_str1='';
    my $diff_str2='';
    while ($diff =~ s/￭([^￭]+)￭//){
	$within=$1;
	if ($within =~ /^\<del\>(.+)\<\/del\>\<ins\>(.+)\<\/ins\>$/){
	    $diff_str1 .= "<font color=\"$color\">".$1."</font>";
	    $diff_str2 .= "<font color=\"$color\">".$2."</font>";
	    $isdiff=1;
	}
	elsif ($within =~ /^\<ins\>(.+)\<\/ins\>\<del\>(.+)\<\/del\>$/){
	    $diff_str1 .= "<font color=\"$color\">".$1."</font>";
	    $diff_str2 .= "<font color=\"$color\">".$2."</font>";
	    $isdiff=1;
	}
	elsif ($within =~ /^\<del\>(.+)\<\/del\>$/){
	    $diff_str1 .= "<font color=\"$color\">".$1."</font>";
	    $isdiff=1;
	}
	elsif ($within =~ /^\<ins\>(.+)\<\/ins\>$/){
	    $diff_str2 .= "<font color=\"$color\">".$1."</font>";
	    $isdiff=1;
	}
	else{
	    $diff_str1 .= $within;
	    $diff_str2 .= $within;
	}
    }
    return ($diff_str1,$diff_str2,$isdiff);
}


