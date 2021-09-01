# Releasing

- Use `bump2version`, available in the installed project dependencies, to update the version number. For example, to bump from v1.1.1 to the next patch version:

```shell
> bump2version patch                  # 1.1.1 -> 1.1.2-dev0
> bump2version --allow-dirty release  # 1.1.2-dev0 -> 1.1.2
```

- Confirm the version number update appears in the project files defined in `.bumpversion.cfg`.
- Update `CHANGELOG.md` with the changes since the last release.
- Commit changes, push, and open a release preparation pull request for review.
- Once the pull request is merged, fetch the updated `main` branch.
- Apply a tag for the new version on the merged commit: vX.Y.Z, for example v1.1.2.
- Push the new version tag up to the project repository to kick off build and artifact publishing to GitHub and PyPI.
