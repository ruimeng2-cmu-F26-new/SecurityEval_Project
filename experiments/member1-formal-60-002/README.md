# Member 1 Formal 60-Candidate Dataset

This directory contains the frozen output of the formal Claude generation run using
function-only prompts. The prompts preserve signatures and functional boundaries while
withholding security requirements, attack cases, and defensive implementation guidance.
The six pilot requests are excluded.

## Configuration

| Setting | Value |
|---|---|
| Provider | Anthropic Messages API |
| Models | `claude-haiku-5-5`, `claude-sonnet-5-5` |
| Tasks | `sql_delete_user`, `command_allowlist`, `path_read_file` |
| Independent runs | 10 per task-model combination |
| Total candidates | 60 |
| Thinking | Adaptive |
| Effort | Medium |
| Maximum output tokens | 16,000 |

## Recorded result

- 60 unique candidate IDs
- 60 `generated` records and 0 generation errors
- 30 candidates from each model
- 10 candidates for every task-model combination
- 10,640 input tokens and 40,740 output tokens
- Estimated API cost: USD 0.1491615 using the pricing metadata frozen in `manifest.json`
- All responses ended with `end_turn`
- 41 distinct code hashes across the 60 candidates
- Request, response, and code hashes were verified before this directory was committed

`generated` means only that the provider returned a normal response containing parseable
Python with the required entry point. It does not mean that a candidate is functionally
correct or secure. The candidates must still be evaluated by Bandit, custom AST rules,
and the restricted Docker test harness. No benchmark, detection, or repair result is
claimed by this dataset.

## Layout

`candidates.csv` is the human-readable index. `manifest.json` is the machine-readable
experiment manifest. Each candidate directory contains:

- `sample.json`: frozen task contract, including evaluation-only requirements
- `request.json`: exact provider request without credentials
- `response.json`: raw provider response
- `completion.txt`: extracted response text
- `code.py`: candidate source for Members 2 and 3
- `generation.json`: model, usage, cost, status, and hash record

API credentials were supplied through a temporary environment variable and are not
stored in this dataset.
