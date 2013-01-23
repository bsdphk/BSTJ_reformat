
from __future__ import print_function

import mmap
import os
import sys
import ppm

import subprocess


pop = list()
for i in range (3):
	pop.append(subprocess.Popen("sh", shell=True, bufsize=8192, stdin=subprocess.PIPE))


def sub_cmd(arg):
	p = pop.pop(0)
	fsh = p.stdin
	fsh.write(arg + "\n")
	fsh.flush()
	pop.append(p)

# Desired height
dwid = 920
dht = 750

###################################

nchunk = 1
lchunk = list()
hchunk = 0
chunk_space = 1

def emit_chunk():
	global nchunk
	global lchunk
	global hchunk
	fn = "_.%04d.ppm" % nchunk
	sys.stderr.write(".... " + fn + "\n")

	wchunk = 0
	xlo = 99999
	xhi = 0
	for r in lchunk:
		wchunk = max(wchunk, r.xhi - r.xlo)
		xlo = min(xlo, r.xlo)
		xhi = max(xhi, r.xhi)

	print("# WC", fn, wchunk, hchunk, xlo, xhi, xhi - xlo)
	if xhi - xlo < dwid:
		xhi = xlo + dwid
		wchunk = dwid

	d = ppm.ppm(fn, "w", 20 + wchunk, max(hchunk,dht))
	y = 0
	for r in lchunk:
		if xhi - xlo == wchunk:
			r.xlo = xlo
			r.xhi = min(xhi, r.p.x)
		d.put_rect(0, y, r)
		y += (r.yhi - r.ylo)
		for x in range(20):
			d.wrpx(x, y, 0, 0, 0)
			d.wrpx(d.x - (1+x), y, 0, 0, 0)
		y += chunk_space

	lchunk = list()
	wchunk = 0
	hchunk = 0

	del d
	sub_cmd("convert -type grayscale -colors 64 %s -compress lzw _.%04d.tiff ; rm -f %s" % (fn, nchunk, fn))
	nchunk += 1

def split_chunk(r, wish, o):
	print("# SP ", r, "Wish", wish)
	if wish < 20:
		return None

	w = (r.xhi - r.xlo) / 2
	r1 = ppm.rect(r.p, r.xlo, r.ylo, r.xhi - w, r.yhi)
	r2 = ppm.rect(r.p, r.xlo + w, r.ylo, r.xhi, r.yhi)
	yh1 = r1.ymin()
	yh2 = r2.ymin()
			
	b = 0
	w = None
	s = None
	adj = 0
	for i in range(wish, 20, -1):
		for sk in range(0,3):
			if i + sk > wish:
				continue
			v = min(yh1[i], yh2[i - sk])
			if v > b or (v == b and adj > sk):
				b = v
				w = i
				s = "^ %d" % sk
				adj = sk
				print(s, w, b)
			v = min(yh1[i - sk], yh2[i])
			if v > b or (v == b and adj > sk):
				b = v
				w = i
				s = "v %d" % sk
				adj = sk
				print(s, w, b)
		if b >= 240 and i < w - 10:
			break

	print("SP:", r, "Wish", wish, "Got", w, "Shade", b, "Skew", s)
	if  b > 240:
		r1 = ppm.rect(r.p, r.xlo, r.ylo, r.xhi, r.ylo + w)
		r.ylo += w

		r1.yhi += adj
		r.ylo -= adj

		if o != None:
			r1.outline(o,0,255,255)
			r.outline(o,0,255,255)
		add_chunk(r1, o)
		add_chunk(r, o)
		return True

	print("############################################")
	return None



def add_chunk(r, o):
	global nchunk
	global lchunk
	global hchunk

	txt = None

	#print("AC", r)

	d = dht - (chunk_space + hchunk)

	h = r.yhi - r.ylo
	if h < 10:
		print("Add_Chunk Y-ignore", r)
		return
	if r.xhi - r.xlo < 20:
		print("Add_Chunk X-ignore", r)
		return

	print("h", h, "hchunk", hchunk, "d", d)

	if h > d and d > 60:
		if split_chunk(r, d, o):
			return


	if hchunk + chunk_space + h > dht:
		if hchunk > 50:
			emit_chunk()

	if h > dht:
		if split_chunk(r, dht, o):
			return

	lchunk.append(r)
	hchunk += chunk_space + h

	if hchunk >= dht:
		emit_chunk()


