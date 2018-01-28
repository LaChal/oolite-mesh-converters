#!/usr/bin/python
#
# -*- coding: utf-8 -*-
#
# Dat2ObjTex_dcg.py v1.0.0
#
"""
dat2obj.py  by D.C.-G. (LaChal) 2018.
Originaly Dat2ObjTex.py by Giles Williams and Kaks.
This version supports multiple textures.

----------------------------- NOTES ON TEXTURES -----------------------------
Textures in .dat files can be referenced by their name or by index.
When an index is used, the texture pseudo-name can be found in the NAMES
section in the .dat file.
The first name in this section is index 0, the second one index 1, etc.
The names are the same as the entries names in the 'materials' object in the
.plist file which defines the Oolite object.

When real texture names are used, they can simply be added to the .mtl file.

When using indexed texture names, we need to know which texture name match
which index/pseudo-name, and which index/pseudo-name match which real name.
To do that, a simple text file named like the .dat, but with a .oti (Oolite
Texture Index) extension can be created alongside the .dat file to convert.
The format of this .oti file is very simple: one texture file name a line.
The first name will be the index 0 found in the .dat file, the second one
index 1, and so on.
"""
__authors__ = "(C) Giles Williams 2005 and Kaks 2008 / LaChal 2018."
__version__ = "1.0.0"

import os
import sys
import re
import pprint
from collections import OrderedDict


__prog_name__ = os.path.basename(__file__)

__help__ = """%s

Converts Oolite .dat files into Wavefromt .obj and .mtl ones.

%s <.dat_file_name_1> [[<.dat_file_name_2 [...]] [--debug]

-h --help       Print this screen and exits regardless other options.
   --debug      Writes output files.

When '--debug' is given, several dump files are witten and contain the program
internal data:
.fac    Faces.
.nor    Normals.
.sec    Sections data as found in .dat files.
.tex    Textures data.
.txm    Textures aliases/real names map.

""" % (__authors__, __prog_name__)


#-------------------------- OUTPUT FILES TEMPLATES ---------------------------
COMMON_HEADER = """# Exported with Dat2ObjTex.py (C) Giles Williams 2005 - Kaks 2008
# Revamped by D.C.-G. 2018."""

OBJ_TEMPLATE = """{header}
mtllib {mtl_lib_file}
o {obj_name}
# {n_verts} vertices, {n_faces} faces, {n_norms} normals
{vertex_lines}
{tex_lines}
{norms_lines}
{faces_lines}

"""

FACES_TEMPLATE = """g {obj_name}_{tex_name}
usemtl {tex_name}
{faces_lines}
"""

MATERIAL_TEMPLATE = """{header}
# Material number {mat_num}
{materials}
"""

MATERIAL_ENTRY_TEMPLATE = """newmtl {mtl_name}
Ns 100.000
d 1.00000
illum 2
Kd 1.00000 1.00000 1.00000
Ka 1.00000 1.00000 1.00000
Ks 1.00000 1.00000 1.00000
Ke 0.00000e+0 0.00000e+0 0.00000e+0
map_Kd {tex_file}

"""


#----------------------------- HELPER FUNCTIONS ------------------------------
def __exit(msg, code=0, std=sys.stdout):
    """Quit the program displaying 'msg' (or nothing) with exit code 'code'.
    Not intended to be used directly!
    :msg: string: Message to display. If an empty string is given, nothing is
        written to the output.
    :code: int: The exit code to send back to the system/program.
        Defaults to 0.
    :std: object: The 'std' file descriptor to wirte the message to.
        Defaults to sys.stdout.
        Valid values are sys.stdout and sys.stderr, or raise an IOError.
    Don't return anything...
    """
    if std not in (sys.stderr, sys.stdout):
        raise IOError("Bad output file descriptor '%s'." % std)
    if not msg.endswith(os.linesep):
        msg += os.linesep
    std.write(msg)
    sys.exit(code)


def _exit(msg):
    """Normal program termination. Calls '__exit' with 'msg' argument.
    :msg: string: Messagr to display.
    Exit code is always 0.
    Don't return anything...
    """
    __exit(msg)


def _error(msg, code=1):
    """Display '! ! ! ERROR:' followed by 'msg' then exit program with 'code'.
    :msg: string: Message to display.
    :code: int: Exit code to use when program exits.
        Defaults to 1.
    Don't return anything...
    """
    __exit("! ! ! ERROR: %s" % msg, code, sys.stderr)


