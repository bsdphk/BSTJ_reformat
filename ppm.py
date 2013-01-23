
from __future__ import print_function

import mmap
import os
import sys

class ppm(object):
	def __init__(self, fn, a = "r", x = None, y = None):
		assert a == "r" or a == "w"
		if a == "w":
			self.wr = True
			assert type(x) == int
			assert type(y) == int
			assert x > 0
			assert y > 0
		else:
			self.wr = False

		if self.wr:
			self.fi = open(fn, "w+b")
			self.fi.truncate(0)
			self.fi.truncate(19 + 3 * x * y)
			self.m = mmap.mmap(self.fi.fileno(), 0 )
			s = "P6\n%5d %5d\n%3d\n" % (x, y, 255)
			self.m[0:len(s)] = s
			self.m[len(s):] = str(bytearray((255,255,255)) * (x * y))
		else:
			self.fi = open(fn, "rb")
			self.m = mmap.mmap(self.fi.fileno(),
			    0, prot=mmap.PROT_READ)
		assert self.m[:2] == "P6"
		o = 0
		n = 0
		while True:
			x = self.m.find("\n", o, o + 100)
			assert x >= -1
			s = self.m[o:x]
			o = x + 1
			if s[0] == '#':
				continue
			if n == 0:
				self.type = s
			elif n == 1:
				s = s.split()
				self.x = int(s[0])
				self.y = int(s[1])
			elif n == 2:
				self.d = int(s)
				self.o = o
				break
			n += 1
		self.xhis = None
		self.yhis = None
		self.fn = fn

	def __repr__(self):
		return "<P %dx%d %s>" % (self.x, self.y, self.fn)

	def rdpx(self, x, y):
		i = self.o + 3 * (y * self.x + x)
		return bytearray(self.m[i:i+3])

	def wrpx(self, x, y, r, g, b):
		assert self.wr
		if y >= self.y:
			print("WRPX hi y", self.y, y)
			return
		if x >= self.x:
			print("WRPX hi x", self.x, x)
			return
		i = self.o + 3 * (y * self.x + x)
		self.m[i:i+3] = str(bytearray((r,g,b)))

	def clone(self, fn):
		o = ppm(fn, "w", self.x, self.y)
		o.m[o.o:] = self.m[self.o:]
		return o

	def hist(self):
		self.yhis = list()
		lx = list([0] * (self.x * 3))
		for y in range(0, self.y):
			o = self.o + y * self.x * 3
			w = self.x * 3
			v = bytearray(self.m[o:o+w])
			self.yhis.append(sum(v)/float(w))
			#for i in range(len(v)):
			#	lx[i] += v[i]
		self.xhis = list()
		for x in range(0, self.x):
			self.xhis.append(sum(lx[x * 3:x*3+3]) / (3 * self.y))

	def put_rect(self, xlo, ylo, r):
		for b in r:
			o = self.o + ylo * self.x * 3 + xlo * 3
			self.m[o:o+len(b)] = str(b)
			ylo += 1

class rect(object):
	def __init__(self, parent, xlo = 0, ylo = 0, xhi = None, yhi = None):
		self.p= parent
		self.xlo = xlo
		self.ylo = ylo
		if xhi == None:
			xhi = parent.x
		self.xhi = xhi
		if yhi == None:
			yhi = parent.y
		self.yhi = yhi
		self.typ = None

	def set_typ(self, typ):
		self.typ = typ

	def outline(self, o, r, g, b):
		for x in range(self.xlo, self.xhi - 1):
			o.wrpx(x, self.ylo, r, g, b)
			o.wrpx(x, self.ylo + 1, r, g, b)
			o.wrpx(x, self.yhi - 2, r, g, b)
			o.wrpx(x, self.yhi - 1, r, g, b)
		for y in range(self.ylo, self.yhi - 1):
			o.wrpx(self.xlo, y, r, g, b)
			o.wrpx(self.xlo + 1, y, r, g, b)
			o.wrpx(self.xhi - 2, y, r, g, b)
			o.wrpx(self.xhi - 1, y, r, g, b)

	def yavg(self):
		l = list()
		w= (self.xhi - self.xlo) * 3
		for y in range(self.ylo, self.yhi):
			a0 = self.p.o + (self.xlo + y * self.p.x) * 3
			a = sum(bytearray(self.p.m[a0:a0 + w]))
			a /= float(w)
			l.append(a)
		return l

	def ymin(self):
		l = list()
		w= (self.xhi - self.xlo) * 3
		for y in range(self.ylo, self.yhi):
			a0 = self.p.o + (self.xlo + y * self.p.x) * 3
			a = min(bytearray(self.p.m[a0:a0 + w]))
			l.append(a)
		return l

	def ymax(self):
		l = list()
		w= (self.xhi - self.xlo) * 3
		for y in range(self.ylo, self.yhi):
			a0 = self.p.o + (self.xlo + y * self.p.x) * 3
			a = max(bytearray(self.p.m[a0:a0 + w]))
			l.append(a)
		return l

	def xmin(self):
		w= (self.xhi - self.xlo)
		l = [255] * w
		for y in range(self.ylo, self.yhi):
			a0 = self.p.o + (self.xlo + y * self.p.x) * 3
			b = bytearray(self.p.m[a0:a0 + w * 3])
			for i in range(w):
				l[i] = min(l[i], b[i * 3])
		return l

	def xmax(self):
		w= (self.xhi - self.xlo)
		l = [0] * w
		for y in range(self.ylo, self.yhi):
			a0 = self.p.o + (self.xlo + y * self.p.x) * 3
			b = bytearray(self.p.m[a0:a0 + w * 3])
			for i in range(w):
				l[i] = max(l[i], b[i * 3])
		return l

	def xavg(self):
		w= (self.xhi - self.xlo)
		l = [0] * w
		for y in range(self.ylo, self.yhi):
			a0 = self.p.o + (self.xlo + y * self.p.x) * 3
			b = bytearray(self.p.m[a0:a0 + w * 3])
			for i in range(w):
				l[i] += b[i * 3]
		for i in range(w):
			l[i] /= float(self.yhi - self.ylo)
		return l

	def ydens(self, lo = 64, hi = 192):
		w= (self.xhi - self.xlo)
		h= (self.yhi - self.ylo)
		dl = [0] * h
		dh = [0] * h
		for y in range(h):
			a0 = self.p.o + (self.xlo + (self.ylo + y) * self.p.x) * 3
			b = bytearray(self.p.m[a0:a0 + w * 3])
			for i in range(w):
				v = b[i]
				if v < lo:
					dl[y] += 1
				elif v > hi:
					dh[y] += 1
		return dl, dh

	def hist(self):
		w= (self.xhi - self.xlo)
		h= (self.yhi - self.ylo)
		hh = [0] * 256
		for y in range(h):
			a0 = self.p.o + (self.xlo + (self.ylo + y) * self.p.x) * 3
			b = bytearray(self.p.m[a0:a0 + w * 3])
			for i in range(w):
				v = b[i * 3]
				hh[v] += 1
		return hh

	def __iter__(self):
		w= (self.xhi - self.xlo)
		for y in range(self.ylo, self.yhi):
			a0 = self.p.o + (self.xlo + y * self.p.x) * 3
			yield bytearray(self.p.m[a0:a0 + w * 3])

	def __repr__(self):
		return "<R %dx%d+%d+%d>" % (
		    self.xhi - self.xlo,
		    self.yhi - self.ylo,
		    self.xlo, self.ylo
		)
