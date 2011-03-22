bbqweb - my own personal offline content management system
==========================================================

I created this "CMS" because I was lazy (yes, I code when I'm lazy, fancy that).
This allows me to store all of my HTML in an SQLite DB, and regenerate the site
at will. This has the advantage of thoughtless generation, ie, it will just work
when you add a new page :).

Requirements
------------
* Python 2.6 or greater (might work with lower, untested)
* SQLAlchemy 0.5 or greater
* Mako 0.4 or greater

Usage
-----
> python <database.db> <path/to/output/html/files>
*   A menu will appear. 
*   For now, you must add at least one base and call it 'index'
    *   Failing to do so may cause crashes (ie, guaranteed to fail generation)
*   Add pages at will.
    *   Right now the code pretty much caters for my JS file which hasn't been 
	    added yet. You can get it from [js](http://bbqsrc.net/bbqsrc.js).

Alright, that's that for the alpha version of my crappy CMS thingy. Enjoy, or 
not.
