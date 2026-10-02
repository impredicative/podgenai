# Tests

Install the development dependencies with `uv sync --locked`, then run the suite from the repository root:

```sh
pytest
```

Run one test module or select cases directly with pytest:

```sh
pytest tests/util/test_semantic_text_splitter.py
pytest -k byte_length_shortcut
```

Place new `test_*.py` modules under `tests/`, generally mirroring the corresponding directories under `src/podgenai/`. Pytest discovers these modules automatically. Keep fixtures in the test module until multiple modules need them; shared fixtures can then live in `conftest.py` in the appropriate directory.
