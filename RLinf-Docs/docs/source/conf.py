import os
import pathlib
import re
import sys

# Ensure project root is on Python path for autodoc
sys.path.insert(0, os.path.abspath("../../"))


# -- Project Information -------------------------------------------------------

project   = 'RLinf'
author    = 'Zhexuan Xu'
copyright = '2025 RLinf Team'
release   = 'v1'


# -- General Configuration -----------------------------------------------------

extensions = [
    "myst_parser",           # Markdown support
    'sphinx.ext.mathjax',
    "sphinx_copybutton",     # “Copy” button for code blocks
    "sphinx.ext.autodoc",    # API documentation from docstrings
    "sphinx.ext.autosummary",# Generate summary tables
    "sphinx.ext.napoleon",   # Google & NumPy style docstrings
    "sphinx_sitemap",        # Sitemap generation
    'sphinxcontrib.video',
    # "sphinx.ext.viewcode", # Source code links (optional)
]

# File types for source documents
source_suffix = {
    '.rst': 'restructuredtext',
    '.md':  'markdown',
}

templates_path    = ['_templates']
exclude_patterns  = []
default_role      = 'code'
autosummary_generate = True

# Autodoc defaults: include members and inheritance
# autodoc_default_options = {
#     "members":            True,
#     "inherited-members":  True,
#     "show-inheritance":   True,
# }


# -- HTML Output Options -------------------------------------------------------

html_theme        = "pydata_sphinx_theme"
html_show_sourcelink = False  # Hide “View page source” link
html_baseurl      = "https://RLinf-docs.readthedocs.io/en/latest/"
html_favicon      = "_static/favicon.ico"
html_static_path  = ['_static']
html_css_files    = [
    "css/custom.css",
    "css/sphinx-modal.css",
    "css/mode-selection.css",
]
html_js_files     = [
    'typesense.min.js',
    'js/config-manager.js',
    'js/typesense-client.js',
    'js/message-manager.js',
    'js/ai-chat-service.js',
    'js/mode-badge.js',
    'js/mode-panel.js',
    'sphinx-modal-widget.js',
]
html_sidebars     = {
    "**": ["sidebar-nav-bs.html"]
}


# -- Theme Options -------------------------------------------------------------

def render_svg_logo(path, width="4rem", height="auto"):
    """Embed and size an SVG logo from the static directory."""
    svg_file = pathlib.Path(__file__).parent / path
    svg_text = svg_file.read_text(encoding="utf-8")
    return re.sub(r"<svg\b",
                  f'<svg width="{width}" height="{height}"',
                  svg_text, count=1)

html_theme_options = {
    "logo": {
        "svg": render_svg_logo("_static/svg/logo.svg")
    },
    "navbar_start":   ["navbar-logo"],
    "navbar_center":  ["navbar-nav"],
    "navbar_end":     ["version-switcher", "navbar-icon-links", "askai"],
    "navbar_align":   "left",
    "secondary_sidebar_items": {
        "**": ["page-toc"],
        "index": [],
    },
    "collapse_navigation":     True,
    "show_nav_level":          2,
    "navigation_depth":        4,
    "header_links_before_dropdown": 10,
    "icon_links": [
        {
            "name": "GitHub",
            "url":  "https://github.com/RLinf/RLinf",
            "icon": "fab fa-github",
            "type": "fontawesome",
        },
    ],
    "switcher": {
        "json_url":      "_static/versions.json",
        "version_match": release,
    },
}


# -- HTML Context & Setup ------------------------------------------------------

def setup_html_context(app, pagename, templatename, context, doctree):
    """Inject build-time config values into templates."""
    cfg = app.config
    context.update({
        'typesense_host':       getattr(cfg, 'typesense_host', 'localhost'),
        'typesense_port':       getattr(cfg, 'typesense_port', 8108),
        'typesense_protocol':   getattr(cfg, 'typesense_protocol', 'http'),
        'typesense_api_key':    getattr(cfg, 'typesense_api_key', ''),
        'typesense_collection': getattr(cfg, 'typesense_collection', 'sphinx_docs'),
        'sphinx_env':           getattr(cfg, 'sphinx_env', 'development'),
        'sphinx_debug':         getattr(cfg, 'sphinx_debug', 'false'),
    })

def setup(app):
    """Register custom config values and connect context setup."""
    # Allow overriding via -D flags
    app.add_config_value('typesense_host',     'typesense.product-team-dev.infini-ai.com', 'html')
    app.add_config_value('typesense_port',     9443, 'html')
    app.add_config_value('typesense_protocol', 'https', 'html')
    app.add_config_value('typesense_api_key',  'hAvqOEYEbtQwuFvm0SeclKHmCX4QXgs3', 'html')
    app.add_config_value('typesense_collection','infini-RL', 'html')
    app.add_config_value('sphinx_env',         'development', 'html')
    app.add_config_value('sphinx_debug',       'false', 'html')

    app.connect('html-page-context', setup_html_context)
    app.add_css_file("css/custom.css")

    return {
        'version':              '0.1',
        'parallel_read_safe':   True,
        'parallel_write_safe':  True,
    }
