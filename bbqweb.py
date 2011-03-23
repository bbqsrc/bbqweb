#!/usr/bin/env python
from mako.template import Template
from mako.lookup import TemplateLookup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, Numeric, String, MetaData, ForeignKey, DateTime, PickleType, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from subprocess import *
import datetime
import sys, os
from tempfile import NamedTemporaryFile

# print t.render(rows=[('herp', 'how to herp', 'herp.html'), ('derp', 'how to cunt it up', 'loldicks.html')])
#engine = sqlalchemy.create_engine('sqlite:///%s' % db)
SqlBase = declarative_base()

class Base(SqlBase):
	__tablename__ = "bases"

	name = Column(String, nullable=False, primary_key=True)
	content = Column(String, nullable=False)

	def __init__(self, name, content):
		self.name = name
		self.content = content

class Page(SqlBase):
	__tablename__ = "pages"

	file = Column(String, nullable=False, primary_key=True)
	title = Column(String, nullable=False)
	link = Column(String, nullable=False)
	content = Column(String, nullable=False)
	created = Column(DateTime, nullable=False)
	base = Column(String, ForeignKey('bases.name'))

	def __init__(self, file, title, link, content, base=None):
		self.title = title
		self.link = link
		self.file = file
		self.content = content
		self.created = datetime.datetime.now()
		if base:
			self.base = base
	
class Bbqweb(object):
	def __init__(self, db, outdir):
		#try:
		# TODO: add base check, enforce adding base
		if True:
			engine = create_engine("sqlite:///%s" % db)
			Session = sessionmaker(bind=engine)
			SqlBase.metadata.bind = engine
			self.session = Session()
			SqlBase.metadata.create_all()
		
			self.outdir = outdir
			self.templates = TemplateLookup()
			if len(self.session.query(Base).all()) < 1:
				print "You have no templates. You should add one now."
				self.add_base()

			for row in self.session.query(Base):
				self.templates.put_string(row.name, row.content)

		#except:
		#	print "Error TODO MAX ERRORS OUT TO THE MAX"
	def selection(self):
		select = {
			'g': self.generate,
			'1': self.add_page,
			'2': self.add_base,
			'q': self.conclude
		}
		while True:
			print "-------------"
			print "bbqweb alpha."
			print "-------------"
			print ""
			print "Options:"
			print "  (g) generate website"
			print "  (1) add page"
			print "  (2) add base"
			print "  (*) edit page"
			print "  (*) edit base"
			print "  (*) show pages"
			print "  (*) show bases"
			print "  (q) quit"
			print ""
			print "Make a selection:",
			select.get(raw_input(), lambda: None)()
			print ""
		
	def conclude(self):
		self.session.commit()
		self.session.close()
		sys.exit()

	def generate(self):
		#TODO outdir checks
		print "Order by:"
		print "  (1) title"
		print "  (2) created date"
		print ""
		x = raw_input("Selection:")
		if x == '1':
			x = Page.title
		elif x == '2':
			x = Page.created
		else:
			print "Poor selection."
			return
		t = self.templates.get_template("index")
		args = []
		for row in self.session.query(Page).order_by(x):
			args.append([row.link, row.title, row.file])
			f = open("%s/%s" % (self.outdir, row.file), 'wb')
			f.write(row.content)
			f.close()
			print "File %s written." % row.file
		index_content = t.render(rows=args)
		f = open("%s/index.shtml" % self.outdir, 'wb')
		f.write(index_content)
		f.close()
		print "File index.shtml written."
		print "Operation complete."

	def add_page(self):
		correct = False
		while not correct:
			f = raw_input("Filename: ").strip()
			t = raw_input("Title: ").strip()
			l = raw_input("Link: ").strip()
			raw_input("Using nano for inserting content. Press ENTER.")	
			# HACK: convoluted wtf.
			tmp = NamedTemporaryFile(delete=False)
			proc = call(['nano', '-w', tmp.name])
			tmp.close()
			tmp2 = open(tmp.name, 'rb')
			c = tmp2.read().strip()
			tmp2.close()
			os.unlink(tmp.name)
			assert(os.path.exists(tmp.name) == False)
			
			# base here
			while True:
				x = raw_input("Is your input correct [Y/N]? ")
				if x.lower() not in ('y', 'n'):
					print "Please enter Y or N."
				elif x.lower() == 'y':
					correct = True
					break
				else: 
					break
			if correct:
				p = Page(f,t,l,c)
				self.session.add(p)
				self.session.commit()


	def add_base(self):
		correct = False
		while not correct:
			f = raw_input("Name: ").strip()
			if len(self.session.query(Base).filter(Base.name==f).all()) > 0:
				print "This name already exists." 
				if(not self.yes_no("Continue")):
					continue

			raw_input("Using nano for inserting content. Press ENTER.")	
			# HACK: convoluted wtf.
			tmp = NamedTemporaryFile(delete=False)
			proc = call(['nano', '-w', tmp.name])
			tmp.close()
			tmp2 = open(tmp.name, 'rb')
			c = tmp2.read().strip()
			tmp2.close()
			os.unlink(tmp.name)
			assert(os.path.exists(tmp.name) == False)
			
			# base here
			if self.yes_no("Is your input correct"):
				correct = True

			if correct:
				q = self.session.query(Base).filter(Base.name==f).all()
				b = None
				if len(q) > 0:
					b = q[0]
					b.content = c
				else:
					b = Base(f,c)
				self.session.add(b)
				self.session.commit()

	def yes_no(self, msg):
		while True:
			x = raw_input("%s [Y/N]?" % msg)
			if x.lower() not in ('y', 'n'):
				print "Please enter Y or N."
			elif x.lower() == 'y':
				return True	
			else: 
				return False

if __name__ == "__main__":
	if len(sys.argv) > 2:
		bbqweb = Bbqweb(sys.argv[1], sys.argv[2])
		bbqweb.selection()
