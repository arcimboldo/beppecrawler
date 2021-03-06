#!/usr/bin/env python
import glob
import os
import site
import sys

try:
    import settings
    # load virtualenv if set
    if settings.VIRTUALENV:
        for d in glob.glob(os.path.join(settings.VIRTUALENV, 'lib/python*/site-packages')):
            site.addsitedir(d)
except:
    # No `settings.py` file found.
    pass

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webgui.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
