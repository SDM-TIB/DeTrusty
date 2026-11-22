# DeTrusty Documentation

The documentation is built using [Sphinx](https://www.sphinx-doc.org/en/master/).

## Prerequisites
* make
* Python packages listed in [../requirements-doc.txt](https://raw.githubusercontent.com/SDM-TIB/diefpy/master/requirements-doc.txt).

## Generating the Documentation
You can create a new version of the documentation by running:
```bash
make docs
```

This will generate the docs of **all versions** without any cached files. The new documentation will be available in `build/html`.

### Versioning
The docs are built with [sphinx-multiversion](https://holzhaus.github.io/sphinx-multiversion/) and contain one version per **minor series**, built from the **latest patch release** of that series (e.g., `v0.15.6` for all of 0.15.x).

Documentation exists from v0.12.2 on; older tags are skipped automatically.
Which tags are built is decided in `conf.py` (`_latest_patch_tags()`).
The newest release is additionally served at the stable URL `/latest/` (a copy that is refreshed on every build).
The root `index.html` and all former unversioned pages (e.g., `/changelog.html`) redirect to the same page below `/latest/`.
A version switcher is rendered by `_templates/versions.html`.

When a release is published, the `Deploy Docs` workflow rebuilds all versions and replaces the content of `gh-pages`.
Building locally needs the full git history including tags (`git fetch --tags`).

## Publishing the Documentation
In order to publish a new version (and building one before), run the following command:
```bash
make docs deploy
```

This will generate the docs and create a new commit on the `gh-pages` branch. GitHub will then deploy the new version automatically.