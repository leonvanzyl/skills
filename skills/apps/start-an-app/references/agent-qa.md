# Browser-flow evidence with agent-qa

Last verified: 2026-10-25

Use this reference when the project already has agent-qa tests, or the user chose agent-qa for the browser checks in `verify.md`. [agent-qa](https://github.com/vostride/agent-qa) combines natural-language testing with advanced memidex memory and self-improvement. Use its run evidence to check the build sheet's promises, not to add new requirements.

## Bind the check to this app

- Find the initialized `agent-qa.config.yaml` and the selected test files. Match each test to a promised flow and inspect its expected outcome. Missing setup is a named unperformed check, not an instruction to install or initialize another tool.
- Resolve the test's target and confirm it points to the authorized app and environment. A run against another URL or revision does not prove this build works.
- Use the project's installed CLI and package manager. Check its Node.js requirement and installed help against the current [CLI documentation](https://vostride.com/docs/agent-qa/cli); do not pin a release in this reference. The npm examples below use `--no-install` to avoid downloading another version.
- Live runs need the configured browser and model provider. Keep application actions and provider costs within the agreed scope. If a server needs restarting after the gate, record which process you start and stop only that process when finished.
- Preserve the first-account rule in `verify.md`: the user becomes admin before any probe account exists. Use approved test accounts and data, keep payments in test mode, and track fixtures for cleanup. Never substitute the user's real records for disposable test data.

Run from the directory containing the configuration. A global `--config <path>` goes before the command.

```bash
npx --no-install agent-qa --version
npx --no-install agent-qa run --help
```

The version printed by the first command is output, not another subcommand. If an option has changed, use the documented equivalent and name the stale instruction at hand-off.

## Select, then execute

Replace `tests/main-flow.yaml` with the test selected for the build-sheet promise:

```bash
npx --no-install agent-qa validate tests/main-flow.yaml
npx --no-install agent-qa run tests/main-flow.yaml --dry-run
```

Validation checks structure; dry run checks selection. Neither exercises the app. Confirm the selected test IDs and target. An empty selection stays unverified; do not broaden it to every test.

Once execution is authorized, run the same selection. Choose a report path that preserves existing evidence:

```bash
npx --no-install agent-qa run tests/main-flow.yaml --junit-output results.xml
```

Keep the exit status and run ID. Verify that the report was actually created; a successful dry run does not produce proof of a JUnit report. `doctor` can contact the model provider, so it is not an offline substitute for validation.

## Read what happened

```bash
npx --no-install agent-qa runs list --json
npx --no-install agent-qa runs overview RUN_ID --json
npx --no-install agent-qa runs knowledge RUN_ID --json
```

Match `RUN_ID` to the selected flow, target, and app revision before interpreting it:

- Exit `0` can mean passed or healed. Read the verdict; explain any healing and check that the original expected outcome still holds.
- Exit `1` can mean a failed or timed-out test, or a missing required file. Distinguish a product defect from a setup failure. Exit `2` means execution could not start; exit `130` means cancellation.
- A run without a completed verdict, or knowledge marked `evidence-incomplete`, remains incomplete. An empty failed-only list does not prove success.
- The run's knowledge view shows what memidex supplied or learned. Use the [memory inspection guide](https://vostride.com/docs/agent-qa/memory/inspect) when a record needs investigation. Memory is diagnostic context, not independent proof that the build sheet is satisfied.

Keep the first failure and its evidence. Correct only a demonstrated issue within the agreed work, then rerun the affected selection. Never weaken an assertion, remove a promised feature, or erase memory to obtain a pass. Keep the parent workflow's two-round limit and report what remains.

## Hand evidence to the critics

Add the promised flow, selected test, target, command, exit, run ID, verdict, and available report paths to the existing evidence capture. Give critics the results, not browser access or this reference. Remove secrets and sensitive test data before sharing.

Keep untested flows and incomplete runs in the hand-off list. A passing selected flow does not cover every browser, provider, visual, ownership, or accessibility check. Clean up only the recorded fixtures, verify the user's account remains admin, and preserve the run evidence.

## Verify

- Each claimed result names the build-sheet promise and the run that checked it.
- Selection, execution, healing, and missing evidence are reported separately.
- The original gate and fresh-eyes review still run; no unperformed check becomes a pass.
- Test data and any server started for this check are cleaned up without changing the user's accounts or existing processes.
