Note: this will be moved to repo-tools at some point.

How to collect conventional commit stats:

#. Install requirements.txt into your current virtualenv.

#. Install repo-tools (https://github.com/edx/repo-tools) into your current
   virtualenv.

#. (if needed) Create a directory called "edx"

#. cd into edx.

#. Clone the edx org::

   $ clone_org edx

#. Update all the repos::

   $ gittree "git fetch --all; git checkout master; git pull"

#. cd ..; Run deptree.py::

   $ python deptree.py

#. Define your branch prefix, for example::

   $ export BRPREFIX=nedbat/

#. Remove previous metadata branches if any::

   $ gittreeif ${BRPREFIX}meta/installed git branch -D ${BRPREFIX}meta/installed

#. Add metadata branches to installed repos::

   $ while read repo; do echo $repo; git -C $repo branch ${BRPREFIX}meta/installed; done < installed.txt

#. Delete the existing commits.db file, if any.

#. Collect commit stats::

   $ gittreeif ${BRPREFIX}meta/installed python ${PWD}/commitstats.py ${PWD}/commits.db

#. Open CommitStats.ipynb and recalc all the cells to generate a graph.
