Below are some helpful guidelines for extending this code.

This codebase uses a clean separation between the following components, each in their own directory:
 * datasets / dataloaders, evaluation logic for each benchmark
 * core API calls to the external model
 * results processing
 * results directory for both raw results and summaries.

The code gives a reproducible flow where one can re-run the same code and generate the same outputs, just having them overwritten.

If we want any new benchmark augmentation, we must add it to the set that gets run, rather than modifying any existing benchmarks (unless there's a mistake).

All functions should be well-documented Python code with type signatures and full documentation strings for each class, function and method, and in general follow Python best practices as well as [Google's Python Style Guide](https://google.github.io/styleguide/pyguide.html). Include extensive comments for any logic that's non-trivial, to explain what it's doing at the level of the evaluation logic and analysis itself (no need to document the low-level behavior of what specific Python constructs do, unless it helps understand the logic of the function).