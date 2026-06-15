# Pre-commit
 
This repo uses [pre-commit](https://pre-commit.com) to run code formatting checks before every commit.
 
## Setup
 
Install dependencies and wire up the Git hook:
 
```bash
uv sync
uv run pre-commit install
```
 
Additionally if you want pre-commit to be available in your PATH:
```bash
uv tool install pre-commit
pre-commit install
```

Black will now run automatically on every `git commit`.
Check the [config](./.pre-commit-config.yaml) for extra details

## Running manually
 
```bash
# Run all hooks against changed files
uv run pre-commit run
 
# Run against all files in the repo
uv run pre-commit run --all-files
 
# Run only black
uv run pre-commit run black
```
 
## Bypassing a hook
 
In an emergency you can skip hooks entirely:
 
```bash
git commit --no-verify
```
 
Or skip a specific hook:
 
```bash
SKIP=black git commit
```
 
Use sparingly (CI will still catch any formatting issues).