# Releasing

1. Update version using `bump2version --new-version 1.12.0 patch` (NOTE: the `patch` is reqiured for the command to execute but doesn't mean anything as you're supplying a full version)
2. Add release entry to [changelog](./CHANGELOG.md)
3. Open a PR with the above, and merge that into main
4. Create new tag on merged commit with the new version (e.g. `git tag -a v2.3.1 -m "v2.3.1"`)
5. Push the tag upstream (this will kick off the release pipeline in CI) e.g. `git push origin v2.3.1`
6. Copy change log entry for newest version into draft GitHub release created as part of CI publish steps
   - generate release notes via github release draft for full changelog notes and any new contributors