#############################################

def rc_trim_box(p, o, r, t = 254, w = dwid):
	print("RTB", r, "T", t, "W", w)
	av = r.xavg()

	if o != None and False:
		for x in range(len(av)):
			for y in range(0, int(255 - av[x])):
				o.wrpx(r.xlo + x, r.ylo + y, 255,0,0)

	w = int(w)
	if w < 10:
		return
	ex = r.xhi - (r.xlo + w)

	print("EX", ex, "W", w, r)
	if ex > 11:
		nh = 0
		nl = 0
		for x in range(ex):
			if av[x] > t:
				nl += 1
			if av[-x] > t:
				nh += 1

		print("N", ex, "NL", nl, "NH", nh)

		if nl > nh and nl > 10:
			r.xlo += nl - 10
			print("TDL", r)
		elif nh > nl and nh > 10:
			r.xhi -= nh - 10
			print("TDH", r)

		av = r.xavg()

	for x in range(len(av)):
		if av[x] < t:
			break
	xnlo = x

	for x in range(len(av)):
		if av[len(av) - (1 + x)] < t:
			break
	xnhi = x

			

	if xnlo > 10:
		r.xlo += xnlo - 10
	if xnhi > 10:
		r.xhi = max(r.xhi, xnhi - 10, r.xlo)
	print("TD", r)


def rc_trim_x(p, o, r):

	lo = r.xmin()

	wx = 20

	if o != None and False:
		for x in range(wx, r.xhi - wx):
			v = min(lo[x - wx: x + wx]) / 10
			for y in range(0, v):
				o.wrpx(x, r.ylo + y, 255, 0, 0)

	for xl in range(wx, len(lo) - wx):
		v = min(lo[xl - wx: xl + wx])
		if v < 128:
			break
	for xh in range(len(lo) - wx, max(r.xlo + xl, wx), -1):
		v = min(lo[xh - wx: xh + wx])
		if v < 128:
			break
	assert r.xhi > r.xlo
	r.xlo += xl
	r.xhi = r.xlo + (xh - xl)
	assert r.xhi > r.xlo


def mk_rect(p, o, ylo, yhi):
	if ylo == yhi:
		return None
	rx = ppm.rect(p, ylo = ylo, yhi = yhi)
	rc_trim_x(p, o, rx)
	h =  rx.yhi - rx.ylo
	w =  rx.xhi - rx.xlo
	a = 1.0 * h * w

	if h < 200 and a < 30000:
		hh = rx.hist()
		dens = sum(hh[:64]) / a
		if a < 1400 and dens < .06:
			print("YDENS", rx, h, w, a, dens)
			if o != None:
				rx.outline(o, 255, 0, 255)
			return None

		if a > 10000 and dens < .001:
			print("ZDENS", rx, h, w, a, dens)
			if o != None:
				rx.outline(o, 255, 0, 255)
			return None

		if a < 10000 and dens < .01:
			print("XDENS", rx, h, w, a, dens)
			if o != None:
				rx.outline(o, 255, 0, 255)
			return None
		print("DENS", rx, h, w, a, dens)
	return rx


def segment(p, o):
	r0 = ppm.rect(p, xlo = 10, xhi = p.x - 10)
	lo = r0.ymin()
	s = False
	s0 = 0
	wy = 7
	l = list()
	for y in range(wy, p.y - wy):
		if o != None and False:
			av = r0.yavg()
			hi = r0.ymax()
			for x in range(0,255):
				if x < lo[y]:
					o.wrpx(x, y, 0, 0, 255)
				elif x < av[y]:
					o.wrpx(x, y, 0, 255, 0)
				elif x < hi[y]:
					o.wrpx(x, y, 255, 0, 0)

		b = int(min(lo[y - wy:y+wy]))

		if o != None and False:
			for x in range(128,b):
				o.wrpx(p.x - 320 + x, y, 255, 0, 0)
		if b > 160:
			if s:
				rx = mk_rect(p, o, s0, y)
				if rx != None:
					l.append(rx)
			s = False
		else:
			if not s:
				s0 = y
			s = True
	if s:
		rx = mk_rect(p, o, s0, y)
		if rx != None:
			l.append(rx)
	return l

