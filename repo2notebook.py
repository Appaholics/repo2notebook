#!/usr/bin/env python3
"""
repo2notebook - Convert any code repository to NotebookLM-compatible format

Usage:
    python repo2notebook.py              # Process current directory
    python repo2notebook.py /path/to/repo  # Process specific directory

Output: _repo2notebook/notebook.md

GitHub: https://github.com/rvoidex7/repo2notebook
License: MIT
"""

import os
import sys
import fnmatch
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_DIR = "_repo2notebook"
GITHUB_URL = "https://github.com/rvoidex7/repo2notebook"

# Always exclude (hardcoded, cannot override)
ALWAYS_EXCLUDE_DIRS = {
    ".git", ".svn", ".hg",                          # Version control
    "node_modules", "bower_components",              # JS
    "__pycache__", ".pytest_cache", ".mypy_cache",  # Python
    "venv", ".venv", "env", ".env",                 # Python virtualenv
    "dist", "build", "out", "_build",               # Build outputs
    ".next", ".nuxt", ".expo", ".turbo",            # JS frameworks
    "target",                                        # Rust, Java
    "bin", "obj", "Debug", "Release",               # C#/.NET
    "vendor",                                        # Go, PHP, Ruby
    "Pods", "DerivedData", ".build",                # iOS/Swift
    ".idea", ".vscode", ".vs", ".fleet",            # IDEs
    ".gradle", ".maven",                            # Java build tools
    OUTPUT_DIR,                                      # Our own output
}

ALWAYS_EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db", "desktop.ini",        # OS files
    ".env", ".env.local", ".env.production",        # Secrets (but .env.example OK)
}

ALWAYS_EXCLUDE_PATTERNS = [
    "*-lock.json",      # package-lock.json, etc.
    "*-lock.yaml",      # pnpm-lock.yaml
    "*.lock",           # Cargo.lock, poetry.lock, Gemfile.lock, composer.lock
    "*.log",
    "*.pyc",
    "*.pyo",
    "*.class",
    "*.dll",
    "*.exe",
    "*.so",
    "*.dylib",
    "*.o",
    "*.obj",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.chunk.js",
    "*.bundle.js",
]

# Extension to language mapping for markdown code blocks
EXT_TO_LANG = {
    # JavaScript/TypeScript
    ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    # Python
    ".py": "python", ".pyw": "python", ".pyi": "python",
    # Systems
    ".go": "go",
    ".rs": "rust",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
    # Mobile
    ".swift": "swift",
    ".kt": "kotlin", ".kts": "kotlin",
    ".java": "java",
    ".dart": "dart",
    # .NET
    ".cs": "csharp",
    ".fs": "fsharp",
    ".vb": "vb",
    # Web
    ".html": "html", ".htm": "html",
    ".css": "css",
    ".scss": "scss", ".sass": "sass", ".less": "less",
    ".vue": "vue",
    ".svelte": "svelte",
    # Data
    ".json": "json",
    ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".csv": "csv",
    # Shell
    ".sh": "bash", ".bash": "bash", ".zsh": "zsh",
    ".ps1": "powershell", ".psm1": "powershell",
    ".bat": "batch", ".cmd": "batch",
    # Other
    ".sql": "sql",
    ".graphql": "graphql", ".gql": "graphql",
    ".md": "markdown", ".markdown": "markdown",
    ".r": "r", ".R": "r",
    ".rb": "ruby",
    ".php": "php",
    ".pl": "perl", ".pm": "perl",
    ".lua": "lua",
    ".ex": "elixir", ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".scala": "scala",
    ".clj": "clojure",
    ".groovy": "groovy",
    ".tf": "terraform",
    ".dockerfile": "dockerfile",
    ".nginx": "nginx",
    ".proto": "protobuf",
}

# ============================================================================
# OUTPUT FILENAME
# ============================================================================

