#!/bin/env python2
#
# -*- encoding: utf-8 -*-
#
# test_dat2obj.py
#
# Multi-platform test file for dat2obj.py
#
# (c) D.C.-G. 2018
#
# Not fitted for any commercial purpose!
#
r"""
This program tests if 'dat2obj.py' can convert Oolite mesh files to Wavefront .obj and .mtl files.

Supported platforms
-------------------

* Linux
* Windows


Prerequisites
-------------

* Python 2.7.3 and over (Python 3 not yet supported by this program).
  This program and 'dat2obj.py' **may** work with older versions of Python, but, no guaranty.
* An internet connection and your operating system being able to support TLS v1.2 protocol.
  The Python package pbPlist is used during the tests, and is not a standard Python package.
  It will be installed in a dedicated virtual environment using 'virtualenv' and 'pip'.
  You don't need to worry about that, this program will download and install the needed packages
  locally. Your system Python installation will not be modified.
  See 'Python dependencies' below for details.
* Oolite installed in the default location for your system.
  On Linux systems: '$HOME/GNUstep/Applications/Oolite/oolite.app'.
  On Windows: 'C:\Oolite\oolite.app'.
* The program 'build_otis.py' in the same folder as this one.
  If it is not there, call Houston, and say you've a problem...


Scenario
--------

<oolite folder> refers to the 'oolite.app' folder.
File system paths are given for Linux platforms.

1. Check and install dependencies. (See 'Python dependencies')
2. Create the 'output_l', 'output_r' and 'cmp_output' directories.
3. Copy all the files starting with 'oolite' and ending with '.dat' found in
   '<oolite dir>/Resources/Models' are copied in 'output_l'.
4. Needed '.oti' files are generated using 'build_otis.py' program.
5. All '.dat' files in 'output_l' are converted to '.obj' files in 'output_l'.
6. The generated '.obj' files in 'output_l' are converted back to '.dat' one in 'output_left'.
7. Needed '.dat' and '.oti' files are copied to 'output_right'.
8. Convert the '.dat' files in 'output_r' to '.obj' files in 'output_r'.
9. Compare '.obj' files in 'output_l' and 'output_r' and store differences in 'cmp_outpout'.
   Files in 'cmp_output' are generated only when diferrences are found.


Python dependencies
-------------------

If the needed Python dependency 'pbPlist' for this test program is not found in your system Python
installation, it is installed in a dedicated virtual environment in the current directory.
The Python package 'virtualenv' version 15.1.0 is used.
If it is not installed on you system Python installation, it will be downloaded and 'installed' only
for the tests. It won't be available for other Python programs.

The virtual environment directory '.venv' and the one containing 'virtualenv' '.virtualenv' can be
removed safely once the tests are finished.
"""
from __future__ import unicode_literals

import os
import sys
import glob
import re
import argparse
import importlib
import urllib2
import shutil
import difflib

DEBUG = False


class Options(object):  # pylint: disable=too-few-public-methods
    """Stores options.
    Options can be accessed using instance attributes or like a dict."""
    def __init__(self, options):
        """:options: dict: Options to store."""
        super(Options, self).__setattr__("options", options)

    def __getattribute__(self, key):
        """Returns self.option value for key, or self.<key> value.
        :key: string: The attribute name to return."""
        options = super(Options, self).__getattribute__("options")
        if key in options.keys():
            return options[key]
        return super(Options, self).__getattribute__(key)

    def __setattr__(self, key, value):
        """Set a value in self.options if not an instance attribute."""
        options = super(Options, self).__getattribute__("options")
        super_obj = super(Options, self)
        if key not in dir(super_obj):
            options[key] = value
        else:
            super_obj.__setattr__(key, value)

    def __getitem__(self, key):
        """Interface to get item like in a dict object."""
        return self.options[key]

    def __setitem__(self, key, value):
        """Interface to set item like in a dict object."""
        self.options[key] = value

    def items(self):
        """Returns internal dict keys."""
        return super(Options, self).__getattribute__("options").items()


def _get_file_names(pattern, src):
    """Finds all the file names corresponding to 'pattern' in 'src' directory.
    :pattern: string: Pattern to be used with glob.glob.
    :src: string: The directory to scan.
    Returns a sorted list of strings."""
    ## return sorted([os.path.join(src, a) for a in glob.glob(os.path.join(src, pattern))])
    return sorted(glob.glob(os.path.join(src, pattern)))

