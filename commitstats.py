import contextlib
import datetime
import fnmatch
import os
import os.path
import re
import subprocess
import sys

import click
import dataset

def get_cmd_output(cmd):
    """Run a command in shell, and return the Unicode output."""
    try:
        data = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        data = ex.output
    try:
        data = data.decode("utf-8")
    except UnicodeDecodeError:
        data = data.decode("latin1")
    return data

def load_commits(db, repo_name):
    """Load the commits from the current directory repo."""

    SEP = "-=:=-=:=-=:=-=:=-=:=-=:=-=:=-"
    GITLOG = f"git log --no-merges --format='format:date: %aI%nhash: %H%nauth: %aE%nname: %aN%nsubj: %s%n%b%n{SEP}'"
    SHORT_LINES = 5

    # $ git log --format="format:---------------------%ndate: %aI%nhash: %H%nauth: %aE%nname: %aN%nsubj: %s%n%b"
    # ---------------------
    # date: 2021-04-21T16:13:23-04:00
    # hash: efa13ff1d2fb3d8b2ddee8be0868ae60f9bc35a6
    # auth: julia.eskew@edx.org
    # name: Julia Eskew
    # subj: fix: TNL-8233: Change exception raised at problem creation failure from generic exception to LoncapaProblemError. (#27361)
    # Raising this specific exception will cause the failure to be handled more gracefully by problem rescoring code.
    # ---------------------
    # date: 2021-04-15T21:36:47-04:00
    # hash: a1fe3d58dc112bd975f1237baaee787ba22929f1
    # auth: astaubin@edx.org
    # name: Albert (AJ) St. Aubin
    # subj: [bug] Corrected issue where program dash showed incorrect completed count
    # [MICROBA-1163]
    # 
    # This change will correct an issue in the Program Dashboard where a user
    # would see a course as completed, but not see their Certificate because
    # it was not available to them yet.
    # ---------------------

    with db:
        commit_table = db["commits"]

        log = get_cmd_output(GITLOG)
        for i, commit in enumerate(log.split(SEP + "\n")):
            if commit:
                lines = commit.split("\n", maxsplit=SHORT_LINES)
                row = {"repo": repo_name}
                for line in lines[:SHORT_LINES]:
                    key, val = line.split(": ", maxsplit=1)
                    row[key] = val
                row["body"] = lines[SHORT_LINES].strip()
                analyze_commit(row)
                commit_table.insert(row)

def analyze_commit(row):
    m = re.search(r"""(?x)
        ^
        (?P<label>build|chore|docs|feat|fix|perf|refactor|revert|style|test|temp)
        (?P<breaking>!?):\s
        (?P<subjtext>.+)
        $
        """, row["subj"]
    )
    row["conventional"] = bool(m)
    if m:
        row["label"] = m["label"]
        row["breaking"] = bool(m["breaking"])
        row["subjtext"] = m["subjtext"]
    row["bodylines"] = len(row["body"].splitlines())

@contextlib.contextmanager
def change_dir(new_dir):
    """Change directory, and then change back.

    Use as a context manager, it will give you the new directory, and later
    restore the old one.

    """
    old_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield os.getcwd()
    finally:
        os.chdir(old_dir)

@click.command(help="Collect stats about commits in local git repos")
@click.option("--db", "dbfile", default="commits.db", help="SQLite database file to write to")
@click.option("--ignore", multiple=True, help="Repos to ignore")
@click.option("--require", help="A file that must exist to process the repo")
@click.argument("repos", nargs=-1)
def main(dbfile, ignore, require, repos):
    db = dataset.connect("sqlite:///" + dbfile)
    for repo in repos:
        if any(fnmatch.fnmatch(repo, pat) for pat in ignore):
            print(f"Ignoring {repo}")
            continue
        if require is not None:
            if not os.path.exists(os.path.join(repo, require)):
                print(f"Skipping {repo}")
                continue
        print(repo)
        with change_dir(repo) as repo_dir:
            repo_name = "/".join(repo_dir.split("/")[-2:])
            load_commits(db, repo_name)

if __name__ == "__main__":
    main()

# then:
# gittreeif nedbat/meta/installed python /src/ghorg/commitstats.py /src/ghorg/commits.db
#
# in sqlite:
# select strftime("%Y%W", date, "weekday 0") as yw, count(*) total, sum(conventional) as con from commits group by yw;
# select yw, total, con, cast((con*100.0)/total as integer) pctcon from (select strftime("%Y%W", date, "weekday 0") as yw, count(*) total, sum(conventional) as con from commits group by yw);

"""
    select
    weekend, total, con, cast((con*100.0)/total as integer) pctcon, bod, cast((bod*100.0)/total as integer) pctbod
    from (
        select
        strftime("%Y%m%d", date, "weekday 0") as weekend,
        count(*) total,
        sum(conventional) as con, sum(bodylines > 0) as bod
        from commits where repo = "edx/edx-platform" group by weekend
    )
    where weekend > '202009';
"""
