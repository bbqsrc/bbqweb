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
	def __init__(self, db):
		#try:
		if True:
			engine = create_engine("sqlite:///%s" % db)
			Session = sessionmaker(bind=engine)
			SqlBase.metadata.bind = engine
			self.session = Session()
			SqlBase.metadata.create_all()
		#except:
		#	print "Error TODO MAX ERRORS OUT TO THE MAX"
	def selection(self):
		select = {
			'1': self.add_page,
			'2': self.add_base,
			'q': self.conclude
		}
		while True:
			print "bbqweb alpha."
			print "-------------"
			print ""
			print "Options:"
			print "  (1) add page"
			print "  (2) add base"
			print "  (3) show pages"
			print "  (4) show bases"
			print "  (q) quit"
			print ""
			print "Make a selection: ",
			select.get(raw_input(), lambda: None)()
		
	def conclude(self):
		self.session.commit()
		self.session.close()
		sys.exit()

	def add_page(self):
		correct = False
		while not correct:
			f = raw_input("Filename: ")
			t = raw_input("Title: ")
			l = raw_input("Link: ")
			raw_input("Using vim for inserting content. Press ENTER.")	
			# HACK: convoluted wtf.
			tmp = NamedTemporaryFile(delete=False)
			proc = call(['vim', tmp.name])
			tmp.close()
			tmp2 = open(tmp.name, 'rb')
			c = tmp2.read()
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


	def add_base(self):
		pass
if __name__ == "__main__":
	if len(sys.argv) > 1:
		bbqweb = Bbqweb(sys.argv[1])
		bbqweb.selection()
