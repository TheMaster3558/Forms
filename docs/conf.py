# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath('..'))


import datetime
import json

from forms.constants import CONFIG_PATH

project = 'Forms'
author = 'The Master'
copyright = f'{datetime.datetime.now().year}, {author}'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['revitron_sphinx_theme']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'revitron_sphinx_theme'
html_static_path = ['_static']
html_theme_options = {'color_scheme': 'dark', 'logo_mobile': 'images/logo.png'}
html_context = {'landing_page': {'menu': []}}

os.chdir('..')
try:
    with open(CONFIG_PATH, 'r') as f:
        data = json.load(f)
    invite_url = data['invite_url']
except (FileNotFoundError, KeyError):
    pass
else:
    html_context['landing_page']['menu'].append({'title': 'Invite', 'url': invite_url})
os.chdir('./docs')

html_logo = 'images/logo.png'
