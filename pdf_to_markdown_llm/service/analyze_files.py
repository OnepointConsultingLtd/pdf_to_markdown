from collections import Counter
from pathlib import Path


def analyze_files(path: Path) -> Counter:
    counter = Counter()
    size_counter = Counter()
    for file in path.rglob("**/*.*"):
        if file.is_file():
            counter[file.suffix] += 1
            size_counter[file.suffix] += file.stat().st_size
    return counter, size_counter


def analyze_file_sizes(path: Path) -> Path:
    assert path.exists(), f"Path {path} does not exist"
    counter, size_counter = analyze_files(path)
    report = f"# {path.as_posix()}\n\n"
    for suffix, count in counter.most_common():
        report += f"{suffix}: {count} {size_counter[suffix] // (1024 * 1024)} MB\n"
    report_path = path / "file_sizes.md"
    report_path.write_text(report)
    return report_path
