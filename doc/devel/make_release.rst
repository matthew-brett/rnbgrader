###################
Releasing rnbgrader
###################

* Review the open list of `rnbgrader issues`_.  Check whether there are
  outstanding issues that can be closed, and whether there are any issues that
  should delay the release.  Label them.

* Review and update the release notes.  Review and update the :file:`Changelog`
  file.  Get a partial list of contributors with something like::

      git log 0.2.0.. | grep '^Author' | cut -d' ' -f 2- | sort | uniq

  where ``0.2.0`` was the last release tag name.

  Then manually go over ``git shortlog 0.2.0..`` to make sure the release notes
  are as complete as possible and that every contributor was recognized.

* Use the opportunity to update the ``.mailmap`` file if there are any
  duplicate authors listed from ``git shortlog -ns``.

* Check the copyright years in ``doc/conf.py`` and ``LICENSE``;

* Check `rnbgrader Github Actions results
  <https://github.com/matthew-brett/rnbgrader/actions>`_.

* Once everything looks good, set the release version.  Edit
  `rnbgrader/__init__.py` to set the version.

* Clean::

    # Check no files outside version control that you want to keep
    git status
    # Nuke
    git clean -fxd

* When ready::

    pip install build twine
    python -m build --sdist
    twine upload dist/rnbgrader*tar.gz

* Tag the release::

    git tag -s 0.3.5

* Update the version in `rnbgrader/__init__.py`.

* Upload the release commit and tag to github::

    git push
    git push --tags

* Push the docs to github pages with::

    cd doc
    make github

.. include:: ../links_names.inc
