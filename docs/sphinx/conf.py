#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join('..','..')))

extensions = [ 'sphinx.ext.autodoc',
               'sphinx.ext.todo',
               'sphinx.ext.viewcode']
source_suffix = '.rst'
master_doc = 'index'
project = u'tortilla8'
copyright = u'2017, adam nunez'
author = u'adam nunez'
version = u'0.2'
release = u'0.2'
language = None
exclude_patterns = ['_build']
pygments_style = 'sphinx'
todo_include_todos = True
html_theme = 'classic'
#html_theme_options = {}
htmlhelp_basename = 'tortilla8doc'
man_pages = [ (master_doc, 'tortilla8', u'tortilla8 Documentation',[author], 1) ]
texinfo_documents = [ (master_doc, 'tortilla8', u'tortilla8 Documentation',
    author, 'tortilla8', 'One line description of project.', 'Miscellaneous') ]
