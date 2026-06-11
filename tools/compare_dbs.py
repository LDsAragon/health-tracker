"""Compara conteos de filas por tabla entre dos DBs (chequeo post-migración)."""
import os
import sqlite3
import sys


def counts(path):
    c = sqlite3.connect(path)
    tabs = [r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    out = {t: c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in sorted(tabs)}
    c.close()
    return out


a, b = sys.argv[1], sys.argv[2]
ca, cb = counts(a), counts(b)
print("iguales:", ca == cb)
for t in sorted(set(ca) | set(cb)):
    if ca.get(t) != cb.get(t):
        print("DIF", t, os.path.basename(a), "=", ca.get(t), "|", os.path.basename(b), "=", cb.get(t))
print(ca)
