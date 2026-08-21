Release steps as done locally:

1. Run `poe fix`, ensuring that all checks pass.
2. Run `uv version` to check the version, then run `uv version --bump major|minor|patch` to bump the version.
3. Use `git` to commit and push.
4. Run `poe release`.
5. Run `poe changes` to list the commit messages since the last tagged release.
6. Tag the release in GitHub with the new version, also supplying release notes.
7. Run `git pull`, thereby obtaining the created tag.
8. Run `git tag --sort=version:refname | tail`, ensuring that the created tag is listed.