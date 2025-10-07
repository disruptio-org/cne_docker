import sys, pandas as pd

if len(sys.argv) < 3:
    print("Uso: python verify_against_reference.py <final_csv> <reference_csv>")
    sys.exit(1)

final_path, ref_path = sys.argv[1], sys.argv[2]
f = pd.read_csv(final_path, sep=";", dtype=str).fillna("")
r = pd.read_csv(ref_path, sep=";", dtype=str).fillna("")

key = ["DTMNFR","ORGAO","SIGLA","TIPO","NUM_ORDEM","NOME_CANDIDATO"]
for c in key:
    if c not in f.columns: f[c] = ""
    if c not in r.columns: r[c] = ""

fk = set(map(tuple, f[key].values))
rk = set(map(tuple, r[key].values))

missing = rk - fk
extra   = fk - rk

print("Linhas no final:", len(fk))
print("Linhas na referência:", len(rk))
print("Faltam (no final):", len(missing))
print("A mais (no final):", len(extra))

if missing or extra:
    import csv
    with open("missing_in_final.csv","w",newline="",encoding="utf-8") as out:
        w = csv.writer(out, delimiter=";")
        w.writerow(key); w.writerows(missing)
    with open("extra_in_final.csv","w",newline="",encoding="utf-8") as out:
        w = csv.writer(out, delimiter=";")
        w.writerow(key); w.writerows(extra)
    print("Gerados: missing_in_final.csv e extra_in_final.csv")
else:
    print("🎉 Chaves batem 100% com a referência.")