def _get_extractor(name):
    """Returns an 'extractor' by loading the corresponding lower case 'name' module.
    :name: string: The case sensitive name of the extractor object to get from the non-case
        sensitive 'name' module.
    This function is appliable only for modules like 'zipfile' and 'tarfile', because they contain
    a 'ZipFile' and 'TarFile' object respectively.
    Returns 'zipfile.ZipFile' or 'tarfile.open'."""
    mod = importlib.import_module(name.lower())
    extractor_cls = getattr(mod, name)
    if hasattr(mod, "open"):
        extractor_cls = getattr(mod, "open")
    if not extractor_cls:
        raise ImportError("Could not import '%s' from '%s'" % (name, mod))
    return extractor_cls


def _get_data(f_path):
    """Reads a given file and returns its lines.
    :f_path: string: Path to the file to read.
    Returns a list of strings."""
    with open(f_path, "U") as fin:
        data = fin.readlines()
    return data


def _install_virtualenv(version, name=".virtualenv"):
    """'Installs' virtualenv in the current directory.
    Actually download the archive and unpack it.
    :version: string: Version to be installed.
    :name: string: The name to rename the 'virtualenv-<version>' directory.
        Defaults to '.virtualenv'."""
    print "* Installing 'virtualenv' v%s locally." % version
    base_url = "https://github.com/pypa/virtualenv/archive/%s" % version
    if sys.platform == "win32":
        ext = "zip"
    else:
        ext = "tar.gz"
    result = urllib2.urlopen(".".join((base_url, ext)))

    arch_name = os.path.abspath(".".join(("virtualenv", ext)))
    with open(arch_name, "wb") as vfo:
        vfo.write(result.read())
        vfo.close()

    # Select he right module/class to extract the data according to the extension.
    extractor = _get_extractor({"tar.gz": "TarFile", "zip": "ZipFile"}[ext])
    arch_obj = extractor(arch_name, mode="r")
    arch_obj.extractall()
    arch_obj.close()

    # Rename the extracted archive, remove an existing folder before.
    if os.path.isdir(name):
        shutil.rmtree(name)
    os.rename("virtualenv-%s" % version, name)


def ensure_pbplist(opts):
    """Ensures that the 'pbPlist' module is avaiable.
    If it is not found, it is installed using virtualenv in a dedicated virtual environment (.venv)
    in the current directory."""
    print "* Checking pbPlist."
    try:
        pb_plist = importlib.import_module("pbPlist")
        del pb_plist
        print "* Found!"
    except ImportError:
        # Find virtualenv.
        print "! Not found. Installing..."
        inst_virtualenv = False
        vver = opts.virtualenv_version
        try:
            virtualenv = importlib.import_module("virtualenv")
            ver = virtualenv.__version__
            if ver != vver:
                print "! Wrong version for 'virtualenv': %s found, but %s wanted." % (ver, vver)
                inst_virtualenv = True
        except ImportError:
            # Trigger the installation
            print "! Can't find 'virtualenv' in sys.path."
            inst_virtualenv = True

        if inst_virtualenv:
            _install_virtualenv(vver)
            virtualenv = importlib.import_module("virtualenv")

        # Create the virtual environment and activate it.
        virtualenv.create_environment(".venv")
        execfile(".venv/bin/activate_this.py", dict(__file__=".venv2/bin/activate_this.py"))

        # Install pbPlist
        pip = importlib.import_module("pip")
        pip.main(args=["install", "pbPlist", "--prefix", sys.prefix])
        print "* pbPlist installed."


def init_options(opts):
    """Initializes options with default values according to the OS we're running on.
    :opts: object: 'Options' instance to initialize.
    Returns updated :opts."""
    if sys.platform == "win32":
        parts = ("C:\\", "Oolite", "oolite.app")
    else:
        parts = (os.environ["HOME"], "GNUstep", "Applications", "Oolite", "oolite.app")
    opts.oolite_app = oolite_app = os.path.join(*parts)
    opts.models_dir = os.path.join(oolite_app, "Resources", "Models")
    opts.plist_file = os.path.join(oolite_app, "Resources", "Config", "shipdata.plist")
    opts.virtualenv_version = "15.1.0"
    return opts


