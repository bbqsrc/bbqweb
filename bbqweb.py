#!/usr/bin/env python
from mako.template import Template
from mako.lookup import TemplateLookup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, Numeric, String, MetaData, ForeignKey, DateTime, PickleType, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from subprocess import *
import datetime
import sys, os, os.path
from glob import glob
import readline
from tempfile import NamedTemporaryFile

SqlBase = declarative_base()

class Config(SqlBase):
	__tablename__ = "config"

	key = Column(String, nullable=False, primary_key=True)
	value = Column(String)

	def __init__(self, key, value):
		self.key = key
		self.value = value

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
			Session = sessionmaker(bind=engine, autoflush=True, autocommit=True)
			SqlBase.metadata.bind = engine
			self.session = Session()
			SqlBase.metadata.create_all()
		
			self.outdir = outdir
			if not os.path.isdir(outdir):
				os.mkdir(outdir) #TODO sanitise, etc

			self.templates = TemplateLookup()
			self.db_init()
			for row in self.session.query(Base):
				self.templates.put_string(row.name, row.content)
		#except:
		#	print "Error TODO MAX ERRORS OUT TO THE MAX"
	
	def db_init(self):
		if len(self.session.query(Base).all()) < 1:
			print "You have no templates. You must add the index now."
			self.add_base("index")
		q = self.session.query(Config).filter(Config.key=="scpdir").all()
		conf = None
		if len(q) < 1:
			conf = Config("scpdir", None)
			self.session.add(conf)

	def selection(self):
		def invalid():
			print "Invalid selection."

		select = {
			'?': self.usage,
			'usage': self.usage,
			
			'g': self.generate,
			'generate': self.generate,
			
			'q': self.conclude,
			'quit': self.conclude,
			'exit': self.conclude,
			
			'a': self.add_page,
			'add': self.add_page,
			'add page': self.add_page,
			
			'ab': self.add_base,
			'add base': self.add_base,

			'd': self.delete_page,
			'delete': self.delete_page,

			'db': self.delete_base,
			'delete base': self.delete_base,

			'e': self.edit_page,
			'edit': self.edit_page,
			'edit page': self.edit_page,
			
			'eb': self.edit_base,
			'edit base': self.edit_base,

			's': self.show_pages,
			'show': self.show_pages,
			'show pages': self.show_pages,
			
			'sb': self.show_bases,
			'show bases': self.show_bases,

			'u': self.upload,
			'upload': self.upload
		}
		print "\n> bbqweb alpha."
		while True:
			x = raw_input("Make a selection (? for usage): ")
			print ""
			select.get(x, invalid)()
	
	def usage(self):
		print "> Options:"
		print " (a)  add page"
		print " (ab) add base"
		print " (d)  delete page"
		print " (db) delete base"
		print " (e)  edit page"
		print " (eb) edit base"
		print " (g)  generate website"
		print " (s)  show pages"
		print " (sb) show bases"
		print " (u)  upload using SCP"
		print " (q)  quit"


	def conclude(self):
		#self.session.commit()
		self.session.close()
		sys.exit()

	def generate(self):
		#TODO outdir checks
		print "> Order by:"
		print " (1) title"
		print " (2) created date"
		print ""
		x = raw_input("Selection: ")
		if x == '1':
			x = Page.title
		elif x == '2':
			x = Page.created
		else:
			print "Poor selection."
			return
		for b in self.session.query(Base):
			t = self.templates.get_template(b.name)
			args = []
			for row in self.session.query(Page).filter(Page.base==b.name).order_by(x):
				args.append([row.link, row.title, row.file])
				f = open("%s/%s" % (self.outdir, row.file), 'wb')
				f.write(row.content)
				f.close()
				print row.file
		
		index_content = t.render(rows=args)
		f = open("%s/index.shtml" % self.outdir, 'wb')
		f.write(index_content)
		f.close()
		
		print "index.shtml"
		print "Operation complete."
	
	def upload(self, dest=None):
		q = self.session.query(Config).filter(Config.key=="scpdir").one()
		if not dest:
			dest = raw_input("Destination [%s]: " % q.value).strip()
			if not dest and q.value:
				dest = q.value
		if dest:
			q.value = dest
			self.session.add(q)
			os.chdir(os.path.realpath(self.outdir))
			proc = call(['scp'] + glob("*") + [dest])

	def edit_page(self, f=None, c=None):
		correct = False
		while not correct:
			if not f:
				f = raw_input("Link: ").strip()
			if f == 'q':
				break
			q = self.session.query(Page).filter(Page.link==f).all()
			if len(q) > 0:
				q = q[0]
			else:
				print "Does not exist. Try again."
				continue
			
			if not c:
				tmp = NamedTemporaryFile(delete=False)
				tmp.write(q.content)
				tmp.close()
				proc = call(['nano', '-w', tmp.name])
				if self.yes_no("Is your input correct"):
					correct = True
				tmp2 = open(tmp.name, 'rb')
				c = tmp2.read().strip()
				tmp2.close()
				os.unlink(tmp.name)
				assert(os.path.exists(tmp.name) == False)
			
			if correct:
				q.content = c
				self.session.add(q)
				print "Page '%s' edited successfully\n--" % q.link
	
	def edit_base(self, n=None, c=None):
		correct = False
		while not correct:
			if not n:
				n = raw_input("Name: ").strip()
			if n == 'q':
				break
			q = self.session.query(Base).filter(Base.name==n).all()
			if len(q) > 0:
				q = q[0]
			else:
				print "Base '%s' does not exist. Try again." % f
				continue
			
			if not c:
				tmp = NamedTemporaryFile(delete=False)
				tmp.write(q.content)
				tmp.close()
				proc = call(['nano', '-w', tmp.name])
				if self.yes_no("Is your input correct"):
					correct = True
				tmp2 = open(tmp.name, 'rb')
				c = tmp2.read().strip()
				tmp2.close()
				os.unlink(tmp.name)
				assert(os.path.exists(tmp.name) == False)
			
			if correct:
				q.content = c
				self.session.add(q)
				print "Base '%s' edited successfully\n--" % q.name
			
	def show_pages(self):
		print "> Pages:"
		for i, row in enumerate(self.session.query(Page).all()):
			print " %d. %s" % (i, row.link)

	def show_bases(self):
		print "> Bases:"
		for i, row in enumerate(self.session.query(Base).all()):
			print " %d. %s" % (i, row.name)
	
	def add_page(self, f=None, t=None, l=None, c=None, b=None):
		correct = False
		while not correct:
			if not f:
				f = raw_input("Filename: ").strip()
			if not t:
				t = raw_input("Title: ").strip()
			if not l:
				l = raw_input("Link: ").strip()
			if not b:
				while True:
					b = raw_input("Base [index]: ").strip()
					if b == "":
						b = "index"
						break
					
					q = self.session.query(Base).filter(Base.name==b).all()
					if len(q) > 0:
						b = q[0].name
						break	
			
			if not c:
				#raw_input("Using nano for inserting content. Press ENTER.")	
				# HACK: convoluted wtf.
				tmp = NamedTemporaryFile(delete=False)
				tmp.write("Add your content here.")
				tmp.close()
				proc = call(['nano', '-w', tmp.name])
				if self.yes_no("Is your input correct?"):
					correct = True
				tmp2 = open(tmp.name, 'rb')
				c = tmp2.read().strip()
				tmp2.close()
				os.unlink(tmp.name)
				assert(os.path.exists(tmp.name) == False)
			
			# base here
			
			if correct:
				p = Page(f,t,l,c,b)
				self.session.add(p)
				print "Page '%s' successfully added.\n--" % p.link


	def add_base(self, f=None, c=None):
		correct = False
		while not correct:
			if not f:
				f = raw_input("Name: ").strip()
			if len(self.session.query(Base).filter(Base.name==f).all()) > 0:
				print "This name already exists." 
				if(not self.yes_no("Continue")):
					continue
			
			if not c:
				#raw_input("Using nano for inserting content. Press ENTER.")	
				# HACK: convoluted wtf.
				tmp = NamedTemporaryFile(delete=False)
				tmp.write("Add your content here.")
				tmp.close()	
				proc = call(['nano', '-w', tmp.name])
				if self.yes_no("Is your input correct"):
					correct = True
				tmp2 = open(tmp.name, 'rb')
				c = tmp2.read().strip()
				tmp2.close()
				os.unlink(tmp.name)
				assert(os.path.exists(tmp.name) == False)
			
			# base here

			if correct:
				q = self.session.query(Base).filter(Base.name==f).all()
				b = None
				if len(q) > 0:
					b = q[0]
					b.content = c
				else:
					b = Base(f,c)
				self.session.add(b)
				print "Base '%s' successfully added.\n--" % b.name

	def delete_page(self, l=None):
		if not l:
			l = raw_input("Link: ")
		q = self.session.query(Page).filter(Page.link==l).all()
		if len(q) > 0 and q[0].link == l:
			if self.yes_no("Are you sure you want to delete '%s'" % l):
				self.session.delete(q[0])
				print "Page '%s' deleted successfully.\n--" % l
		else:
			print "'%s' does not exist." % l

	def delete_base(self, n=None):
		if not n:
			n = raw_input("Name: ")
		q = self.session.query(Base).filter(Base.name==n).all()
		if len(q) > 0 and q[0].name == n:
			if self.yes_no("Are you sure you want to delete '%s'" % n):
				self.session.delete(q[0])
				print "Page '%s' deleted successfully.\n--" % n
		else:
			print "'%s' does not exist." % n

	def yes_no(self, msg):
		while True:
			x = raw_input("%s [Y/N]? " % msg).strip()[0]
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
	else:
		print "bbqweb alpha."
		print "Usage: %s <sqlite.db> <output_dir>" % sys.argv[0]
