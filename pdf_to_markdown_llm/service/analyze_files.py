from collections import Counter
import re
from datetime import datetime, timezone, timedelta
from PyPDF2 import PdfReader
from pathlib import Path
import zipfile
from lxml import etree 


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


def get_docx_creation_time(docx_path: Path) -> str | None:
    with zipfile.ZipFile(docx_path) as docx:
        try:
            core_xml = docx.read('docProps/core.xml')
        except KeyError:
            return None  # No core.xml found
        
    tree = etree.fromstring(core_xml)
    ns = {
        'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }

    created = tree.find('dcterms:created', namespaces=ns)
    return created.text if created is not None else None


def get_pdf_creation_time(path):
    reader = PdfReader(path)
    if not reader.metadata:
        return None
    raw_date = reader.metadata.get('/CreationDate')
    if raw_date and isinstance(raw_date, str):
        return parse_pdf_date(raw_date)
    return None


def parse_pdf_date(date_str: str):
    # Basic format: D:YYYYMMDDHHmmSSOHH'mm'
    match = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(Z|([+-])(\d{2})'?(\d{2})'?)?", date_str)
    if not match:
        return None
    
    year, month, day, hour, minute, second, zulu, sign, tz_hour, tz_minute = match.groups()
    dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))

    if zulu == 'Z':
        dt = dt.replace(tzinfo=timezone.utc)
    elif sign and tz_hour and tz_minute:
        offset = timedelta(hours=int(tz_hour), minutes=int(tz_minute))
        if sign == '-':
            offset = -offset
        dt = dt.replace(tzinfo=timezone(offset))
    else:
        dt = dt.replace(tzinfo=None)

    return dt.isoformat()


def analyze_file_timestamps(path: Path) -> list[tuple[Path, datetime]]:
    assert path.exists(), f"Path {path} does not exist"
    all_files_timestamps = []
    for p in path.rglob("**/*.*"):
        if p.is_file():
            timestamp = p.stat().st_mtime
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            iso_string = dt.isoformat()
            if p.suffix == ".docx":
                word_ts = get_docx_creation_time(p)
                if word_ts:
                    iso_string = word_ts
            elif p.suffix == ".pdf":
                pdf_ts = get_pdf_creation_time(p)
                if pdf_ts:
                    iso_string = pdf_ts
            all_files_timestamps.append((p, iso_string))
    return sorted(all_files_timestamps, key=lambda f: f[1], reverse=False)


def convert_to_timestamp(expression: str) -> str:
    return datetime.fromisoformat(expression.replace("Z", "+00:00"))

if __name__ == "__main__":
    import shutil
    output_path = "clustre_timestamps.txt"
    original_path = Path(__file__).parent.parent.parent / "docs/clustre"
    with open(output_path, "w") as f:
        for p, t in analyze_file_timestamps(original_path):
            f.write(f"{t} {p.as_posix()}\n")
    filtered_files = []
    with open(output_path, "r") as f:
        for l in f.readlines():
            year_str = l[:4]
            year = int(year_str)
            if year > 2019 and not l.strip().endswith(".md"):
                filtered_files.append(l)
    with open("clustre_filtered.txt", "w") as f:
        f.writelines(filtered_files)
    good_files_path = Path("clustre_filtered_files.txt")
    with open(good_files_path, "w", encoding="utf-8") as f:
        for l in filtered_files:
            f.write(l[l.find(" ") + 1:])
    # Copy the filtered files to the target path
    target_path = Path(__file__).parent.parent.parent / "docs/clustre_filtered"
    if not target_path.exists():
        target_path.mkdir(parents=True)
    filtered_files = good_files_path.read_text(encoding="utf-8").splitlines()
    for l in filtered_files:
        relative_path = Path(l).as_posix().replace(original_path.as_posix(), "")
        if relative_path.startswith("/"):
            relative_path = relative_path[1:]
        file_path = target_path / relative_path
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)
        shutil.copy(l, file_path)