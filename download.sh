#!/bin/bash

ODIR=$HOME/raw

jrc_enfr(){
    DIR=$ODIR/jrc/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=JRC-Acquis/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php\?f\=JRC-Acquis%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/JRC-Acquis.en-fr.xml $DIR/download.php?f=JRC-Acquis%2Fen-fr.txt.zip
}

emea_enfr(){
    DIR=$ODIR/emea/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=EMEA/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=EMEA%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/download.php?f=EMEA%2Fen-fr.txt.zip
}

ecb_enfr(){
    DIR=$ODIR/ecb/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=ECB/v1/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=ECB%2Fv1%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/ECB.en-fr.ids $DIR/download.php?f=ECB%2Fv1%2Fmoses%2Fen-fr.txt.zip
}

epps_enfr(){
    DIR=$ODIR/epps/enfr
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

unpc_enfr(){
    DIR=$ODIR/unpc/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=UNPC/v1.0/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=UNPC%2Fv1.0%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/LICENSE $DIR/UNPC.en-fr.xml $DIR/download.php?f=UNPC%2Fv1.0%2Fmoses%2Fen-fr.txt.zip
}

news_enfr(){
    DIR=$ODIR/news/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://data.statmt.org/news-commentary/v14/training/news-commentary-v14.en-fr.tsv.gz
    gunzip $DIR/news-commentary-v14.en-fr.tsv.gz
    cut -f 1 $DIR/news-commentary-v14.en-fr.tsv > $DIR/news-commentary-v14.en
    cut -f 2 $DIR/news-commentary-v14.en-fr.tsv > $DIR/news-commentary-v14.fr
    rm -f $DIR/news-commentary-v14.en-fr.tsv
}

TED2013_enfr(){
    DIR=$ODIR/TED2013/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=TED2013/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=TED2013%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/TED2013.en-fr.ids $DIR/download.php?f=TED2013%2Fen-fr.txt.zip
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

OSub_enfr(){
    DIR=$ODIR/OSub/enfr
    if [ -e $DIR ]; then echo "warning: directory $DIR already exists"; return; fi
    wget -P $DIR http://opus.nlpl.eu/download.php?f=OpenSubtitles/v2018/moses/en-fr.txt.zip
    unzip -d $DIR $DIR/download.php?f=OpenSubtitles%2Fv2018%2Fmoses%2Fen-fr.txt.zip
    rm -f $DIR/README $DIR/OpenSubtitles.en-fr.ids $DIR/download.php?f=OpenSubtitles%2Fv2018%2Fmoses%2Fen-fr.txt.zip
}

#jrc_enfr
#emea_enfr
#ecb_enfr
#epps_enfr
#unpc_enfr
#news_enfr
#TED2013_enfr
#GNOME_enfr
#KDE4_enfr
#Ubuntu_enfr
#PHP_enfr
#Wikipedia_enfr
#OSub_enfr

exit

#mkdir -p $PWD/epps/testsets
#wget http://www.statmt.org/europarl/v7/fr-en.tgz
#wget http://www.statmt.org/europarl/v7/de-en.tgz
#cp /DEV/Projects/Generic-Models/OfficialTestSets/wmt/enfr/test200*enfr* $PWD/epps/testsets/
#cp /DEV/Projects/Generic-Models/OfficialTestSets/wmt/ende/test200*ende* $PWD/epps/testsets/

#mkdir -p $PWD/ted/testsets
#wget http://opus.nlpl.eu/download.php?f=TED2013/de-en.txt.zip
#wget http://opus.nlpl.eu/download.php?f=TED2013/en-fr.txt.zip
#download test sets from:
# https://wit3.fbk.eu/mt.php?release=2016-01
# https://wit3.fbk.eu/mt.php?release=2017-01-trnmted
#into: $PWD/ted/testsets/
#for f in `ls -1 ted/testsets/IWSLT*.xml | perl -pe 's/\.xml//'`
#do
#    echo $f
#    cat $f.xml | perl -pe 's/^\<seg id=\"\d+\"\> (.+) \<\/seg\>$/$1/' | grep -v "^<" > $f
#done

#wget https://download.microsoft.com/download/1/4/8/1489BF45-93AA-4B38-B4DA-5CA5678B2121/MSLT_Corpus.zip

#rm -f $PWD/ted/testsets/mslt_test_fren.fr
#for f in `ls -1 $PWD/ted/testsets/MSLT_Test_FR_*/MSLT_Test_FR_*.T2.fr.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_test_fren.fr
#done
#rm -f $PWD/ted/testsets/mslt_test_fren.en
#for f in `ls -1 $PWD/ted/testsets/MSLT_Test_FR_*/MSLT_Test_FR_*.T3.en.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_test_fren.en
#done

#rm -f $PWD/ted/testsets/mslt_dev_fren.fr
#for f in `ls -1 $PWD/ted/testsets/MSLT_Dev_FR_*/MSLT_Dev_FR_*.T2.fr.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_dev_fren.fr
#done
#rm -f $PWD/ted/testsets/mslt_dev_fren.en
#for f in `ls -1 $PWD/ted/testsets/MSLT_Dev_FR_*/MSLT_Dev_FR_*.T3.en.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_dev_fren.en
#done

#rm -f $PWD/ted/testsets/mslt_test_deen.de
#for f in `ls -1 $PWD/ted/testsets/MSLT_Test_DE_*/MSLT_Test_DE_*.T2.de.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_test_deen.de
#done
#rm -f $PWD/ted/testsets/mslt_test_deen.en
#for f in `ls -1 $PWD/ted/testsets/MSLT_Test_DE_*/MSLT_Test_DE_*.T3.en.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_test_deen.en
#done

#rm -f $PWD/ted/testsets/mslt_dev_deen.de
#for f in `ls -1 $PWD/ted/testsets/MSLT_Dev_DE_*/MSLT_Dev_DE_*.T2.de.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_dev_deen.de
#done
#rm -f $PWD/ted/testsets/mslt_dev_deen.en
#for f in `ls -1 $PWD/ted/testsets/MSLT_Dev_DE_*/MSLT_Dev_DE_*.T3.en.snt`
#do
#    iconv -f UTF-16 -t UTF-8 $f >> $PWD/ted/testsets/mslt_dev_deen.en
#done