def check_cli():
    """Reads sys.argvs and process arguments.
    Returns a tuple: (bool:debug_mode, list:input_file_names).
    """
    if "--help" in sys.argv or "-h" in sys.argv:
        _exit(__help__)
    debug = False
    if "--debug" in sys.argv:
        debug = True
        sys.argv.remove("--debug")
    input_file_names = sys.argv[1:]
    return debug, input_file_names


def split_line(line):
    """Splits a line on commas or blank characters.
    :line: string: The line to be split.
    Returns a list of strings."""
    if ',' in line:
        return [a.strip() for a in line.split(',')]
    else:
        return line.split()


def build_file_path(dir_name, file_name, ext):
    """Rebuilds a file path.
    :dir_name: string: The directory where the file lies.
    :file_name: string: The name of the file.
    :ext: string: Teh file extension.
    Return a string.
    """
    return os.path.join(dir_name, os.path.extsep.join((file_name, ext)))


def write_dump_file(dir_name, file_name, ext, datas):
    """Writes a dump file for debugging internal data.
    :dir_name, :file_name and :ext: See 'build_file_path' docstring.
    :datas: dictionary: Key are data names and values datas to be dumped.
    """
    f_name = build_file_path(dir_name, file_name, ext)
    with open(f_name, "w") as fd_out:
        fd_out.write("Dump file for %s" % file_name)
        for name, data in datas.items():
            fd_out.write("\n\n%s\n%s\n\n" % ("-" *80, name))
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, OrderedDict):
                        value = dict(value)
                    fd_out.write('"%s": %s\n' % (key, pprint.pformat(value,
                                                                     indent=4)
                                                                     ))
            else:
                fd_out.write(pprint.pformat(data, indent=4))


def _check_nentries(sections, num_def, dat_def):
    """Used by 'check_...' functions.
    :sections: dictionary:  The object send by 'get_sections' function.
    :num_def: string: The object in :section to get the number of entries.
    :dat_def: string: The name of the object in :sections to check the entries
        number in.
    """
    print "  * Checking %s" % num_def
    nentries = int(sections[num_def]["arguments"].split()[0])
    if nentries == len(sections[dat_def]["data"]):
        return True
    return False


def _parse_vn(lines, out_format):
    """Used to parse data which have same input shape and return same type of
    objects.
    :lines: list of string: Data to be parsed.
    :format: string: Format to be used to build the result.
    Returns a tuple:
    (int:number, list:lines_out)
    Used by parse_VERTEX and parse_NORMALS.
    """
    number = 0
    lines_out = []
    loa = lines_out.append
    for line in lines:
        coordinates = split_line(line)
        if len(coordinates) == 3:
            number += 1
            loa(out_format % (-float(coordinates[0]),
                              float(coordinates[1]),
                              float(coordinates[2])))
    return number, lines_out


def _get_tex_name(tex_map, idx, suffix="_auv"):
    """Returns a texture name built according to :tex_map data.
    :tex_map: dictionary: The texture map to search in.
    :idx: string: The index to search for in :tex_map.
    :suffix: string: the suffix to be added to the texture name.
        Defaults to '_auv'.
    If :idx is not found in :tex_map, a default name is built like this:
    'tex<idx><suffix>'.
    Returns the texture name as string.
    """
    return "%s%s" % (tex_map.get(idx, {}).get("alias", "tex%s" % idx), suffix)


#------------------------------ MAGIC FUNCTIONS ------------------------------
# These functions are called 'magically' and only if they exists.
def check_nverts(sections):
    """Verify if the number of lines in VERTEX section are exactly as
    defined in NVERS.
    :sections: dictionary: The object send by 'get_sections' function.
    """
    return _check_nentries(sections, "NVERTS", "VERTEX")


def check_nfaces(sections):
    """Verify if the number of lines in FACES section are exactly as
    defined in NFACES.
    :sections: dictionary: The object send by 'get_sections' function.
    """
    return _check_nentries(sections, "NFACES", "FACES")


def check_names(sections):
    """Verify the tesxure names length is as declared in NAMES.
    :sections: dictionary: The object send by 'get_sections' function.
    """
    return _check_nentries(sections, "NAMES", "NAMES")


