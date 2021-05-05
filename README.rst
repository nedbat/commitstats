Note: this will be moved to repo-tools at some point.

How to collect conventional commit stats:

1. (First time) Create a directory called "edx"

1. cd into edx.

1. Install requirements.txt into your current virtualenv.

1. Install repo-tools (https://github.com/edx/repo-tools) into your current
   virtualenv.

1. Clone the edx org::

   $ clone_org

1. Update all the repos::

   $ gittree git fetch --all
   $ gittree git ma

1. cd ..; Run deptree.py::

   $ python deptree.py

1. Remove previous metadata branches if any:

   $ gittreeif nedbat/meta/installed git branch -D nedbat/meta/installed

1. Add metadata branches to install repos:

   $ while read repo; do echo $repo; git -C $repo branch nedbat/meta/installed; done < installed.txt

1. Delete the existing commits.db if any.

1. Collect commit stats:

   $ gittreeif nedbat/meta/installed python /src/ghorg/commitstats.py /src/ghorg/commits.db

1. Open CommitStats.ipynb and recalc all the cells to generate a graph.
