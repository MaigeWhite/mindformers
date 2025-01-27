# Copyright 2023 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
"""Configuration file for the Sphinx documentation builder."""

import os
import shutil
from sphinx.util import logging

# -- Project information -----------------------------------------------------

project = 'mindformers'
# pylint: disable=W0622
copyright = '2023, mindformers contributors'
author = 'mindformers contributors'

# The full version, including alpha/beta/rc tags
release = 'dev'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['myst_parser',
              'sphinx.ext.autodoc',
              'sphinx.ext.viewcode',
              'sphinx.ext.autosummary',
              'sphinx.ext.intersphinx']

source_suffix = {'.rst': 'restructuredtext',
                 '.md': 'markdown'}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

pygments_style = 'sphinx'

autodoc_inherit_docstrings = False

autosummary_generate = True

# -- Options for HTML output -------------------------------------------------

# Reconstruction of sphinx auto generated document translation.
language = 'zh_CN'
gettext_compact = False

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Copy source files of chinese python api from mindscience repository.
logger = logging.getLogger(__name__)


copy_path = ['../../../../README.md',
             '../../../aicc_cards',
             '../../../feature_cards',
             '../../../model_cards',
             '../../../task_cards',
             '../../../FAQ.md',
             '../../../transformer仓Python编程规范.md']


def copy_file_to_docs(ori_name):
    """copy dir in docs to readthedocs workspace."""
    current_path = os.path.abspath('__file__')
    ori_path = os.path.realpath(os.path.join(current_path, ori_name))
    new_path = os.path.realpath('/'.join(ori_path.split('/')[-2:]))
    if ori_name.endswith('README.md'):
        new_path = os.path.realpath(ori_path.split('/')[-1])
        shutil.copy(ori_path, new_path)
    elif ori_name.endswith('.md'):
        shutil.copy(ori_path, new_path)
    else:
        shutil.copytree(ori_path, new_path)

for file_path in copy_path:
    copy_file_to_docs(file_path)

# split README
with open('README.md', 'r') as f:
    title_list = ['Introduction', 'Install', 'Version_Match', 'Quick_Tour', 'Contribution', 'License']
    title_for_index = ['# 一、介绍', '# 二、安装', '# 三、版本配套', '# 四、快速开始', '-', '-']
    file_count = 0
    fn = None
    for line in f:
        if line.startswith('##') and not line.startswith('###'):
            if fn:
                fn.close()
            fn = open(f'docs/start/{title_list[file_count]}.md', 'w')
            fn.write(title_for_index[file_count])
            file_count += 1
            continue
        if fn:
            fn.write(line)
    fn.close()

def setup(app):
    app.add_css_file('my_theme.css')
