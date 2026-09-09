"""Where the download formats derived from a UVL model live on disk.

A dataset's storage mirrors the folder structure of its UVL files::

    uploads/user_<uid>/dataset_<did>/uvl/<sub>/model.uvl
    uploads/user_<uid>/dataset_<did>/glencoe/<sub>/model.json
    uploads/user_<uid>/dataset_<did>/dimacs/<sub>/model.cnf
    uploads/user_<uid>/dataset_<did>/splot/<sub>/model.splx

``transform_uvl`` writes the derived files; this module names them so other
code (the ``formats:generate`` command, download zipping) can tell which are
missing without re-deriving that knowledge.
"""

import os

# format name -> file extension of the derived artifact
DERIVED_FORMATS = {
    "glencoe": ".json",
    "dimacs": ".cnf",
    "splot": ".splx",
}


def derived_format_path(uvl_path: str, fmt: str) -> str:
    """On-disk path of the ``fmt`` artifact derived from ``uvl_path``, keeping
    the folder the UVL lives in:
    ``.../dataset_N/uvl/<rel>/x.uvl`` -> ``.../dataset_N/<fmt>/<rel>/x.<ext>``."""
    marker = os.sep + "uvl" + os.sep
    if marker in uvl_path:
        base_dir, _, rel = uvl_path.partition(marker)
        rel_dir = os.path.dirname(rel)
    else:
        base_dir = os.path.dirname(os.path.dirname(uvl_path))
        rel_dir = ""

    name = os.path.basename(uvl_path)
    if name.endswith(".uvl"):
        name = name[:-4] + DERIVED_FORMATS[fmt]

    folder = os.path.join(base_dir, fmt, rel_dir) if rel_dir else os.path.join(base_dir, fmt)
    return os.path.join(folder, name)


def missing_derived_formats(uvl_path: str) -> list[str]:
    """Which derived formats have not been generated yet for this UVL file."""
    return [fmt for fmt in DERIVED_FORMATS if not os.path.isfile(derived_format_path(uvl_path, fmt))]
