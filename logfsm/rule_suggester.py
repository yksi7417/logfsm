from collections import Counter
from .normalizer import normalize_line

def suggest_rules_from_lines(lines, top_n=20):
    freq = Counter()
    for line in lines:
        norm = normalize_line(line)
        freq[norm] += 1
    return freq.most_common(top_n)
