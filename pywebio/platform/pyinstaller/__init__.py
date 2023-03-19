import os


# Tell PyInstaller where to find hooks provided by this distribution;
# this is referenced by the :ref:`hook registration <hook_registration>`.
# This function returns a list containing only the path to this
# directory, which is the location of these hooks.
# # https://pyinstaller.readthedocs.io/en/stable/hooks.html

def get_hook_dirs():
    return [os.path.dirname(__file__)]
