#!/usr/bin/env bash
# in /src/ghorg, with a tmpenv made from the readme in edx-repo-health.
# 
# Real computed data is in /src/ghorg/edx/repo-health-data/dashboards/dashboard_main.csv

if [[ -z "$GITHUB_TOKEN" ]]; then
    echo 'Missing GitHub credentials: opvars github'
    exit 1
fi

WORKDIR=/tmp/checks
HERE=$(pwd)

if [[ -d "$WORKDIR" ]]; then
    source $WORKDIR/.venv/bin/activate
else
    mkdir -p $WORKDIR
    python3.8 -m venv --prompt checks $WORKDIR/.venv
    source $WORKDIR/.venv/bin/activate

    cd /ses/edx-repo-health
    make requirements
    python3 -m pip install -q -e .

    cd $HERE
fi

for y in */*/openedx.yaml; do
    repo=$(dirname $y)
    if [[ "$repo" == "openedx/edx-repo-health" ]]; then
        # checking edx-repo-health itself gets tangled up. Skip it.
        continue
    fi
    cd $repo
    vis=$(gh api 'repos/{owner}/{repo}' --template '{{.visibility}}')
    if [[ $vis == public ]]; then
        echo '== ' $repo
        # `-k readme` here will limit the checks run
        run_checks -q --no-cov --disable-warnings
        mkdir -p $WORKDIR/$repo
        mv repo_health.yaml $WORKDIR/$repo
        rm -f .coverage
    fi
    cd $HERE
done
