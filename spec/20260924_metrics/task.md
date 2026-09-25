# Background

Consider the `generate_media` function in `src/podgenai/podgenai.py` to be the outermost function of the application at this time. Consider the `get_completion` function in `src/podgenai/util/openai.py` to be the innermost function of the application. Calls emanate from `generate_media` and eventually reach `get_completion`. In between the two aforementioned functions, there exist several intermediate functions across various modules within the application.

The `get_completion` function creates a `metrics` object that is to be collected for a run triggered by the `generate_media` function. Many calls to `get_completion` are made during a run, and each call generates its own `metrics` object. The goal is to collect all these `metrics` objects and make them available in `generate_media` for further processing and reporting. Note that the metrics are token utilization metrics.

The intent is to capture the `metrics` objects using Python's `contextvars`. The underlying intent is to not have to pass around a `reporter` object explicitly through all intermediate functions.

# Task

Your task is to implement the `contextvars` based mechanism to:

1. Capture the `metrics` object created in `get_completion`.
2. Provision the list of captured `metrics` objects in the `generate_media` function. As a usage example, print each captured `metrics` object just below the duologue generation section, i.e. just above the final `match speakers:` line, in the `generate_media` function. Later I will remove the print, and I will implement the necessary transformations and reporting logic over these captured metrics.
3. Ensure that the mechanism works correctly even when there are multiple concurrent invocations of `generate_media`, each with its own set of `metrics` objects. Be careful when appending the metrics to a shared list, if any, as this may require locking, etc. for thread safety.
4. Use the `src/podgenai/util/contextvars.py` module for any reusable utility code related to `contextvars`. This module should be generic enough such that it can be reused in other projects with similar goals.
5. Ensure that the context propagation mechanism is compatible with concurrent execution of `generate_media`, such as when using intermediate `ThreadPoolExecutor` invocations, as is the case at multiple locations in `src/podgenai/content/subtopics.py`.
6. If `get_completion` is called outside of an active metrics-collection scope, then its `metrics` object should in effect not be captured and no error should be raised. This handling may be abstracted away within the `contextvars` utility module.
7. Run `poe check` after implementation to ensure that static analysis checks are passing.

# Remarks
    
1. There are no tests. None are required. Do not implement any tests.
2. Do not run the code. I will functionally test it myself.
3. Python 3.14 has some new features in its `contextvars` module that may simplify portions of the required implementation. For your reference, its documentation is attached (`spec/20260924_metrics/contextvars_doc_python3.14.txt`).
4. Speech generation in `src/podgenai/content/tts.py` does not matter for this purpose of token utilization metrics collection.