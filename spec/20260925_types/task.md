# Background

I am using Python 3.14. My project's relevant code is in the `src/podgenai` directory.

My project already uses Python's type annotations, but perhaps they're not as tight as they can reasonably be.

# Task

1. Wherever sensible, tighten the Python type annotations in the `src/podgenai` codebase while keeping the annotations somewhat comprehensible. Avoid changing any runtime logic of the code.
2. You are free to add any necessary type definitions into `src/podgenai/types.py` or elsewhere, but only so long as they don't over-tighten the type annotations.
3. Ensure that `ty check` continues to pass as it does now.

# Exclusions

1. Take special care not to over-constrain the functions in `src/podgenai/util/openai.py`, as especially their forwarded keyword arguments are to remain open to SDK extensions.
2. Do not add low-value annotations in `src/podgenai/util/threading.py`, whether `print` related  or otherwise.

# Remarks

1. For your reference, I have provisioned the file `spec/20260925_types/typing_doc_python3.14.txt` as the official documentation for Python 3.14's typing features.
2. There are no tests. None are required. Do not implement any tests.
3. Do not run the code. I will functionally test it myself.

# Aftertask

Create a minimal agents file with these general points:

1. There are no tests. None are required. Do not implement any tests.
2. Do not run the code. I will functionally test it myself.
3. Run `poe check` to ensure that no new errors have been introduced.