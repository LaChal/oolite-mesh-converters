# Documentation for `dat2obj.py`

`dat2obj.py` is the heir of `Dat2Obj.py` and `Dat2ObjTex.py` and their replacer. It includes normals and multi-texture support.

To convert correctly multi-textured objects, you will have to use `.oti` files if a *NAMES* section exists in their `.dat` files.
See __What are `.oti` files?__, __How to write a `.oti` file?__ and __Feeling `.oti` lazy?__ sections.


## How to use it?

The usage of this program is very like than the former ones.  
Just call it with at least one `.dat` file, and it will create `.obj` and `.mtl` files.  
However, a `--help` and a `--debug` command line arguments have beed added.

On a Linux system (provided the file is executable), if you enter in the shell:

```
$ ./dat2obj.py -h
```

You'll get:

```
==============================================================================
dat2obj.py 1.0.0
(C) Giles Williams 2005 and Kaks 2008 / LaChal 2018.

Converts Oolite .dat files into Wavefromt .obj and .mtl ones.

dat2obj.py <.dat_file_name_1> [[<.dat_file_name_2 [...]] [--debug]

-h --help       Print this screen and exits regardless other options.
   --debug      Writes output files.

When '--debug' is given, several dump files are witten and contain the program
internal data:
.fac    Faces.
.nor    Normals.
.sec    Sections data as found in .dat files.
.tex    Textures data.
.txm    Textures aliases/real names map.

```

For named textures models, you'll need to create a `.oti` file before running `dat2obj.py` to have a correct `.mtl` file.  
See __What are `.oti` file?__ below.


## What `.dat` files is it able to convert?

This program shall be able to convert any Oolite `.dat` file.

However, some 'ill-formated' files (like `alloy.dat`, `buoy.dat` and `scarred_alloy.dat`) can't be converted.


## What are 'named' and 'indexed' textures?

'Named' textures are the ones which image file name is written in the *FACES* section in `.dat` files.  
'Indexed' textures are the ones which uses an alias in the *NAMES* section and are referenced by the alias number in the *FACES* section.

`dat2obj.py` is able to handle both, however, when 'indexed' textures ar used in `.dat` files, you'll need to have a corresponding `.oti` file.


## What are `.oti` files?

These files are used to store the real texture file names in the same order than in the *NAMES* section if the `.dat` file.  
They are simple raw text files containing one texture file name a line.

Without the corresponding `.oti` file, `dat2obj.py` will not be able to write the image file name for the textures in the `.mtl` file.


## How to write a `.oti` file?

Let's use an example: you want to convert `oolite_anaconda.dat`.

* First, create an empty text file named `oolite_anaconda.oti` alongside the `.dat` one. Be sure that the name ends with `.oti`, not something else!
* Then open `oolite_anaconda.dat` in a text editor, and search for *NAMES*.  
  Here, you have three names: *Engine*, *Gun* and *Hull*, in this order.
* Then, open `shipdata.plist` (or the `.plist` file in which the game object using this model is defined).  
  Look for the line `oolite_template_anaconda`. Insude this section, you'll find a `materials` object defined.  
  This section has objects defined with the same names than in the *NAMES* section in the `.dat` file.
* In the `.oti` file, write the file name defined by *diffuse_map* in the section named like the names we have in the `.dat` file.  
  Write these file names in the same order the names are in the `.dat` file!

The final `.oti` file will be:

```
oolite_anaconda_subents.png
oolite_anaconda_subents.png
oolite_anaconda_diffuse.png
```

## Feeling `.oti` lazy?

If you don't want to create yourself `.oti` files, you can try the `build_otis.py` Python program in the `test` directory.

This program requires two command line arguments:
* The path to the `.plist` file to get the texture file names from.
* The path to the directory where the `.dat` files you want to convert are.

All the `.dat` files found will be scanned, and corresponding `.oti` files created.
If a `.dat` file do not have a *NAMES* section, no corresponding `.oti` file is generated!

