#!/usr/bin/perl

use utf8;
use open qw(:std :encoding(utf8));

$char_length=10;
$font_size=18;
$deg=-60;

print "
<!DOCTYPE html>
<html>
<style>
table, th, td {
    font-family:monospace;
    font-weight: normal;
    border-collapse: collapse;
    border: 1px solid #eee;
    border-spacing: 0px;
    padding: 0px;
    text-align: right;
    font-size: ${font_size}px;
}
tr:hover {background-color: #ffff99;}
th.rotate > div {
  text-align: left;
  transform: 
    rotate(${deg}deg);
  width: ${font_size}px; #size of columns
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
    &print_matrix();
}

print "
</body>
</html>
";

sub print_matrix{
    @SRC=split / +/,$src;

    $maxheight=0;
    for ($i=0; $i<=$#SRC; $i++){
        $l = length($SRC[$i]);
	$maxheight = $l if ($l>$maxheight);
    }
    $maxheight *= $char_length;
    for ($i=0; $i<$maxheight/25; $i++){
	print "<br>\n";
    }


    @TGT=split / +/,$tgt;
    %s2t=();
    foreach $a (split / /,$ali){
	($s,$t) = split /\-/,$a;
	$s2t{$s}{$t}=1;
    }

    print "<table>\n";
    print "<tr>\n";
    print "<th></th>\n";
    for ($s=0; $s<=$#SRC; $s++) {
        print "<th class=\"rotate\"><div>$SRC[$s]</div></th>\n";
    }
    print "</tr>\n";
    for ($t=0; $t<=$#TGT; $t++){
	print "<tr>\n";
	print "<th>$TGT[$t]</th>\n";
	for ($s=0; $s<=$#SRC; $s++){
	    if (exists $s2t{$s}{$t}){$color="bgcolor=#000000";}
	    else {$color="bgcolor=#ffffff";}
	    print "<td nowrap width=\"${font_size}px\" $color></td>\n";
	}
	print "</tr>\n";
    }
    print "</table>\n";
    print "<br>\n";
}