#-------------------------- DATA PARSING FUNCTIONS ---------------------------
def parse_textures(lines):
    """Parses the TEXTUES data and new data to be used later and written in
    .obj file.
    :lines: list of strings: The TEXTURES lines as found in the .dat file.
    Returns a tuple:
    (dict:textures_references, list:.obj_file_textures)"""
    print "  * Parsing textures"

    def tex_index(tex, vts):
        """Returns the index of 'tex' in 'vts' or -1 if not found.
        :tex: string: Preformated string to be found.
        :vts: list of prformatted strings: Where to find 'tex'.
        Returns a signed int.
        """
        if tex in vts:
            return vts.index(tex)
        return -1

    tex_refs = {}
    named = OrderedDict()
    numbered = OrderedDict()
    vts = []
    vtsa = vts.append
    tex_lines_out = []
    tloa = tex_lines_out.append
    n_faces = 0
    for line in lines:
        # It may happen that some lines uses more than one tab to separate
        # values, so let's remove empty elements in the split result.
        tokens = filter(None, line.split("\t"))
        tex_name = tokens[0]
        if tex_name not in named.keys():
            named[tex_name] = {}
        if n_faces not in numbered.keys():
            numbered[n_faces] = {}
        tex_for_face = named[tex_name]
        points = tokens[2:]
        tff = []

        for point in points:
            v_data = point.split()
            vt_data = '%.6f %.6f' % (float(v_data[0]), 1 - float(v_data[1]))
            if vt_data not in vts:
                vtsa(vt_data)
                tloa("vt %s" % vt_data)
            tff[len(tff):] = [tex_index(vt_data, vts)]
        tex_for_face[n_faces] = tff
        numbered[n_faces] = tff, tex_name
        n_faces += 1
    tex_refs = {"named": named, "numbered": numbered}
    return tex_refs, tex_lines_out


def parse_vertex(lines):
    """Parses the VERTEX data and return new data to be written in .obj file.
    :lines: list of strings: The FACES lines as found in the .dat file.
    Returns a tuple:
    (int:number_of_vertex, list:.obj_file_vertex)"""
    print "  * Parsing vertex"
    return _parse_vn(lines, "v %.6f %.6f %.6f")


def parse_normals(lines):
    """Parses the NORMALS data and return new data to be written in .obj file.
    :lines: list of strings: The FACES lines as found in the .dat file.
    Returns a tuple:
    (int:number_of_normals, list:.obj_file_normals)"""
    print "  * Parsing normals"
    return _parse_vn(lines, "vn %.6f %.6f %.6f")


def parse_faces(lines, tex_for_face, n_normals):
    """Parses the FACES data and new data to be written in .obj file.
    :lines: list of strings: The FACES lines as found in the .dat file.
    :tex_for_face: dict: Contains texture information as parsed by
        'parse_textures'.
    :n_normals: int: The number of lines in NORMALS .dat file entry.
    Returns a tuple:
    (int:number_of_faces, dict:faces_groups)
    dict:faces_groups contains lists of lines to be written in the .obj file,
    according to the texture they belong to."""
    print "  * Parsing faces"

    def build_face_no_norm(p_d, f_i, *args):
        """Builds a 'face' without mormal reference.
        :p_d: int: Point data.
        :f_i: int: Face 'info'.
        Returns a string: '<:p_d + 1>/<:f_i + 1>/ '.
        """
        # *args are unused, don't keep them.
        del args
        return "%s/%s/ " % (p_d + 1, f_i + 1)

    def build_face_norm(p_d, f_i, n_i):
        """Builds a 'face' with mormal reference.
        :p_d: int: Point data.
        :f_i: int: Face 'info'.
        :n: int: The normal reference index.
        returs a string: '<:p_d + 1>/<:f_i + 1>/<n_i + 1> '.
        """
        return "%s/%s/%s " % (p_d + 1, f_i + 1, n_i + 1)

    build_face = build_face_no_norm
    if n_normals:
        build_face = build_face_norm

    n_faces = 0
    faces_groups = OrderedDict()

    tex_numbered = tex_for_face["numbered"]
    tex_named = tex_for_face["named"]
    for line in lines:
        tokens = split_line(line)
        if len(tokens) > 9:
            # color_data and normal_data are not (yet) used...
            # normal_data will be used to write 'vn' entries in the .obj file.
            ## color_data = tokens[0:3]
            ## normal_data = tokens[3:6]
            n_points = int(tokens[6])
            point_data = tokens[7:]
            faces = ""
            face_info = tex_numbered[n_faces]
            tex_name = face_info[-1]
            if tex_name not in faces_groups.keys():
                faces_groups[tex_name] = []

            # Verify the face data in also in the 'named' texture data.
            verif = tex_named.get(tex_name)
            err = ""
            if not verif:
                err = "Could not find name '%s' in references." % tex_name
            verif = verif.get(n_faces)
            if not verif:
                err = "Could not find index %s in references." % n_faces
            if err:
                raise KeyError(err)

            floa = faces_groups[tex_name].append
            f_i = face_info[0]
            for i in xrange(n_points):
                faces += build_face(int(point_data[i]), f_i[i], n_faces)
            floa("f %s" %faces)
            n_faces += 1

    return n_faces, faces_groups


