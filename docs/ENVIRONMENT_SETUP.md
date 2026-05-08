# Environment Setup (Anaconda + uv)

This guide is for students who install Anaconda and want a reproducible local environment for this course while keeping `uv` as the package manager.

## 1) Install Prerequisites
- Install Anaconda from the official distribution.
- Ensure Conda is available in your terminal:

```bash
conda --version
```

- Install `uv` (if not installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your terminal and verify:

```bash
uv --version
```

## 2) Clone Repository

```bash
git clone https://github.com/hrodriguezgi/data_engineering_etl.git
cd data_engineering_etl
```

## 3) Create and Activate Conda Environment (Python 3.10)

```bash
conda create -n etl-course python=3.10 -y
conda activate etl-course
```

Verify interpreter:

```bash
python --version
```

## 4) Initialize and install Dependencies with uv

Preferred flow:

```bash
uv pip install -r requirements.txt
uv sync
```

If your machine has cache-permission issues:

```bash
UV_CACHE_DIR=.uv-cache uv sync
```

## 5) Validate Environment

Run tests:

```bash
uv run pytest -q
```

Optional import check:

```bash
uv run python -c "import pandas, requests, sqlalchemy, schedule; print('Environment OK')"
```

## 6) Daily Usage

From a new terminal session:

```bash
conda activate etl-course
cd /path/to/data_engineering_etl
```

Run scripts:

```bash
uv run python module_2_pandas/01_intro_to_pandas.py
```

Run tests:

```bash
uv run pytest -q
```

## Troubleshooting
- `conda: command not found`:
  - Reopen terminal or initialize shell with `conda init`, then restart terminal.
- `uv: command not found`:
  - Restart terminal after installation or add `uv` to your shell PATH.
- Permission errors under `~/.cache/uv`:
  - Use `UV_CACHE_DIR=.uv-cache` with `uv` commands.

