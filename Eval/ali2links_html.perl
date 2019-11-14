#!/usr/bin/perl

use utf8;
use open qw(:std :encoding(utf8));

$height=120;
$length_char=9;

while ($#ARGV>=0){
    $tok = shift @ARGV;
    if ($tok eq "-height" && $#ARGV>=0) {$height=shift @ARGV; next;}
    die "error: unparse $tok option\n";
}

print "
<!DOCTYPE html>
<html>
<style>
p {
    font-family:monospace;
    font-size: 15px;
    white-space: nowrap;
    margin:0;
    padding:0;
}
table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
    border-color: gray;
}
table {
    border-spacing: 0px;
    background-color: #ffffff;
}
th, td {
    padding: 0px;
    text-align: left;
}
</style>
<body>
";


while (<>){
    $nsent++;
    chomp;
    ($src,$tgt,$ali) = split /\t/;
    $src =~ s/  +/ /g; $src =~ s/^ +//; $src =~ s/ +$//;
    $tgt =~ s/  +/ /g; $tgt =~ s/^ +//; $tgt =~ s/ +$//;
    &print_links();
    print "<br>\n";
}

print "
</body>
</html>
";

sub print_links{
    @src2x=();
    @SRC=split / +/,$src;
    $length=0;
    for ($i=0; $i<=$#SRC; $i++){
	$length_wrd = length($SRC[$i]);
	push @src2x, ($length*$length_char) + ($length_wrd*$length_char/2);
	$length += $length_wrd + 1;
    }
    $width_src=$length*$length_char;

    @tgt2x=();
    @TGT=split / +/,$tgt;
    $length=0;
    for ($i=0; $i<=$#TGT; $i++){
	$length_wrd = length($TGT[$i]);
	push @tgt2x, ($length*$length_char) + ($length_wrd*$length_char/2);
	$length += $length_wrd + 1;
    }
    $width_tgt=$length*$length_char;
    $width = $width_tgt>$width_src?$width_tgt:$width_src;

    print "<table>\n";
    print "<tr>\n";
    print "<td>\n";
    print "
<p>@SRC</p>
<canvas id=\"sent$nsent\" width=\"$width\" height=\"$height\" style=\"border:0px solid #c3c3c3;\"></canvas>
<p>@TGT</p>

<script>
var c = document.getElementById(\"sent$nsent\");
var ctx = c.getContext(\"2d\");
";
    foreach $a (split / /,$ali){
	($s,$t) = split /\-/,$a;
	print "ctx.beginPath(); ctx.moveTo($src2x[$s], 5); ctx.lineTo($tgt2x[$t], $height); ctx.lineWidth=1; ctx.strokeStyle = '#0000ff'; ctx.lineCap = 'square'; ctx.stroke();\n";
    }
    print "</script>\n";
    print "</td>\n";
    print "</tr>\n";
    print "</table>\n";	
}

