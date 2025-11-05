import os
import sys
from platformdirs import user_data_dir


class Config:
    PATHFILE_EXPORT = PATHFILE = (
        sys._MEIPASS
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.realpath(__file__))
    )
    conda_prefix = os.environ.get("CONDA_PREFIX")
    lib = "Library" if sys.platform == "win32" else ""
    PROJ_LIB = (
        os.path.join(sys._MEIPASS, lib, "share/proj")
        if getattr(sys, "frozen", False)
        else os.path.join(conda_prefix, lib, "share/proj")
    )
    GDAL_DATA = (
        os.path.join(sys._MEIPASS, lib, "share/gdal")
        if getattr(sys, "frozen", False)
        else os.path.join(conda_prefix, lib, "share/gdal")
    )
    LOOKUP = "Jenette_Creek_Watershed/Database/lookup.db3"
    TEMPDIR = os.path.join(user_data_dir("Temp", False), "TempFiles")
    # BASE_DIR = "//int.ec.gc.ca/shares/M/MSC&ONT/Strategic Integration Office/GLHP/Nutrients/FEI_LakeErie_Streams/FEI_Databases/Databases"
    BASE_DIR = "C:\\Users\\viran\\Documents\\GitHub\\Nutri-View\\backend"