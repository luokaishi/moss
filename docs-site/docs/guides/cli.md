# CLI Reference

MOSS provides a comprehensive command-line interface for code analysis and refactoring.

## Global Options

```bash
moss [OPTIONS] COMMAND [ARGS]

Options:
  --version, -v    Show version and exit
  --help, -h       Show help message
```

## Commands

### analyze

Analyze code quality and generate reports.

```bash
moss analyze [PATH] [OPTIONS]
```

**Arguments:**
- `PATH` - Project path (default: current directory)

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--format, -f` | Output format: text, json, junit, github | text |
| `--output, -o` | Output file path | - |
| `--threshold` | Function line count threshold | 50 |
| `--complexity` | Cyclomatic complexity threshold | 10 |
| `--no-cache` | Disable caching | false |
| `--parallel, -p` | Number of parallel workers (0=auto) | 0 |
| `--fail-on-error` | Exit with error code if issues found | false |

**Examples:**

```bash
# Basic analysis
moss analyze ./src

# JSON output for CI/CD
moss analyze . --format json --output report.json

# GitHub Actions format
moss analyze . --format github --fail-on-error

# Strict analysis
moss analyze . --threshold 30 --complexity 8
```

### refactor

Execute refactoring operations.

```bash
moss refactor COMMAND [OPTIONS]
```

**Subcommands:**

#### move

Move symbol to another module.

```bash
moss refactor move --symbol MyClass --source module.a --target module.b [--dry-run]
```

#### extract

Extract selected code as function.

```bash
moss refactor extract --file main.py --start-line 10 --end-line 50 --name helper_function
```

#### imports

Organize and sort imports.

```bash
moss refactor imports --file main.py
```

### server

Start LSP server for IDE integration.

```bash
moss server [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | Transport mode: stdio, tcp | stdio |
| `--host` | TCP host address | 127.0.0.1 |
| `--port` | TCP port | 2087 |

**Examples:**

```bash
# Stdio mode (for VSCode)
moss server --mode stdio

# TCP mode
moss server --mode tcp --port 2087
```

### cache

Manage analysis cache.

```bash
moss cache COMMAND
```

**Subcommands:**

#### status

Show cache statistics.

```bash
moss cache status
```

Output:
```
MOSS 缓存状态:
  L1 缓存: 1250 条目
  L2 缓存: 5000 条目
  L3 缓存: 150 文件
  提升次数: 3200
  驱逐次数: 150
```

#### clear

Clear all cache.

```bash
moss cache clear
```

#### warm

Pre-populate cache by analyzing all files.

```bash
moss cache warm
```

### benchmark

Run performance benchmarks.

```bash
moss benchmark [PATH] [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--iterations` | Number of iterations | 3 |
| `--compare` | Compare serial vs parallel | false |

**Example:**

```bash
moss benchmark . --iterations 5 --compare
```

### init

Initialize MOSS configuration for a project.

```bash
moss init [PATH] [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing configuration |

**Example:**

```bash
moss init . --force
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Analysis found issues (with `--fail-on-error`) |
| 2 | Command error |
| 130 | Interrupted (Ctrl+C) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MOSS_CONFIG` | Path to custom config file |
| `MOSS_CACHE_DIR` | Cache directory path |
| `MOSS_LOG_LEVEL` | Log level: DEBUG, INFO, WARNING, ERROR |

## Configuration File

MOSS reads configuration from `.moss/config.json`:

```json
{
  "version": "9.3.0",
  "analysis": {
    "threshold": 50,
    "complexity_threshold": 10,
    "enable_incremental": true,
    "enable_parallel": true
  },
  "cache": {
    "l1_size": 1000,
    "l2_ttl": 3600
  }
}
```
