# repo2notebook

[![PyPI version](https://badge.fury.io/py/repo2notebook.svg)](https://pypi.org/project/repo2notebook/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Convert any code repository into a single markdown file for [NotebookLM](https://notebooklm.google.com/) and other LLM tools.

**Problem:** NotebookLM doesn't accept `.tsx`, `.py`, `.cs`, or most code files. You have to manually copy-paste everything.

**Solution:** One command, one file. Upload and start chatting with your codebase.

## Installation

```bash
pip install repo2notebook
```

## Usage

```bash
# Run in your project directory
cd your-project
repo2notebook

# Or specify a path
repo2notebook /path/to/your/repo
```

**Output:** `_repo2notebook/notebook.md` — ready to upload to NotebookLM.

### Alternative: Run Without Installing

```bash
curl -O https://raw.githubusercontent.com/rvoidex7/repo2notebook/main/repo2notebook.py
python repo2notebook.py
```

## Features

- **Zero dependencies** — Only Python standard library
- **Single file** — Just `repo2notebook.py`, nothing else
- **All languages** — TypeScript, Python, Rust, Go, Kotlin, Swift, C#, and 50+ more
- **Smart filtering** — Automatically excludes `node_modules`, lock files, build outputs
- **Respects .gitignore** — Your ignore rules are honored
- **Safe** — Never modifies or deletes your original files
- **Auto-updates .gitignore** — Adds output folder to prevent committing

## What Gets Excluded

The tool automatically skips files that would add noise without value:

| Category | Examples |
|----------|----------|
| Dependencies | `node_modules/`, `vendor/`, `venv/`, `Pods/` |
| Lock files | `package-lock.json`, `yarn.lock`, `Cargo.lock`, `poetry.lock` |
| Build output | `dist/`, `build/`, `.next/`, `target/`, `bin/`, `obj/` |
| IDE config | `.idea/`, `.vscode/`, `.vs/` |
| OS files | `.DS_Store`, `Thumbs.db` |
| Secrets | `.env` (but `.env.example` is included) |

Plus everything in your `.gitignore`.

## Output Format

Clean markdown with proper syntax highlighting:

```markdown
# Repository: my-project

Generated: 2025-01-15 14:30
Total files: 42

---

## File: src/components/Button.tsx

​```typescript
import React from 'react';

export const Button = ({ label }) => {
  return <button>{label}</button>;
};
​```

---

## File: src/utils/api.py

​```python
def fetch_data(url: str) -> dict:
    ...
​```
```

## Requirements

- Python 3.9+

That's it. No `pip install`, no virtual environments.

## License

[MIT](LICENSE)

## Contributing

Issues and PRs welcome. Keep it simple.