def parse_cli(opts):
    """Parses the command line options and populate the given 'opts' object.
    :opts: object: A 'Options' instance.
    Returns updated :opts."""
    cwd = os.getcwd()
    ## p_join = os.path.join
    arg_parser = argparse.ArgumentParser()
    add_arg = arg_parser.add_argument
    add_arg("--models-dir", help="The directory where the models .dat files are. Defaults to the " \
            "'Models' directory in the 'Resources' one in Oolite default installation directory",
            default=opts.models_dir)
    add_arg("--plist-file", help="Read the given .plist file to find texture aliases. Defaults " \
            "the 'shipdata.plist' file in the 'Config' directory in the 'Resources' ones in " \
            "Oolite default installation directory.",
            default=opts.plist_file)
    add_arg("--left-dir", help="The conversion first pass directory to store files in. Defaults " \
            ## "to 'output_l' in the current directory.", default=p_join(cwd, "output_l"))
            "to 'output_l' in the current directory.", default="output_l")
    add_arg("--right-dir", help="The conversion second pass directory to store fines in. "\
            ## "Defaults to 'output_r' in the current directory.", default=p_join(cwd, "output_r"))
            "Defaults to 'output_r' in the current directory.", default="output_r")
    add_arg("--diff-dir", help="The directory to put the potential .diff files in. Defaults to " \
            ## "'cmp_output' in the current directory.", default=p_join(cwd, "cmp_output"))
            "'cmp_output' in the current directory.", default="cmp_output")
    add_arg("--debug", action="store_true", help="Print some debugging information.", default=False)
    args = arg_parser.parse_args()
    for key, val in dict(args._get_kwargs()).items():  # pylint: disable=protected-access
        setattr(opts, key, val)
    return opts


def create_dirs(*names):
    """Create directories for each name in 'names'.
    If a directory alerady exists, it is removed before being re-created.
    :names: strings: The names of the directories to create."""
    for name in names:
        if os.path.isdir(name):
            print "* Removing '%s'." % name
            shutil.rmtree(name)
        print "* Creating '%s'." % name
        os.mkdir(name)


def copy_files(pattern, src, dst):
    """Copy files corresponding to 'pattern' from 'src' directory to 'dst' one.
    :pattern: string: A usable pattern for glob.glob.
    :src: string: The directory to copy from.
    :dst: string: The directory to copy to. Must exists."""
    print "* Copying '%s' files from '%s' to '%s'." % (pattern, src, dst)
    names = _get_file_names(pattern, src)
    for name in names:
        shutil.copy2(name, dst)


def build_otis(plist_file, dat_dir, output_dir):
    """Builds '.oti' files using the 'build_otis.py' program.
    :plist_file: string: The path to the '.plist' file containing materials information.
    :dat_dir: string: The directory where the '.dat' files to scan are.
    :output_dir: string: the directory where to write the '.oti' files. Must exists."""
    if globals()['DEBUG']:
        print "% DEBUG: build_otis::"
        print "% plist_file:", plist_file
        print "% dat_dir:", dat_dir
        print "% output_dir:", output_dir
    oti_builder = importlib.import_module("build_otis")
    oti_builder.main(args=(plist_file, dat_dir, output_dir))


def convert_dat(src):
    """Converts '.dat' files by calling 'dat2obj.py'.
    :src: string: The directory where the '.dat' files are and where the '.obj' and '.mtl' ones will
        be written.
    Returns the number of files for which the conversion failed."""
    failures = 0
    for name in _get_file_names("*.dat", src):
        if globals()['DEBUG']:
            print "% DEBUG: convert_dat::"
            print "% src:", src
            print "% name:", name
        failures += min(1, os.system("python %s %s" % (os.path.join("..", "dat2obj.py"), name)))
    return failures


def convert_obj(src):
    """Convert '.obj' files using 'Obj2DatTex.py' or 'Obj2DatTexNorm.py'.
    The conversion program is automatically selected according the normals data contained in the
    '.obj' files.
    :src: string: The directory where the '.obj' files are.
    Returns the number of files for which the conversion failed."""
    failures = 0
    cwd = os.getcwd()
    sep = os.path.sep
    for name in _get_file_names("*.obj", src):
        if globals()['DEBUG']:
            print "% DEBUG: name (1):", name
        # We have to 'relativize' the file path, since Obj2DatTex.py calls 'lower()' method on the
        # file path, which is not compatible with case sensitive file systems...
        name = re.sub("^%s" % re.escape(r"%s%s" % (cwd, sep)), "", name)
        if globals()['DEBUG']:
            print "% DEBUG: name (2):", name
        prog = "Obj2DatTex.py"
        with open(name) as fin:
            if re.findall(r"^vn\s", fin.read(), re.M):
                prog = "Obj2DatTexNorm.py"
        # We need to convert Windows path separators to Unix for Obj2DatTex.py...
        if sys.platform == "win32" and prog == "Obj2DatTex.py":
            name = name.replace(os.sep, os.altsep)
        print "* Calling '%s'." % prog
        failures += min(1, os.system("python %s %s" % (os.path.join("..", prog), name)))
    return failures


