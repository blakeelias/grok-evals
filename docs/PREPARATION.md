I want to set up a code skeleton so I'm ready to hit the ground running when I start the challenge, with a bunch of primitives that might help. This could include:
-a couple sample benchmarks/evals that could plausibly be included in the challenge (this could include code to download the dataset if there's a standard place to download these, or just some pre-generated data)
-code to run Grok on these benchmarks
-code to collate the total results in terms of accuracy
-code to generate a Markdown report of these accuracies in table-format.

[x] Let's have a discussion around the design of this codebase.
[x] What are some flaws or potential areas of improvement in this current code skeleton that would make it easier to keep the code organized and easily add new datasets or evaluation methods?
[x] Let's make/revise this skeleton together and make some design choices along the way.
        [x] Better interfaces overall (Benchmark, Evaluation, etc.)
        [x] Use structured outputs for letter choices, numbers, etc.
[ ] Let's implement the core API calling functionality.
        [ ] Since we'll be making many Grok requests, we might want to consider how to parallelize these for faster response.
            - E.g. is there any batch API that can allow us to submit many requests in a single HTTP request?
            - If that's not possible, perhaps just send multiple HTTP requests in parallel using multithreading or multiprocessing (like I did during the phone interview)?
            - Let's use [this example](https://docs.x.ai/docs/guides/async?utm_source=chatgpt.com) for asynchronous requests.
        [ ] The Grok API says there's a way to cache prompt tokens. We maybe want to turn this on. How do we do this?
            - (See this section of the docs: 
                  "Trying to run the same prompt multiple times? You can now use cached prompt tokens to incur less cost on repeated prompts. By reusing stored prompt data, you save on processing expenses for identical requests. Enable caching in your settings and start saving today! The caching is automatically enabled for all requests without user input. You can view the cached prompt token consumption in the "usage" object.")

[ ] Let's add an example dataset.
[ ] Let's implement the first step of evaluation: run Grok on all the items from the dataset and collect results.
        [ ] Depending on the type of task being evaluated, perhaps we want to use [Structured Outputs](https://docs.x.ai/docs/guides/structured-outputs) from the Grok API?
        [ ] We may want to run the model multiple times with different random seeds, or with nonzero temperature, to get different outputs and check how often the model is right. How should we best do this?
            - We could maybe use the list of completions here to include things other than the top completion?
            - Or should we always use completions[0] to get the top response, and just make multiple calls if we want to try again to check consistency in the model's outputs?
[ ] Let's implement the second step of evaluation: checking Grok's answers against the golden results, to get a per-item evaluation.
        [ ] Once again, it may be helpful to use [Structured Outputs](https://docs.x.ai/docs/guides/structured-outputs) e.g. if we want to have a judge model that outputs a binary answer as to whether the answer was correct/incorrect, or an enumeration as to which parts of a rubric were met, etc.
            - One such schema for such structured outputs from a judge model, see here: 
[ ] Let's implement the third step of evaluation: summary statistics on the per-item results (e.g. percentage right or wrong).
      [ ] Is there a way to add confidence intervals?
[ ] Let's implement per-item failure analysis.
[ ] Let's add reporting that translates the summary statistics to a markdown file.
