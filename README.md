BSTJ_reformat
=============

I want to read the Bell Systems Technical Journal on my Kobo Glow
eBook reader, particular when I'm sitting in a plane or an airport.

Alcatel Lucent has graciously scanned all 100K pages and made them
available here:

	http://www.alcatel-lucent.com/bstj/

First thing you must do is mirror those 46GB to you local computer.

You also need to install xpdf, Imagemagick, python and libtiff

conv2.sh runs the show, you'll probably need to adjust stuff.

pagesplit2.py is the image-processing smarts, and it can certainly
be made smarter.

After the reformatting, you only need about 12 GB to store the
entire BSTJ, a 16GB SD card will do nicely.

Have fun,

phk
