# Configuration file for the Sphinx documentation builder.
import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

# -- Project information -----------------------------------------------------
project = 'RLInf'
copyright = '2025, xzxuan'
author = 'xzxuan'
release = 'v1'

# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",
    "sphinx_copybutton",

    "sphinx.ext.autodoc",             
    "sphinx.ext.autosummary",          
    "sphinx.ext.napoleon",      
    "sphinx_sitemap"      
    # "sphinx.ext.viewcode",            
]

on_rtd = os.environ.get("READTHEDOCS") == "True"

if on_rtd:
    html_baseurl = "https://rlinf-docs.readthedocs.io/en/latest/"
else:
    html_baseurl = "http://localhost:8000/"

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    # "undoc-members": True,
    "inherited-members": True,
    "show-inheritance": True,
}
# suppress_warnings = ["toc.excluded"]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
templates_path = ['_templates']
exclude_patterns = []

default_role = 'code'

# Remove the "View page source" link from the sidebar
html_show_sourcelink = False

# -- Options for HTML output -------------------------------------------------
html_theme = "pydata_sphinx_theme"

# Function to read SVG content for the logo
# import pathlib
# def render_svg_logo(path):
#     with open(pathlib.Path(__file__).parent / path, "r", encoding="utf-8") as f:
#         return f.read()
import pathlib, re
def render_svg_logo(path, width="4rem", height="auto"):
    svg_path = pathlib.Path(__file__).parent / path
    text = svg_path.read_text(encoding="utf-8")
    return re.sub(
        r"<svg\b",
        f'<svg width="{width}" height="{height}"',
        text,
        count=1,
    )

# Theme options to configure the navbar and sidebar
html_theme_options = {
    "logo": {
        "svg": render_svg_logo("_static/logo.svg")
    },

    "navbar_start": ["navbar-logo"],
    "navbar_end": ["theme-switcher", "version-switcher", "navbar-icon-links"],
    "navbar_align": "left",

    "navbar_center": ["navbar-nav"],
    "secondary_sidebar_items": ["page-toc"],
    # "page_sidebar_items": ["sidebar-nav-bs.html"],

    # Version switcher configuration (requires _static/versions.json)
    "switcher": {
        "json_url": "_static/versions.json",
        "version_match": release,
    },
    "primary_sidebar_end": [],
    "collapse_navigation": True,
    "show_nav_level": 1,
    "navigation_depth": 1,

    "header_links_before_dropdown": 10,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://cloud.infini-ai.com", # TODO: change to github link
            "icon": "fab fa-github",
            "type": "fontawesome",
        },
    ],
}

# Enhanced AI Chat Configuration
html_js_files = [
    'typesense.min.js',  # Local Typesense client library
    'js/config-manager.js',
    'js/typesense-client.js',
    'js/message-manager.js',
    'js/ai-chat-service.js',
    'js/mode-badge.js',
    'js/mode-panel.js',
    'sphinx-modal-widget.js',
]

html_css_files = [
    "css/custom.css",
    'css/sphinx-modal.css',
    'css/mode-selection.css',
    # 'https://cdn.jsdelivr.net/npm/typesense-docsearch-css@0.3.0'
]


html_sidebars = {
    "**": ["sidebar-nav-bs.html"]
}

html_favicon = "_static/favicon.ico"

# Paths for custom static files (such as CSS)
html_static_path = ['_static']

# Function to setup template context with build-time configuration
def setup_html_context(app, pagename, templatename, context, doctree):
    """Add build-time configuration variables to template context."""
    
    # Get configuration values injected via -D flags
    config = app.config
    
    # Template context for Sphinx AI configuration
    context.update({
        'typesense_host': getattr(config, 'typesense_host', 'localhost'),
        'typesense_port': getattr(config, 'typesense_port', 8108),
        'typesense_protocol': getattr(config, 'typesense_protocol', 'http'),
        'typesense_api_key': getattr(config, 'typesense_api_key', ''),
        'typesense_collection': getattr(config, 'typesense_collection', 'sphinx_docs'),
        'sphinx_env': getattr(config, 'sphinx_env', 'development'),
        'sphinx_debug': getattr(config, 'sphinx_debug', 'false'),
    })

def setup(app):
    """Setup function called by Sphinx."""
    
    # Register configuration values that can be set via -D flags
    app.add_config_value('typesense_host', 'localhost', 'html')
    app.add_config_value('typesense_port', 8108, 'html')
    app.add_config_value('typesense_protocol', 'http', 'html')
    app.add_config_value('typesense_api_key', '', 'html')
    app.add_config_value('typesense_collection', 'sphinx_docs', 'html')
    app.add_config_value('sphinx_env', 'development', 'html')
    app.add_config_value('sphinx_debug', 'false', 'html')
    
    # Connect the template context function
    app.connect('html-page-context', setup_html_context)
    
    app.add_css_file("css/custom.css")

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