def trim(p, o, sl):

	for rx in sl:
		rc_trim_box(p, o, rx)

	for iter in range(3):
		if len(sl) < 2:
			break
		lxlo = list()
		lxhi = list()
		xmid = 0
		xn = 0.
		for rx in sl:
			xmid += (rx.xlo + rx.xhi) * .5
			xn += 1.0
			lxlo.append(rx.xlo)
			lxhi.append(rx.xhi)
		lxlo.sort()
		lxhi.sort()
		if lxhi[-1] - lxlo[0] < dwid:
			break
		xmid /= xn
		print("ZZZ", lxlo, lxhi, xmid)

		for rx in sl:
			if rx.xlo == lxlo[0]:
				w = (rx.xhi - rx.xlo) - (lxlo[1] - lxlo[0])
				rc_trim_box(p, o, rx, t = 254 - iter, w=w)
			if rx.xhi == lxhi[-1]:
				w = (rx.xhi - rx.xlo) - (lxhi[-1] - lxhi[-2])
				rc_trim_box(p, o, rx, t = 254 - iter, w=w)


	for iter in range(3):
		break
		for xx in range(2):
			xlo = p.x
			xhi = 0
			xmid = 0
			xn = 0
			for rx in sl:
				xlo = min(xlo, rx.xlo)
				xhi = max(xhi, rx.xhi)
				xmid += (rx.xlo + rx.xhi) * .5
				xn += 1
			xmid /= xn
			print("D", xhi - xlo, xmid, xlo, xhi)
			if xhi - xlo < dwid:
				break
			g = False
			for rx in sl:
				sk = max(xmid - rx.xlo, rx.xhi - xmid) - dwid/2
				if sk > 0:
					w = max(
						(xmid - dwid/2) - rx.xlo,
						rx.xhi - (xmid + dwid/2)
					)
					w = (rx.xhi - rx.xlo) - w
					w = (rx.xhi - rx.xlo) - sk
					
					print("SKEW", rx, xmid, sk, w)
					
					rc_trim_box( p, o, rx, t = 254 - iter, w = w)
					g = True
			if not g:
				break

	xlo = p.x
	xhi = 0
	for rx in sl:
		xlo = min(xlo, rx.xlo)
		xhi = max(xhi, rx.xhi)
	return xhi - xlo

def doit(fn):
	p = ppm.ppm(fn)
	print(p)
	if p.x < 700:
		p2 = ppm.ppm(fn + "_.ppm", "w", p.x * 2, p.y * 2)
		print("Doubling", p, p2)
		for y in range(p2.y):
			for x in range(p2.x):
				i = p.rdpx(x / 2, y / 2)
				p2.wrpx(x, y, i[0], i[1], i[2])
		p = p2

	if False:
		o = p.clone("_.ppm")
	else:
		o = None

	# Segment
	if p.x > 1400:
		sl = list()
		sl.append(ppm.rect(p, 0, 0, p.x, p.y))
	else:
		sl = segment(p, o)
	if len(sl) == 0:
		sl.append(ppm.rect(p, 0, 0, p.x, p.y))


	# Trim
	w = trim(p, o, sl)
	print("W", w)
	g = True
	if w > dwid:
		g = False

	for rx in sl:
		if o != None:
			rx.outline(o, 0, 0, 255)
		add_chunk(rx, o)
	return g

test_set = [
]
	
if __name__ == '__main__':
	n = 0
	av = sys.argv[1:]
	if len(av) == 0:
		av = test_set
	fl = open("_fl", "w")
	go = False
	for fn in av:
		#if fn == "Conv/bstj19-2-161-011.ppm":
		#	go = True
		print("#", fn)
		sys.stderr.write("... " + fn + "\n")
		g = doit(fn)
		if not g:
			fl.write(fn + "\n")
		if go or True:
			g = False
		sys.stdout.flush()
		g = True
		if len(av) > 1 and not g:
			sys.stderr.write("==> ")
			sys.stdin.readline()
	if hchunk > 0:
		emit_chunk()

for i in pop:
	i.stdin.close()
for i in pop:
	i.wait()