def parse_names(lines, oti_file_name):
    """Parses the NAMES data.
    :lines: array of strings: The data to ba parsed.
    :oti_file_name: string: The .oti file to read texture file names from.
    Returns a dict like:
    {"line_index": "alias": "<texture_alias>", "name": "<texture_file_name>"}
    """
    print "  * Parsing names"
    # Read the real texture file names form the file.
    real_names = []
    if os.path.isfile(oti_file_name):
        with open(oti_file_name, "rU") as oti_fd:
            real_names = oti_fd.read().splitlines()

    names = {}
    for i, line in enumerate(lines):
        name = "."
        if i < len(real_names):
            name = real_names[i]
        names["%s" % i] = {"alias": line, "name": name}
    return names


#------------------------------ CORE FUNCTIONS -------------------------------
def get_sections(data):
    """Parses 'data' to get the sections defined in.
    :data: string: Raw .dat file content.
    Returns an OrderedDict like:
    {"SECTION_NAME": {"arguments": "what follows SECTION_NAME",
                      "data": [list of lines in section data]}}
    """
    print "  * Extracting sections"
    sections = OrderedDict()

    results = re.finditer(r"^([A-Z][A-Z]+)([ ]+.*)?$", data, re.M)
    data_start = None
    data_end = None
    prev_section = None
    cur_section = None
    for res in results:
        print "    * Found", res.groups()[0]
        data_end = res.start()
        if prev_section is not None:
            # Get rid of potential comments at the end of a line.
            _data = re.sub(r"\s*#.*", "", data[data_start:data_end])
            sections[prev_section]["data"] = filter(None, _data.splitlines())
        data_start = res.end()
        cur_section = res.groups()[0]
        sections[cur_section] = {"arguments": res.groups()[1], "data": ""}
        prev_section = "%s" % cur_section # Only to be sure we get a brand new string...

    return sections


def update_tex_map(tex_map, tex_keys):
    """Updates :tex_map with :tex_keys. Existing data in :tex_map is not
    changed.
    :tex_map: dictionary: Textures map to be updated.
    :tex_keys: list of strings: Keys to be added to :tex_map.
        Is considered is being a list of file names WITH its extension.
    Returns updated :tex_map.
    """
    for key in tex_keys:
        if key not in tex_map:
            tex_map[key] = {"alias": os.path.splitext(key)[0], "name": key}
    return tex_map


def write_obj(output_file_name, obj_name, mtl_lib_file, tex_lines,
              tex_map, n_verts, vertex_lines, n_normals,
              normals_lines, n_faces, faces_groups):
    """Builds the data and writes the .obj file.
    :output_file_name: string: File path to be written.
    :obj_name: string: The object name.
    :mtl_lib_file: string: The .mtl file name.
    :tex_lines: list of strings: The texture data.
    :tex_map: dictionary: Contains texture alias/name data.
    :n_verts: int: Number of vertex.
    :vertex_lines: list of string: The vertex data.
    :n_normals: int: Number of normals.
    :normals_lines: list of strings: Normals data.
    :n_faces: int: Number of faces.
    :faces_groups: dictionary: Faces data groupped by texture index.
    """

    def _join(lns):
        """Joins lines.
        :lns: list of strings: Lines to join.
        Returns joined lines as string.
        """
        return "\n".join(lns)

    # Rebuild the faces data first.
    faces = ""
    for idx, lines in faces_groups.items():
        # Get the texture 'alias' or use a default value
        tex_name = _get_tex_name(tex_map, idx)
        faces += FACES_TEMPLATE.format(obj_name=obj_name, tex_name=tex_name,
                                       faces_lines=_join(lines))

    # 'Apply' data to the template.
    with open(output_file_name, "w") as fd_out:
        fd_out.write(OBJ_TEMPLATE.format(header=COMMON_HEADER,
                                         mtl_lib_file=mtl_lib_file,
                                         obj_name=obj_name,
                                         n_verts=n_verts,
                                         n_faces=n_faces,
                                         n_norms=n_normals,
                                         vertex_lines=_join(vertex_lines),
                                         tex_lines=_join(tex_lines),
                                         norms_lines=_join(normals_lines),
                                         faces_lines=faces))
        print "  * Saved '%s'." % output_file_name


