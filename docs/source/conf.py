import os
import sys
from unittest.mock import MagicMock

# Allow Sphinx to import the app package
sys.path.insert(0, os.path.abspath('../..'))

# Mock heavy dependencies so ReadTheDocs doesn't need to install them
_MOCK_MODULES = [
    'psycopg2', 'psycopg2.extras',
    'flask', 'flask.session', 'flask.redirect', 'flask.url_for', 'flask.abort',
    'dotenv', 'supabase', 'jwt',
    'mimetypes',
]
for mod_name in _MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()

# -- Project information -----------------------------------------------------
project = 'Snip-Snap'
copyright = '2026, Cyrus Alli'
author = 'Cyrus Alli'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# autodoc defaults: show members, don't skip private (_) unless double-underscore
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'private-members': False,
}

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
