# -*- coding: utf-8 -*-
#
# build_otis.py
#
# (C) D.C.-G. (LaChal) 2018
#
# Build .oti files fo dat2obj.py
#
# Reads a given .plist file and extract the texture data needed by dat2obj.py
# Requires pbPlist v1.0.3 (https://pypi.python.org/pypi/pbPlist/1.0.3)
#
"""
Builds .oti files for dat2obj.py

Usage:

python build_oti.py <plist_file> <dat_files_dir> [<output_dir>]

"""
from __future__ import unicode_literals

import os
import sys

# Ensure the virtual environment is loaded if it exists.
# Deactivate pylint import order checks since we need to activate the virtual environment before
# importing pbPList.
# pylint: disable=wrong-import-position
__VENV = False
if os.path.isdir(".venv/lib/python2.7"):
    if sys.platform == "win32":
        ACTIVATE_THIS = os.path.abspath(".venv/Scripts/activate_this.py")
    else:
        ACTIVATE_THIS = os.path.abspath(".venv/bin/activate_this.py")
    execfile(ACTIVATE_THIS, dict(__file__=ACTIVATE_THIS))
    __VENV = True

import glob
from pbPlist import pbPlist

# Ensure we can use dat2obj.py as a module.
sys.path.insert(1, "..")
from dat2obj import get_sections
# pylint: enable=wrong-import-position


def read_plist(f_path):
    """Reads a plist file.
    :f_path: string: path to the plist file to read.
    Returns a pbPlist.PBPlist instance.
    """
    assert os.path.isfile(f_path)
    return pbPlist.PBPlist(f_path).root.value


def get_models_map(plist):
    """Builds the models map from plist data.
    :plist: dict: plist data to be scanned.
    Returns a dict like:
    {"model_file_name.dat": "model_entry_name_in_plist"}
    """
    models = {}
    for name, value in plist.items():
        if "model" in value.keys():
            models[value["model"]] = name
    return models


def get_tex_aliases(f_name, tex_aliases=None):
    """Find the texture names (aliases) in the given .dat file and update the tex_aliases dict.
    :f_name: string: The file path to read.
    :tex_aliases: dict: Dictionary to update. Defaults to an empty dict.
    Returns the updated tex_aliases dict.
    """
    if tex_aliases is None:
        tex_aliases = {}
    with open(f_name, "rU") as f_in:
        aliases = get_sections(unicode(f_in.read())).get("NAMES", {}).get("data")
    if aliases:
        tex_aliases[os.path.basename(f_name)] = aliases
    return tex_aliases


def write_oti(name, directory, tex_names, plist):
    """Writes the .oti file.
    :name: string: The .dat file name to write the .oti for.
    :directory: string: Where to write the .oti file.
    :tex_names: list/tuple: List of the textures names (aliases). The order of elements defines in
        which order the real textures names are written in the .oti file.
    :plist: dict: Contains the 'model' data extracted from a .plist file.
    Retruns nothing.
    """
    lines = []
    for tex in tex_names:
        lines.append(getattr(plist["materials"].get(tex, {}).get("diffuse_map", tex), "value", tex))
    f_name = os.path.join(directory, os.path.extsep.join((os.path.splitext(name)[0], "oti")))
    with open(f_name, "w") as f_out:
        f_out.write("\n".join(lines))


def main(args=None):
    """Program bootstrap."""
    print "= Starting build_otis."
    if not args:
        args = sys.argv[1:]
    if __VENV:
        print "  (Virtual environment in '.venv' activated.)"
    if len(args) < 3:
        print "! ERROR: Too many CLI arguments."
        print "Put at least two positional arguments on CLI:"
        print "<plist_file> <dat_files_dir>"
        sys.exit(1)
    f_plist = args[0]
    dat_dir = output_dir = args[1]
    if len(args) == 3:
        output_dir = args[2]
    plist = read_plist(f_plist)
    models = get_models_map(plist)

    # Scan the .dat files in the directory given as second CLI arg to get names order.
    # Store them in a dict with file base name (without ext) as keys.
    names = sorted(glob.glob(os.path.join(dat_dir, "*.dat")))
    tex_aliases = {}
    for name in names:
        print "* Finding texture aliases for '%s'." % name
        tex_aliases = get_tex_aliases(name, tex_aliases)

    # Get the materials information from the .plist file.
    for name, aliases in tex_aliases.items():
        model = models.get(name)
        if model:
            print "* Writing .oti file for '%s'." % name
            write_oti(name, output_dir, aliases, plist[model])


if __name__ == '__main__':
    main()
