Release steps as done locally:

1. Bump version in `pyproject.toml`, either manually or using `rye version -b major|minor|patch`.
2. Run `rye run release`.
3. Tag the release in GitHub with the new version, also supplying release notes.
4. Pull from remote, thereby obtaining the created tag.