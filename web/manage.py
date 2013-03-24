#!/usr/bin/env python
import os
import site
import sys

try:
    import settings
    # load virtualenv if set
    if settings.VIRTUALENV:
        site.addsitedir(settings.VIRTUALENV)
except:
    # No `settings.py` file found.
    pass

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
