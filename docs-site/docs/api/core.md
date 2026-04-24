# Core API

## PerformanceEngine

The main entry point for MOSS analysis and refactoring.

```python
from moss.core import PerformanceEngine, PerformanceConfig
```

### Constructor

```python
PerformanceEngine(
    codebase_path: Union[str, Path],
    config: Optional[PerformanceConfig] = None
)
```

**Parameters:**
- `codebase_path` - Path to the project root
- `config` - Performance configuration (optional)

### Methods

#### analyze_codebase

```python
async def analyze_codebase(
    file_paths: Optional[List[str]] = None,
    analysis_type: str = 'full',
    use_incremental: bool = True,
    use_parallel: bool = True
) -> AnalysisReport
```

Analyze the codebase with optimal strategy selection.

**Parameters:**
- `file_paths` - Specific files to analyze (None = all)
- `analysis_type` - Type of analysis: 'parse', 'analyze', 'metrics', 'full'
- `use_incremental` - Use incremental analysis
- `use_parallel` - Use parallel processing

**Returns:** `AnalysisReport` with results and statistics

**Example:**

```python
engine = PerformanceEngine("./src", config)
report = await engine.analyze_codebase()

print(f"Duration: {report.duration:.2f}s")
print(f"Cache hits: {report.cache_hits}/{report.file_count}")
print(f"Speedup: {report.parallel_speedup:.1f}x")
```

#### refactor_with_performance

```python
async def refactor_with_performance(
    symbol_name: str,
    source_module: str,
    target_module: str,
    dry_run: bool = False
) -> RefactoringResult
```

Execute refactoring with incremental impact analysis.

**Parameters:**
- `symbol_name` - Name of the symbol to move
- `source_module` - Source module path
- `target_module` - Target module path
- `dry_run` - Preview changes without applying

**Returns:** `RefactoringResult` with success status and modified files

#### run_performance_benchmark

```python
async def run_performance_benchmark() -> Dict
```

Run comprehensive performance benchmarks.

**Returns:** Dictionary with benchmark results

**Example:**

```python
results = await engine.run_performance_benchmark()
print(f"Parallel speedup: {results['parallel']['speedup']:.1f}x")
```

## PerformanceConfig

Configuration for performance optimization.

```python
from moss.core import PerformanceConfig

config = PerformanceConfig(
    enable_incremental=True,
    enable_parallel=True,
    max_workers=8,
    l1_cache_size=1000,
    l2_cache_ttl=3600
)
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_l1_cache` | bool | True | Enable memory cache |
| `enable_l2_cache` | bool | True | Enable SQLite cache |
| `enable_l3_cache` | bool | True | Enable JSON project cache |
| `l1_cache_size` | int | 1000 | L1 cache entries |
| `l2_cache_ttl` | int | 3600 | L2 cache TTL in seconds |
| `enable_parallel` | bool | True | Enable parallel processing |
| `max_workers` | Optional[int] | None | Number of workers (None = auto) |
| `target_speedup` | float | 10.0 | Target speedup ratio |

## IncrementalAnalyzer

Incremental analysis with change detection.

```python
from moss.core import IncrementalAnalyzer

analyzer = IncrementalAnalyzer("./src")
```

### Methods

#### analyze

```python
async def analyze(
    files: List[Path],
    analyzer_func: Callable,
    use_cache: bool = True
) -> Tuple[List[Any], Dict]
```

Analyze files incrementally.

**Returns:** (results, stats)

## ParallelAnalyzer

Parallel file analysis using process pools.

```python
from moss.core import ParallelAnalyzer

analyzer = ParallelAnalyzer(max_workers=8)
```

### Methods

#### analyze_files_parallel

```python
async def analyze_files_parallel(
    files: List[Tuple[str, str]],
    analysis_type: str = 'parse'
) -> ParallelResult
```

Analyze multiple files in parallel.

## MultiLevelCache

Three-tier caching system.

```python
from moss.core import MultiLevelCache

cache = MultiLevelCache("./src")

# Get from cache
result = cache.get("key")

# Set with auto-promotion
cache.set("key", value)

# Invalidate
cache.invalidate("key")
```

### Cache Levels

| Level | Storage | Latency | Persistence |
|-------|---------|---------|-------------|
| L1 | Memory (OrderedDict) | ~1μs | Process only |
| L2 | SQLite | ~1ms | Project-level |
| L3 | JSON files | ~10ms | Shareable |

## AnalysisReport

Report from code analysis.

```python
@dataclass
class AnalysisReport:
    file_count: int
    duration: float
    cache_hits: int
    cache_misses: int
    parallel_speedup: float
    issues_found: int
```

## Exceptions

### MossError

Base exception for MOSS errors.

### RefactoringError

Raised when refactoring fails.

### AnalysisError

Raised when analysis fails.
