import re
import os

with open("index.html", encoding="utf-8") as f:
    html = f.read()

sources = re.findall(r'(?:src|href)="([^"]+)"', html)
print("Verificando rutas locales en index.html:")
all_ok = True
for s in sources:
    if s.startswith(('http://', 'https://', '#', 'data:')):
        continue
    exists = os.path.exists(s)
    size = os.path.getsize(s) if exists else 0
    status = f"OK ({size/1024:.1f} KB)" if exists else "ERROR: NO EXISTE"
    if not exists:
        all_ok = False
    print(f"  {s:42} -> {status}")

if all_ok:
    print("\n[PERFECTO] Todos los recursos locales existen y son válidos.")
else:
    print("\n[ALERTA] Hay recursos faltantes.")
