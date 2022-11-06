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

from forms.constants import INVITE_URL, GITHUB_URL

project = 'Forms'
author = 'The Master'
copyright = f'{datetime.datetime.now().year}, {author}'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'revitron_sphinx_theme'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'revitron_sphinx_theme'
html_static_path = ['_static']
html_theme_options = {
    'color_scheme': 'dark',
    'github_url': GITHUB_URL,
    'logo_mobile': 'images/logo.png'
}
html_context = {
    'landing_page': {
        'menu': [
            {'title': 'Invite', 'url': INVITE_URL},
            {'title': 'GitHub', 'url': GITHUB_URL}
        ]
    }
}
html_logo = 'images/logo.png'
