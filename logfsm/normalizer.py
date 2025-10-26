import re

TS_PATTERN = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+')
LONG_ID_PATTERN = re.compile(r'[A-Z0-9]{6,}')
NUM_PATTERN = re.compile(r'\d+(\.\d+)?')

def normalize_line(raw: str) -> str:
    line = TS_PATTERN.sub("<TS>", raw)
    line = LONG_ID_PATTERN.sub("<ID>", line)
    line = NUM_PATTERN.sub("<NUM>", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip().lower()

def extract_timestamp(raw: str) -> str:
    m = TS_PATTERN.search(raw)
    return m.group(0) if m else ""