def diff_files(left, right, output, pattern):
    """Find differences between to sets of files filtered using a pattern. Differences are saved in
    individual files.
    :left: string: The 'left' folder to get the first set of files.
    :right: string: The 'right' folder to get the second set of files.
    :output: string: The folder to write the '.diff' files in. Must exists.
    :pattern: string: A pattern compatible with glob.glob like '*.foo'."
    Returns the number of different files."""
    result = 0
    file_names = sorted(glob.glob(os.path.join(left, pattern)))

    print "* Comparing %s '%s' files." % (len(file_names), pattern)

    b_name = os.path.basename

    for file_name in file_names:
        right_name = os.path.join(right, b_name(file_name))
        diff = tuple(difflib.unified_diff(_get_data(file_name), _get_data(right_name),
                                          file_name, right_name))

        print "  * '%s' ('%s' | '%s')" % (b_name(file_name), b_name(left), b_name(right)),

        if diff:
            result += 1
            print "FAILED"
            # Write the diff to the output file.
            o_name = os.path.join(output, os.extsep.join((os.path.splitext(b_name(file_name))[0],
                                                          "diff")))
            with open(o_name, "w") as fout:
                fout.writelines(diff)
        else:
            print "OK"

    return result


def main():
    """Program bootstrap."""
    print "= Starting test_dat2obj.py"
    # -----------------
    # Build the options
    # Instanciate the options object
    opts = Options({})
    # Populate it with default values.
    init_options(opts)

    # Parse the command line and update opts accordingly.
    parse_cli(opts)
    if opts.debug:
        globals()['DEBUG'] = True
        print "% DEBUG: options"
        for key, value in opts.options.items():
            print "%% %s: %s" % (key, value)

    # -------------
    # Check pbPlist
    # If not found, it is automatically installed using a virtual environment.
    # If virtualenv is not found, it is 'installed' for the program only.
    ensure_pbplist(opts)

    # ----------------------
    # Start the test process

    # Create the directories.
    create_dirs(opts.left_dir, opts.right_dir, opts.diff_dir)

    # Copy the needed .dat files to left directory.
    copy_files("oolite*.dat", opts.models_dir, opts.left_dir)

    # Build .oti files.
    build_otis(opts.plist_file, opts.left_dir, opts.left_dir)

    # Convert .dat to . obj (1/2).
    fail_to_obj1 = convert_dat(opts.left_dir)
    if fail_to_obj1:
        print "Failed to convert %s '.dat' file to '.obj' ones (pass 1)." % fail_to_obj1

    # Convert back .obj files to .dat ones.
    fail_to_dat = convert_obj(opts.left_dir)
    if fail_to_obj1:
        print "Failed to convert %s '.obj' file to '.dat' ones." % fail_to_dat

    # Copy needed .dat and .oti files from left to right directory.
    copy_files("*.dat", opts.left_dir, opts.right_dir)
    copy_files("*.oti", opts.left_dir, opts.right_dir)

    # Convert new .dat files to .obj ones (2/2).
    fail_to_obj2 = convert_dat(opts.right_dir)
    if fail_to_obj1:
        print "Failed to convert %s '.dat' file to '.obj' ones (pass 2)." % fail_to_obj2

    if fail_to_obj1 != fail_to_obj2:
        print "Second dat2obj pass did not gave the same converted file number:"
        print "First: %s, second: %s." % (fail_to_obj1, fail_to_obj2)

    # Compare converted files.
    failed_diffs = diff_files(opts.left_dir, opts.right_dir, opts.diff_dir, "*.obj")
    if failed_diffs:
        print "Comparison did not pass for %s .obj files." % failed_diffs
        print "See '.diff' file in '%s'." % opts.diff_dir
        print "Test failed!"
    else:
        print "Tests successful!"


if __name__ == "__main__":
    main()
