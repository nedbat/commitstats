.PHONY: clones check_forks update collect plot help

.DEFAULT_GOAL := help

all: latest collect plot						## Do everything to get latest data and plot it

latest: clones check_forks fix_private_remotes update			## Get all the latest repo contents

install:	## Get the code needed to run this stuff
	python -m pip install -e '/src/edx/src/repo-tools[conventional_commits,find_dependencies]'

init:		## Create the initial directory structure
	mkdir -p {,archived/,forks/}{edx,openedx}

check_env:
	@if [[ -z "$$GITHUB_TOKEN" ]]; then \
		echo 'Missing GITHUB_TOKEN: opvars github'; \
		exit 1; \
	fi

CLONE = clone_org --prune --ignore='*-ghsa-*-*-*'

clones: init check_env	## Fully clone our orgs
	cd edx; $(CLONE) --no-forks --no-archived edx
	cd openedx; $(CLONE) --no-forks --no-archived openedx
	cd archived/edx; $(CLONE) --archived-only edx
	cd archived/openedx; $(CLONE) --archived-only openedx
	cd forks/edx; $(CLONE) --forks-only --no-archived edx
	cd forks/openedx; $(CLONE) --forks-only --no-archived openedx

check_forks:
	python -c "import os;bad=set(os.listdir('forks/openedx'))&set(os.listdir('edx'));print('BAD: ', bad)if bad else ''"
	python -c "import os;bad=set(os.listdir('forks/edx'))&set(os.listdir('openedx'));print('BAD: ', bad)if bad else ''"

fix_private_remotes:
	. gittools.sh; gittree git fix-private-remotes

update:		## Update all working trees
	. gittools.sh; \
		gittree "git checkout --quiet \$$(git remote show origin | awk '/HEAD branch/ {print \$$NF}'); git pull --all" | \
		sed -e '/Already up to date./d'

collect:	## Collect statistics
	rm -f commits.db
	conventional_commits collect --ignore='*-private' edx/* openedx/*

plot:		## Plot the weekly statistics
	conventional_commits plot

help:		## Show this help.
	@# Adapted from https://www.thapaliya.com/en/writings/well-documented-makefiles/
	@echo Available targets:
	@awk -F ':.*##' '/^[^: ]+:.*##/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^##@/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)
