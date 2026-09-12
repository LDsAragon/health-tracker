"""Compara conteos de filas por tabla entre dos DBs (chequeo post-migración)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bitacora.database.conn import table_counts as counts


# Tras __main__ para que counts() se pueda importar (lo usa la migración a perfiles).
if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    ca, cb = counts(a), counts(b)
    print("iguales:", ca == cb)
    for t in sorted(set(ca) | set(cb)):
        if ca.get(t) != cb.get(t):
            print("DIF", t, os.path.basename(a), "=", ca.get(t), "|", os.path.basename(b), "=", cb.get(t))
    print(ca)
