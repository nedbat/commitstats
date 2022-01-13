.PHONY: clones update collect plot help

.DEFAULT_GOAL := help

all: clones update collect plot		## Do everything to get latest data and plot it

clones:		## Fully clone our orgs
	cd edx; clone_org --prune --forks --no-archived edx
	cd openedx; clone_org --prune --forks --no-archived openedx
	cd archived/edx; clone_org --prune --archived-only edx
	cd archived/openedx; clone_org --prune --archived-only openedx
	cd edx-solutions; clone_org --prune --forks edx-solutions

update:		## Update all working trees
	. gittools.sh; gittree "git fetch --all --quiet; git checkout --quiet \$$(git remote show origin | awk '/HEAD branch/ {print \$$NF}'); git pull"

collect:	## Collect statistics
	rm commits.db
	conventional_commits collect --ignore='*-private' edx/* openedx/*

plot:		## Plot the weekly statistics
	conventional_commits plot

help:		## Show this help.
	@# Adapted from https://www.thapaliya.com/en/writings/well-documented-makefiles/
	@echo Available targets:
	@awk -F ':.*##' '/^[^: ]+:.*##/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^##@/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)
