Release steps as done locally:

1. Run `rye run fix`, ensuring that all checks pass.
2. Bump version in `pyproject.toml`, either manually or using `rye version -b major|minor|patch`.
3. Use `git` to commit and push.
4. Run `rye run release`.
5. Tag the release in GitHub with the new version, also supplying release notes.
6. Run `git pull`, thereby obtaining the created tag.
7. Run `git tag --sort=version:refname | tail`, ensuring that the created tag is listed.