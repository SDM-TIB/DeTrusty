# Configuration file for the Sphinx documentation builder.
#
# For a full list of options see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import re
import subprocess
import sys
sys.path.insert(0, os.path.abspath('../'))
from DeTrusty import __version__


# -- Project information -----------------------------------------------------
project = 'DeTrusty'
copyright = '2020-2024, Philipp D. Rohde, Avellino and Mazen Bechara'
author = 'Philipp D. Rohde, Avellino, Mazen Bechara'

version = __version__
release = __version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_multiversion',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'sphinx_mdinclude',
    'sphinxcontrib.bibtex',
]

# bibtex configuration
bibtex_bibfiles = ['refs.bib']
bibtex_default_style = 'unsrt'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.md']

# The name of the Pygments (syntax highlighting) style to use.
# pygments_style = 'friendly'
pygments_style = "sphinx"


# -- Options for autodoc ----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "description"

# Don't show class signature with the class' name.
autodoc_class_signature = "separated"

# Don't show the module name.
add_module_names = False

autodoc_default_flags = ['members']
autosummary_generate = True


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'css/custom.css',
]

html_logo = '_images/logo.png'

html_copy_source = False

# configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/{.major}'.format(sys.version_info), None),
}


# -- Options for sphinx-multiversion ------------------------------------------
# Docs exist from v0.12.2 on. Only the latest patch release of each minor series
# is built (e.g., v0.15.6 for 0.15.x) and published as /v0.15.6/.
FIRST_DOCUMENTED = (0, 12, 2)


def _latest_patch_tags():
    out = subprocess.run(['git', 'tag'], capture_output=True, text=True, cwd=os.path.dirname(__file__) or '.').stdout
    best = {}
    for tag in out.split():
        m = re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', tag)
        if not m:
            continue
        ver = tuple(int(g) for g in m.groups())
        if ver < FIRST_DOCUMENTED:
            continue
        if ver[:2] not in best or ver > best[ver[:2]]:
            best[ver[:2]] = ver
    return ['v%d.%d.%d' % v for v in best.values()]


_TAGS = sorted(_latest_patch_tags(), key=lambda t: tuple(int(x) for x in t[1:].split('.')), reverse=True)
# sphinx-multiversion sorts the refs alphabetically (e.g., v0.100.0 < v0.99.0). The Makefile hands
# this newest-first order to the templates via `-D html_context.release_order=...`.
RELEASE_ORDER = ','.join(_TAGS)
smv_tag_whitelist = r'^(%s)$' % '|'.join(re.escape(t) for t in _TAGS) if _TAGS else r'^$'
smv_branch_whitelist = r'^$'
smv_remote_whitelist = None
smv_latest_version = 'latest'
smv_outputdir_format = '{ref.name}'

# Render the version switcher on every page (and in all versions, since
# sphinx-multiversion uses the templates of the ref it is run from).
html_sidebars = {'**': ['versions.html']}
