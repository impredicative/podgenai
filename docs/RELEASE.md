Release steps as done locally:

1. Bump version in `pyproject.toml`, either manually or using `rye version -b major|minor|patch`.
2. Use `git` to commit and push.
3. Run `rye run release`.
4. Tag the release in GitHub with the new version, also supplying release notes.
5. Run `git pull`, thereby obtaining the created tag.