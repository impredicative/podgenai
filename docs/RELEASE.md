Release steps as done locally:

1. Bump version `pyproject.toml`.
2. Run `rye run release`.
3. Tag the release in GitHub, also supplying release notes.
4. Pull from remote, thereby obtaining the created tag.