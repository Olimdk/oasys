# Releasing OASYS

OASYS is installed with a one-line curl pipe installer that lives at the repo
root (install.sh). Every shipped version gets its OWN curl command, so users
can install or roll back to an exact release without guessing a ref.

## Install commands

Latest (rolling main):

    curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | bash

Specific version (self-pins to that release):

    curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/v0.2.0/install.sh | bash

Explicit override (optional - wins over the baked-in version):

    curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/main/install.sh | OASYS_REF=v0.2.0 bash

## How per-version installs work

The installer bakes a version into itself via a variable near the top:

    OASYS_VERSION="v0.2.0"   # empty string on main = rolling latest

At runtime it resolves the install target as:

    REF="${OASYS_REF:-${OASYS_VERSION}}"

So fetching v0.2.0/install.sh from GitHub always installs exactly v0.2.0, no
extra flags required. To confirm which version a fetched installer targets,
check the OASYS_VERSION line:

    curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/v0.2.0/install.sh | grep OASYS_VERSION=

## Cutting a new release

1. Bump the version in install.sh (set OASYS_VERSION to the new tag):

       sed -i 's/^OASYS_VERSION=.*/OASYS_VERSION="v0.3.0"/' install.sh

2. Commit and push:

       git add install.sh
       git commit -m "release: v0.3.0"
       git push origin main

3. Tag the release at that commit and push the tag:

       git tag -a v0.3.0 -m "OASYS v0.3.0"
       git push origin refs/tags/v0.3.0

4. Done. Users can now run:

       curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/v0.3.0/install.sh | bash

## Rolling back if a release breaks

Run the curl command for the known-good version, e.g.:

    curl -fsSL https://raw.githubusercontent.com/Olimdk/oasys/v0.2.0/install.sh | bash

The installer force-checks-out that ref and reinstalls the package into the
venv (pip install --force-reinstall --no-deps .), so the older code actually
takes effect. Your config/keys in ~/.oasys are never touched.

## Notes

- main must keep OASYS_VERSION="" (rolling latest). Only tagged releases bake
  a concrete version.
- Moving a published tag (e.g. fixing what a release points at) requires
  git push --force origin refs/tags/<tag> - do this only for your own repo and
  announce it, since it rewrites history for anyone who already fetched it.
