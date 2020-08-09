import os
import cProfile
import pstats

import pylint.lint
from pylint_ignore.__main__ import main


for i in range(2):
    filename = 'profile_stats_%d.stats' % i
    if 1:
        args = [
            "--rcfile=setup.cfg",
            "--ignorefile=pylint-ignore.md",
            "metadata/",
        ]
        cProfile.run('main(args)', filename)
    else:
        args = [
            "--rcfile=setup.cfg",
            "metadata/",
        ]
        cProfile.run("pylint.lint.Run(args)", filename)

# Read all stats files into a single object
stats = pstats.Stats('profile_stats_0.stats')
for i in range(1, 2):
    stats.add('profile_stats_%d.stats' % i)

# stats.strip_dirs()

stats.sort_stats('tottime')
# stats.sort_stats('cumtime')
stats.print_stats()


# stats.print_callers("'get'")
# stats.print_callers("'format'")
# stats.print_callers("'join'")
