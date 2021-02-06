#!/bin/bash

ODIR=$PWD/raw

newscrawl_fr(){
    DIR=$ODIR/newscrawl/fr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    for year in 2019 2018 2017 2016 2015 2014 2013 2012 2011 2010 2009 2008 2007; do
	wget -P $DIR http://data.statmt.org/news-crawl/fr/news.$year.fr.shuffled.deduped.gz
	gunzip $DIR/news.$year.fr.shuffled.deduped.gz
    done
}

JRC_enfr(){
    DIR=$ODIR/JRC-Acquis/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=JRC-Acquis/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php\?f\=JRC-Acquis%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/JRC-Acquis.en-fr.xml $DIR/download.php?f=JRC-Acquis%2Fen-fr.txt.zip
}

EMEA_enfr(){
    DIR=$ODIR/EMEA/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=EMEA/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=EMEA%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/download.php?f=EMEA%2Fen-fr.txt.zip
}

ECB_enfr(){
    DIR=$ODIR/ECB/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=ECB/v1/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=ECB%2Fv1%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/ECB.en-fr.ids $DIR/download.php?f=ECB%2Fv1%2Fmoses%2Fen-fr.txt.zip
}

EPPS_enfr(){
    DIR=$ODIR/Europarl/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    #v8
    wget -P $DIR http://opus.nlpl.eu/download.php?f=Europarl/v8/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=Europarl%2Fv8%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/Europarl.en-fr.xml $DIR/download.php?f=Europarl%2Fv8%2Fmoses%2Fen-fr.txt.zip
    #v7
    #wget -P $DIR http://www.statmt.org/europarl/v7/fr-en.tgz
    #tar xvzf $DIR/fr-en.tgz -C $DIR
    #rm -f $DIR/fr-en.tgz
}

UNPC_enfr(){
    DIR=$ODIR/UNPC/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=UNPC/v1.0/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=UNPC%2Fv1.0%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/UNPC.en-fr.xml $DIR/download.php?f=UNPC%2Fv1.0%2Fmoses%2Fen-fr.txt.zip
}

NEWS_enfr(){
    DIR=$ODIR/news-commentary/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://data.statmt.org/news-commentary/v14/training/news-commentary-v14.en-fr.tsv.gz
    gunzip $DIR/news-commentary-v14.en-fr.tsv.gz
    cut -f 1 $DIR/news-commentary-v14.en-fr.tsv > $DIR/news-commentary-v14.en
    cut -f 2 $DIR/news-commentary-v14.en-fr.tsv > $DIR/news-commentary-v14.fr
    rm -f $DIR/news-commentary-v14.en-fr.tsv
}

NEWS_testsets_enfr(){
    DIR=$ODIR/news-commentary/enfr/testsets
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi

    wget -P $DIR http://www.statmt.org/wmt14/dev.tgz
    tar xvzf $DIR/dev.tgz -C $DIR
    mv raw/news-commentary/enfr/testsets/dev/news*test????.{fr,en} $DIR/
    rm -rf $DIR/dev
    mv $DIR/news-test2008.en $DIR/newstest2008.en
    mv $DIR/news-test2008.fr $DIR/newstest2008.fr
    
    wget -P $DIR http://www.statmt.org/wmt14/test-full.tgz
    tar xvzf $DIR/test-full.tgz -C $DIR    
    cat $DIR/test-full/newstest2014-fren-ref.en.sgm | grep '^<seg' | perl -pe 's/^<seg id[^>]*>(.*)\<\/seg\>$/$1/' > $DIR/newstest2014.en
    cat $DIR/test-full/newstest2014-fren-ref.fr.sgm | grep '^<seg' | perl -pe 's/^<seg id[^>]*>(.*)\<\/seg\>$/$1/' > $DIR/newstest2014.fr

    rm -rf $DIR/test-full*
    rm -rf $DIR/dev*
}


TED2013_enfr(){
    DIR=$ODIR/TED2013/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=TED2013/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=TED2013%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/TED2013.en-fr.ids $DIR/download.php?fT=ED2013%2Fen-fr.txt.zip
}

GNOME_enfr(){
    DIR=$ODIR/GNOME/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=GNOME/v1/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=GNOME%2Fv1%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/GNOME.en-fr.xml $DIR/download.php?f=GNOME%2Fv1%2Fmoses%2Fen-fr.txt.zip
}

KDE4_enfr(){
    DIR=$ODIR/KDE4/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=KDE4/v2/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=KDE4%2Fv2%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/KDE4.en-fr.xml $DIR/download.php?f=KDE4%2Fv2%2Fmoses%2Fen-fr.txt.zip
}

Ubuntu_enfr(){
    DIR=$ODIR/Ubuntu/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=Ubuntu/v14.10/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=Ubuntu%2Fv14.10%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/Ubuntu.en-fr.xml $DIR/download.php?f=Ubuntu%2Fv14.10%2Fmoses%2Fen-fr.txt.zip
}

PHP_enfr(){
    DIR=$ODIR/PHP/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=PHP/v1/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=PHP%2Fv1%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/download.php?f=PHP%2Fv1%2Fmoses%2Fen-fr.txt.zip
}

Wikipedia_enfr(){
    DIR=$ODIR/Wikipedia/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=Wikipedia/v1.0/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=Wikipedia%2Fv1.0%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/Wikipedia.en-fr.ids $DIR/download.php?f=Wikipedia%2Fv1.0%2Fmoses%2Fen-fr.txt.zip
}

OpenSubtitles_enfr(){
    DIR=$ODIR/OpenSubtitles/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=OpenSubtitles/v2018/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=OpenSubtitles%2Fv2018%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/OpenSubtitles.en-fr.ids $DIR/download.php?f=OpenSubtitles%2Fv2018%2Fmoses%2Fen-fr.txt.zip
}

#newscrawl_fr
#JRC_enfr
#EMEA_enfr
#ECB_enfr
#EPPS_enfr
#UNPC_enfr
#NEWS_enfr
#TED2013_enfr
#GNOME_enfr
#KDE4_enfr
#PHP_enfr
#Ubuntu_enfr
#Wikipedia_enfr
#OSub_enfr

NEWS_testsets_enfr