def write_mtl(output_file_name, tex_map):
    """Builds the data and writes the .mtl file.
    :output_file_name: string: File path to be written.
    :tex_map: dict: Texture map to find texture file names.
    """

    def _build_entry(_tex_map, _idx="0"): 
        """Builds a .mtl file entry.
        :_tex_map: dictionary: Map to look into.
        :_idx: string: The index to look for.
            Defaults to "0".
        Returns string data."""
        return MATERIAL_ENTRY_TEMPLATE.format(
            mtl_name=_get_tex_name(tex_map, _idx),
            tex_file=tex_map.get(_idx, {}).get("name", "."))

    materials = ""
    mat_num = len(tex_map)
    if mat_num:
        for idx in sorted(tex_map.keys()):
            materials += _build_entry(tex_map, idx)
    else:
        #Let define a default material when there's no map at all.
        materials += _build_entry(tex_map)

    with open(output_file_name, "w") as fd_out:
        fd_out.write(MATERIAL_TEMPLATE.format(header=COMMON_HEADER,
                                              mat_num=mat_num,
                                              materials=materials))
    print "  * Saved '%s'." % output_file_name


def main():
    """Main function of the program."""
    print "=" * 78
    print "%s %s" % (__prog_name__, __version__)
    debug, input_file_names = check_cli()
    if not input_file_names:
        _error("No input file name found!\n\n%s" % __help__)
    for input_file_name in input_file_names:
        print "* Reading", input_file_name
        file_base_name = os.path.splitext(os.path.basename(input_file_name))[0]
        file_dir_name = os.path.dirname(input_file_name)
        sections = {}
        tex_map = {}
        with open(input_file_name, 'rU') as in_fd:
            sections = get_sections(in_fd.read())

            if debug:
                write_dump_file(file_dir_name, file_base_name, "sec",
                                {"sections": sections})

            if not len(sections):
                _error("Nothing could be read from '%s'.\nIs this an Oolite .dat file?" % input_file_name)

        # Magically call the 'check' functions
        for name in sections.keys():
            f_name = "check_%s" % name.lower()
            if f_name in globals().keys():
                if not globals()[f_name](sections):
                    _error("Number of entries in '%s' section is different as declared!" % name)

        def get_data(name, sections=sections):
            """Returns the 'data' object from the 'name' one found in the
            'sections' one.
            :sections: dictionary: Object returned by 'get_sections'.
            :name: string: The name of the section to get the 'data'.
            Returns a list of 'lines'.
            """
            return sections.get(name, {}).get("data", [])

        oti_file_name = build_file_path(file_dir_name, file_base_name, "oti")
        tex_map = parse_names(get_data("NAMES"), oti_file_name)

        tex_refs, tex_lines_out = parse_textures(get_data("TEXTURES"))

        if debug:
            write_dump_file(file_dir_name, file_base_name, "tex",
                            {"tex_refs": tex_refs,
                             "tex_lines_out": tex_lines_out})

        # Update the tex_map object if textures indexes and names are both
        # used in 'TEXTURES'.
        if  sorted(tex_map.keys()) != sorted(tex_refs.get("named").keys()):
            tex_map = update_tex_map(tex_map,
                    set(tex_refs["named"].keys()).difference(tex_map.keys()))

        if debug:
            write_dump_file(file_dir_name, file_base_name, "txm",
                            {"tex_map": tex_map})

        n_verts, vertex_lines_out = parse_vertex(get_data("VERTEX"))

        if debug:
            write_dump_file(file_dir_name, file_base_name, "ver",
                            {"n_verts": n_verts,
                             "vertex_lines_out": vertex_lines_out})

        n_normals, normals_lines_out = parse_normals(get_data("NORMALS"))

        if debug:
            write_dump_file(file_dir_name, file_base_name, "nor",
                            {"n_normals": n_normals,
                             "normals_lines_out": normals_lines_out})

        n_faces, faces_groups = parse_faces(get_data("FACES"), tex_refs,
                                            normals_lines_out)

        if debug:
            write_dump_file(file_dir_name, file_base_name, "fac",
                            {"n_faces": n_faces,
                             "faces_groups": faces_groups})

        output_file_name = build_file_path(file_dir_name,
                                           file_base_name, 'obj').lower()
        material_file_name = build_file_path(file_dir_name,
                                             file_base_name, 'mtl').lower()
        mtl_lib_file = os.path.basename(material_file_name)

        write_obj(output_file_name, file_base_name, mtl_lib_file,
                  tex_lines_out, tex_map, n_verts, vertex_lines_out,
                  n_normals, normals_lines_out, n_faces, faces_groups)

        write_mtl(material_file_name, tex_map)

        _exit("* Done")


#--------------------------------- BOOTSTRAP ---------------------------------
if __name__ == '__main__':
    main()
