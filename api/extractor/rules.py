import re
from typing import List, Tuple

EFETIVOS_REGEX  = re.compile(r'Candidatos?\s+efe?etivos?:?', re.IGNORECASE)  # efetivos/efectivos
SUPLENTES_REGEX = re.compile(r'Candidatos?\s+suplentes?:?', re.IGNORECASE)

def normalize_whitespace(text: str) -> str:
    text = text.replace('\r', '')
    text = re.sub(r'[\t\u00A0]+', ' ', text)
    text = re.sub(r'\s+\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def clean_lines(t: str) -> List[str]:
    lines = []
    for l in t.splitlines():
        x = l.strip()
        x = re.sub(r'^\s*[\-–—•]*\s*', '', x)      # bullets
        # remove prefixos de numeração (1., 1), 1-, 1º, 1.º, 1° etc.)
        x = re.sub(r'^\s*\d+(?:\s*[\.\)\-º°]+)*\s*', '', x)
        x = x.strip(" -–—;:")
        if x and not x.lower().startswith("nota"):
            lines.append(x)
    return lines

def split_candidates_by_type(text: str) -> Tuple[List[str], List[str]]:
    efetivos, suplentes = [], []
    e = EFETIVOS_REGEX.search(text)
    s = SUPLENTES_REGEX.search(text)
    if e and s:
        if e.start() < s.start():
            efetivos_text = text[e.end():s.start()]
            suplentes_text = text[s.end():]
        else:
            suplentes_text = text[s.end():e.start()]
            efetivos_text = text[e.end():]
    elif e:
        efetivos_text = text[e.end():]
        suplentes_text = ""
    elif s:
        efetivos_text = ""
        suplentes_text = text[s.end():]
    else:
        efetivos_text = text
        suplentes_text = ""

    return clean_lines(efetivos_text), clean_lines(suplentes_text)