def get_output_filename(repo_path: Path) -> str:
    """Generate output filename from git remote or folder name."""
    
    # Try to get git remote URL
    git_config = repo_path / ".git" / "config"
    if git_config.exists():
        try:
            with open(git_config, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse remote URL (supports both https and ssh formats)
            import re
            
            # Match: url = https://github.com/owner/repo.git
            # Match: url = git@github.com:owner/repo.git
            patterns = [
                r'url\s*=\s*https?://([^/]+)/([^/]+)/([^/\s]+?)(?:\.git)?$',
                r'url\s*=\s*git@([^:]+):([^/]+)/([^/\s]+?)(?:\.git)?$',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    host = match.group(1).replace(".", "-")  # github.com -> github-com
                    owner = match.group(2)
                    repo = match.group(3)
                    return f"{host}-{owner}-{repo}.md"
        except Exception:
            pass
    
    # Fallback: use folder name
    return f"{repo_path.name}.md"


# ============================================================================
# GITIGNORE PARSER
# ============================================================================

def parse_gitignore(repo_path: Path) -> list[str]:
    """Parse .gitignore and return list of patterns."""
    gitignore_path = repo_path / ".gitignore"
    patterns = []
    
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception:
            pass
    
    return patterns


def matches_gitignore(path: str, patterns: list[str]) -> bool:
    """Check if path matches any gitignore pattern."""
    # Normalize path separators
    path = path.replace("\\", "/")
    
    for pattern in patterns:
        # Remove leading/trailing slashes for matching
        clean_pattern = pattern.strip("/")
        
        # Directory pattern (ends with /)
        if pattern.endswith("/"):
            if fnmatch.fnmatch(path, clean_pattern + "*") or \
               fnmatch.fnmatch(path, "*/" + clean_pattern + "*"):
                return True
        
        # File/directory pattern
        if fnmatch.fnmatch(path, clean_pattern) or \
           fnmatch.fnmatch(path, "*/" + clean_pattern) or \
           fnmatch.fnmatch(os.path.basename(path), clean_pattern):
            return True
    
    return False

# ============================================================================
# FILE FILTERING
# ============================================================================

def should_exclude_dir(dir_name: str) -> bool:
    """Check if directory should be excluded."""
    return dir_name in ALWAYS_EXCLUDE_DIRS or dir_name.startswith(".")


def should_exclude_file(file_name: str) -> bool:
    """Check if file should be excluded based on name/pattern."""
    # Exact match
    if file_name in ALWAYS_EXCLUDE_FILES:
        return True
    
    # Pattern match
    for pattern in ALWAYS_EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(file_name, pattern):
            return True
    
    # Hidden files (except some config files we want)
    if file_name.startswith(".") and file_name not in {".env.example", ".gitignore"}:
        return True
    
    return False


def is_text_file(file_path: Path) -> bool:
    """Check if file is likely a text file."""
    # Known text extensions
    text_extensions = set(EXT_TO_LANG.keys()) | {
        ".txt", ".rst", ".ini", ".cfg", ".conf", ".config",
        ".editorconfig", ".gitattributes", ".gitignore",
        ".prettierrc", ".eslintrc", ".babelrc",
        ".env.example", ".env.sample", ".env.template",
        ".htaccess", ".npmrc", ".yarnrc",
        "Makefile", "Dockerfile", "Containerfile",
        "Procfile", "Gemfile", "Rakefile",
        "CMakeLists.txt", "requirements.txt", "constraints.txt",
    }
    
    ext = file_path.suffix.lower()
    name = file_path.name
    
    if ext in text_extensions or name in text_extensions:
        return True
    
    # No extension - check if it's a known config file
    if not ext and name in {"Makefile", "Dockerfile", "Procfile", "Gemfile", "Rakefile"}:
        return True
    
    # Try to read first bytes to detect binary
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            # Binary files typically have null bytes
            if b"\x00" in chunk:
                return False
            return True
    except Exception:
        return False


def get_language(file_path: Path) -> str:
    """Get markdown language identifier for file."""
    ext = file_path.suffix.lower()
    name = file_path.name.lower()
    
    # Special files without extension
    if name == "dockerfile" or name == "containerfile":
        return "dockerfile"
    if name == "makefile":
        return "makefile"
    if name == "gemfile" or name == "rakefile":
        return "ruby"
    if name == "procfile":
        return "yaml"
    
    return EXT_TO_LANG.get(ext, "")

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def collect_files(repo_path: Path) -> list[Path]:
    """Collect all files to process."""
    gitignore_patterns = parse_gitignore(repo_path)
    files = []
    
    for root, dirs, filenames in os.walk(repo_path):
        # Filter directories in-place to prevent descending
        dirs[:] = [d for d in dirs if not should_exclude_dir(d)]
        
        rel_root = Path(root).relative_to(repo_path)
        
        for filename in filenames:
            # Skip excluded files
            if should_exclude_file(filename):
                continue
            
            file_path = Path(root) / filename
            rel_path = rel_root / filename if str(rel_root) != "." else Path(filename)
            
            # Skip gitignore matches
            if matches_gitignore(str(rel_path), gitignore_patterns):
                continue
            
            # Skip non-text files
            if not is_text_file(file_path):
                continue
            
            files.append(file_path)
    
    # Sort for consistent output
    files.sort(key=lambda p: str(p.relative_to(repo_path)).lower())
    return files


def read_file_content(file_path: Path) -> str | None:
    """Read file content, return None if failed."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            return None
    
    return None


def generate_markdown(repo_path: Path, files: list[Path]) -> str:
    """Generate markdown content from files."""
    repo_name = repo_path.name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"# Repository: {repo_name}",
        f"",
        f"Generated: {timestamp}",
        f"",
        f"Total files: {len(files)}",
        f"",
        f"---",
        f"",
    ]
    
    word_count = 0
    
    for file_path in files:
        rel_path = file_path.relative_to(repo_path)
        content = read_file_content(file_path)
        
        if content is None:
            continue
        
        language = get_language(file_path)
        
        lines.append(f"## File: {rel_path}")
        lines.append("")
        lines.append(f"```{language}")
        lines.append(content.rstrip())
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        word_count += len(content.split())
    
    return "\n".join(lines), word_count


def update_gitignore(repo_path: Path):
    """Add our output to .gitignore."""
    gitignore_path = repo_path / ".gitignore"
    marker = "# repo2notebook"
    entries_to_add = [
        "",
        marker,
        f"# {GITHUB_URL}",
        f"{OUTPUT_DIR}/",
        "repo2notebook.py",
    ]
    
    # Read existing content
    existing_content = ""
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception:
            pass
    
    # Check if already added
    if marker in existing_content:
        return False
    
    # Append our entries
    try:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n".join(entries_to_add))
            f.write("\n")
        return True
    except Exception:
        return False


def main():
    # Determine repo path
    if len(sys.argv) > 1:
        repo_path = Path(sys.argv[1]).resolve()
    else:
        repo_path = Path.cwd()
    
    # Validate
    if not repo_path.exists():
        print(f"Error: Path does not exist: {repo_path}")
        sys.exit(1)
    
    if not repo_path.is_dir():
        print(f"Error: Path is not a directory: {repo_path}")
        sys.exit(1)
    
    print(f"Processing: {repo_path}")
    print()
    
    # Collect files
    print("Scanning files...")
    files = collect_files(repo_path)
    print(f"Found {len(files)} files to include")
    print()
    
    if not files:
        print("No files found to process.")
        sys.exit(0)
    
    # Generate markdown
    print("Generating markdown...")
    content, word_count = generate_markdown(repo_path, files)
    print(f"Word count: {word_count:,}")
    print()
    
    # Create output directory
    output_dir = repo_path / OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    
    # Write output
    output_filename = get_output_filename(repo_path)
    output_path = output_dir / output_filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✓ Output: {output_path}")
    
    # Update .gitignore
    if update_gitignore(repo_path):
        print(f"✓ Updated .gitignore")
    
    print()
    print("Done! Upload the markdown file to NotebookLM.")


if __name__ == "__main__":
    main()
