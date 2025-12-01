# SPDX-FileCopyrightText: 2025 PHYTEC
# SPDX-License-Identifier: MIT

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys


def read(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with open(os.path.join(here, rel_path)) as fp:
        return fp.read()


def get_version(rel_path: str) -> str:
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            # __version__ = "0.9"
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

project = 'EEPROM Flashtool'
copyright = '2025, PHYTEC Holding AG'
author = 'PHYTEC Holding AG'
release = get_version('../../phytec_eeprom_flashtool/src/__init__.py')

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/logo-phytec.svg'
html_css_files = ['theme.css']

# -- Options for LaTeX to PDF output -----------------------------------------
root_doc = 'index'
latex_engine = 'pdflatex'  # or 'xelatex' or 'lualatex'

latex_elements = {
    # Paper size ('letterpaper' or 'a4paper')
    'papersize': 'a4paper',

    # Font size ('10pt', '11pt' or '12pt')
    'pointsize': '11pt',

    # Additional preamble content
    'preamble': r'''
        \usepackage{charter}
        \usepackage[defaultsans]{lato}
        \usepackage{inconsolata}
    ''',

    # Figure alignment
    'figure_align': 'htbp',

    # Custom title page
    'maketitle': r'''
        \begin{titlepage}
            \centering
            \includegraphics[width=0.4\textwidth]{logo-phytec.png}\par
            \vspace*{2cm}
            {\Huge\bfseries PHYTEC EEPROM Flashtool\par}
            \vspace{1cm}
            {\Large Documentation\par}
            \vspace{2cm}
            {\large Version ''' + release + r''' \par}
            \vfill
            {\large \today\par}
        \end{titlepage}
    ''',

    # Table of contents depth
    'tableofcontents': r'\sphinxtableofcontents',
}

# LaTeX document class
latex_documents = [
    (root_doc, 'phytec-eeprom-flashtool.tex', 'PHYTEC EEPROM Flashtool Documentation',
     'support@phytec.de', 'manual'),
]

# Logo for LaTeX output
latex_logo = '_static/logo-phytec.png'

# Additional LaTeX styling
latex_theme = 'manual'  # or 'howto'
