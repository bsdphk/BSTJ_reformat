#!/bin/sh

set -e

mkdir -p Logs
rm -rf Conv
mkdir -p Conv
rm -f _.*.ppm
rm -f _.*.tiff

if false ; then
	find bstj.bell-labs.com/bstj -name '*.pdf' -print | 
	    sort -t- -n -k 1 -k 2 -k 3 -k 4 -k 5 > _.targets
fi
for f in `cat targets.txt`
do
	if [ "x$f" = "xstop" ] ; then
		break
	fi
	b=`basename $f .pdf`
	v=`expr $b : '\(.*\)-[0-9]*[0-9]*'`
	w=`expr $f : '.*/\(vol.*\)/a.*'`
	z=`expr $v : '.*-\(.*\)'`
	fn="BSTJ-"$w"-"$z
	if [ -f $fn.pdf ] ; then
		echo ".+" $v $w $z $fn
		continue
	fi
	echo "." $v $w $z $fn
	mkdir -p Conv/$v
	if [ "x$v" != "x$v0" ] ; then
		if [ "x$v0" != "x" ] ; then
			echo "---- $fn0.pdf"
			tiffcp $l _.tiff
			rm -f $l
			tiff2pdf -t $fn0 -z -o $fn0.pdf _.tiff
			ls -l $fn0.pdf
		fi
		l=""
		v0=$v
		fn0=$fn
		rm -rf Conv
		mkdir -p Conv
	fi
	echo ".." $v $b
	/usr/local/libexec/xpdf/pdfimages -j $f Conv/$b
	(
		cd Conv
		for i in *
		do
			if [ -d $i ] ; then
				rmdir $i || true
			fi
		done
		for i in *
		do
			if a=`grep $i ../special.txt` ; then
				echo "... spec $a"
				eval $a $i.ppm
				rm -f $i
			fi
		done

		for i in *
		do
			if [ `expr $i : '.*[.]ppm$'` -ne 0 ] ; then
				continue
			fi
			
			if [ -f $i ] ; then
				echo "... ? $i "
				convert $i ${i}.ppm
				echo "# $i" >> ../special_missing.txt
				rm -f $i
			fi
		done
	)
	if [ `ls Conv | grep -v ppm | wc -l` -ne 0 ] ; then
		echo "Residual files in Conv"
		exit 2
	fi
	rm -f _.????.ppm
	python pagesplit2.py Conv/*.ppm > Logs/_.${b}.log
	for i in _.????.tiff
	do
		fo=_.$b.$i
		mv $i $fo
		l="$l $fo"
	done
	rm -f Conv/*.ppm
done
if [ "x$v0" != "x" ] ; then
	echo "---- $fn0.pdf"
	tiffcp $l _.tiff
	rm -f $l
	tiff2pdf -t $fn0 -z -o $fn0.pdf _.tiff
	ls -l $fn0.pdf
fi
