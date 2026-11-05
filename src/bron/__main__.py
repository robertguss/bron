"""`python -I -m bron`: the command line, runnable without the console script.

Commands that read downloaded scans are run this way, isolated from the working directory
and the environment, so nothing beside a download can shadow a module.
"""

import sys

from bron.cli import main

sys.exit(main())
