Release steps as done locally:

1. Run `poe uv-version` and `poe uv-update` to ensure `uv` is up to date.
2. Run `poe fix` and `poe check`, ensuring that all checks pass.
3. Run `uv version` to check the version, then run `uv version --bump major|minor|patch` to bump the version.
4. Use `git` to commit and push.
5. Run `poe release`.
6. Run `poe changes` to list the commit messages since the last tagged release.
7. Tag the release in GitHub with the new version, also supplying release notes.
8. Run `git pull`, thereby obtaining the created tag.
9. Run `poe tags` to list git tags in reverse chronological order, ensuring that the created tag is listed.