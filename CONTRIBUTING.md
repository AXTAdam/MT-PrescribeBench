# Contributing

Do not commit API keys, access tokens, provider endpoints, local absolute paths, private model outputs, or files from the manuscript workspace.

Before opening a pull request:

1. Run `python -m py_compile Code/score.py Code/Benchmark_Prompts.py`.
2. Validate workbook sheet names, row counts, and identifier uniqueness.
3. Scan tracked text and notebook files for secrets, URLs, model credentials, and local paths.
4. Describe any changed benchmark files and their validation results.
