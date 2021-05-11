import csv
import json
import pprint
import re

from pydantic import BaseModel, validator
import pytest

ORG = "edx"

# Helpers

def name_version_from_requirement(line):
    m = re.search(r"^(.*?)(?:\[.*\])?==(.*?)(?:;.*)?$", line)
    return m.groups()

@pytest.mark.parametrize("line, name_version", [
    ("django==2.2.20", ("django", "2.2.20")),
    ("opaque-keys[django]==1.2.3a4-dev", ("opaque-keys", "1.2.3a4-dev")),
    ("atomac==1.1.0; sys_platform == 'darwin'", ("atomac", "1.1.0")),
    ("futures==3.0.5; python_version < '3.0'", ("futures", "3.0.5")),
    ("futures==3.0.5; python_version == '2.6' or python_version=='2.7'", ("futures", "3.0.5")),
])
def test_name_version_from_requirement(line, name_version):
    assert name_version_from_requirement(line) == name_version

def repo_from_github_dependency(line):
    # git+https://github.com/edx/codejail.git@3.1.3#egg=codejail==3.1.3
    m = re.search(r"^git\+https://github\.com/(.*?/.*?)(?:\.git)?@.*$", line)
    if not m:
        print(f"BUH? {line}")
    return m[1]

@pytest.mark.parametrize("line, repo", [
    ("git+https://github.com/edx/codejail.git@3.1.3#egg=codejail==3.1.3", "edx/codejail"),
    ("git+https://github.com/edx/codejail.git@3.1.3#egg=codejail", "edx/codejail"),
    ("git+https://github.com/edx/codejail.git@3.1.3", "edx/codejail"),
    ("git+https://github.com/edx/codejail@3.1.3", "edx/codejail"),
])
def test_repo_from_github_dependency(line, repo):
    assert repo_from_github_dependency(line) == repo

# Convenient model for Repos

class Repo(BaseModel):
    repo_name: str
    openedx_yaml_release: str
    dependencies_github_list: list[str]
    dependencies_pypi_list: dict[str, str]
    dependencies_js_list: dict[str, str]
    setup_py_pypi_name: str
    npm_package: str
    github_is_private: bool
    github_is_archived: bool
    github_is_disabled: bool

    def __lt__(self, other):
        return self.repo_name < other.repo_name

    def __eq__(self, other):
        return self.repo_name == other.repo_name

    def __hash__(self):
        return hash(self.repo_name)

    @validator("dependencies_github_list", pre=True)
    def parse_dependencies_github_list(cls, val):
        if val: 
            return json.loads(val)
        else:
            return []

    @validator("dependencies_pypi_list", pre=True)
    def parse_dependencies_pypi_list(cls, val):
        deps = {}
        if val:
            for line in json.loads(val):
                m = re.search(r"^(.*?)(?:\[.*\])?==(.*)(?:;.*)?", line)
                deps[m[1]] = m[2]
        return deps

    @validator("dependencies_js_list", pre=True)
    def parse_dependencies_js_list(cls, val):
        deps = {}
        if val:
            deps = json.loads(val)
        return deps

    @validator("setup_py_pypi_name")
    def canonicalize_setup_py_pypi_name(cls, val):
        # A PyPI name could be listed as "edx_foo", but PyPI canonicalizes it
        # to "edx-foo".
        return val.replace("_", "-")

    @classmethod
    def from_csv(cls, d):
        return cls.parse_obj({re.sub(r"[.:]", "_", k): v for k, v in d.items()})


def main():
    with open("edx/repo-health-data/dashboards/dashboard_main.csv") as repos_csv:
        # The d["org_name"] check is because one row is completely empty:
        # https://openedx.atlassian.net/browse/ARCHBOM-1771
        raw_health = [d for d in csv.DictReader(repos_csv) if d["org_name"]]
        repo_health = [Repo.from_csv(d) for d in raw_health]

    with open("repo_health.json", "w") as health_out:
        json.dump(raw_health, health_out, indent=4)

    repos = {r.repo_name: r for r in repo_health}
    our_pypi = {pypi_name: r for r in repo_health if (pypi_name := r.setup_py_pypi_name)}
    our_npm = {npm_name: r for r in repo_health if (npm_name := r.npm_package)}

    print(f"{len(repos)} repos")
    print(f"{len(our_pypi)} pypi packages")
    print(f"{len(our_npm)} npm packages")

    mains = set()
    for repo in repos.values():
        release = repo.openedx_yaml_release
        if release:
            mains.add(repo)

    installed = set(mains)
    pypi_third_party = set()
    github_third_party = set()
    npm_third_party = set()
    print(f"{len(installed)} mains")

    last_len_installed = len(installed)
    while True:
        for repo in list(installed):
            for dep in repo.dependencies_pypi_list:
                if dep in our_pypi:
                    installed.add(our_pypi[dep])
                else:
                    pypi_third_party.add(dep)
            for ghdep in repo.dependencies_github_list:
                ghrepo = repo_from_github_dependency(ghdep)
                if ghrepo in repos:
                    installed.add(repos[ghrepo])
                else:
                    github_third_party.add(ghdep)
            for dep in repo.dependencies_js_list:
                if dep in our_npm:
                    installed.add(our_npm[dep])
                else:
                    npm_third_party.add(dep)
        if len(installed) == last_len_installed:
            break
        last_len_installed = len(installed)
    with open("installed.txt", "w") as f:
        print("\n".join(r.repo_name for r in sorted(installed)), file=f)
    print(f"{len(installed)} installed (in installed.txt)")
    # then:  while read repo; do echo $repo; git -C $repo branch nedbat/meta/installed; done < installed.txt

    print(f"{sum(1 for r in installed if r.github_is_private)} private repos installed")
    print(f"{sum(1 for r in installed if r.github_is_archived)} archived repos installed")
    print(f"{sum(1 for r in installed if r.github_is_disabled)} disabled repos installed")

    print()
    print("GitHub installed:")
    print("\n".join(sorted(github_third_party)))

    print()
    print(f"npm installed: {len(npm_third_party)} packages, including:")
    print("\n".join(sorted(p for p in npm_third_party if "edx" in p)))

    print()
    print(f"PyPI installed: {len(pypi_third_party)} packages, including:")
    print("\n".join(sorted(p for p in pypi_third_party if "edx" in p)))


if __name__ == "__main__":
    main()
