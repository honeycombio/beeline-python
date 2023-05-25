# Releasing

Use `poetry run bump2version --new-version <version> <semver` to update the version, including both the version number and semver type.
  (The `patch` is required for the command to execute but doesn't mean anything as you're supplying a full version).

  For example, to bump from v3.5.1 to the next patch version:

```sh
> poetry run bump2version --new-version 3.5.2 patch
```

- Confirm the version number update appears in `.bumpversion.cfg`, `pyproject.toml`, and `version.py`
- Update `CHANGELOG.md` with the changes since the last release. Consider automating with a command such as these two:
  - `git log $(git describe --tags --abbrev=0)..HEAD --no-merges --oneline > new-in-this-release.log`
  - `git log --pretty='%C(green)%d%Creset- %s | [%an](https://github.com/)'`
- Commit changes, push, and open a release preparation pull request for review.
- Once the pull request is merged, fetch the updated `main` branch.
- Apply a tag for the new version on the merged commit (e.g. `git tag -a v3.5.2 -m "v3.5.2"`)
- Push the tag upstream (this will kick off the release pipeline in CI) e.g. `git push origin v3.5.2`
- Ensure that there is a draft GitHub release created as part of CI publish steps (this will also publish to PyPi).
- Click "generate release notes" in GitHub for full changelog notes and any new contributors
- Publish the GitHub draft release
