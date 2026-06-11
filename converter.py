"""
Converte o app.py de latin-1 para UTF-8.
Coloque este script na mesma pasta do app.py e execute:
    python converter_encoding.py
"""
 
import os
import shutil
from pathlib import Path
 
INPUT_FILE  = "app.py"
BACKUP_FILE = "app.py.bak"
OUTPUT_FILE = "app.py"
 
def main():
    if not Path(INPUT_FILE).exists():
        print(f"❌ Arquivo '{INPUT_FILE}' não encontrado.")
        print("   Certifique-se de que este script está na mesma pasta do app.py")
        input("\nPressione Enter para fechar...")
        return
 
    # Faz backup antes de qualquer coisa
    shutil.copy2(INPUT_FILE, BACKUP_FILE)
    print(f"✅ Backup criado: {BACKUP_FILE}")
 
    # Lê o arquivo detectando o encoding
    content = None
    detected = None
 
    with open(INPUT_FILE, "rb") as f:
        raw = f.read()
 
    for enc in ("utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            content = raw.decode(enc)
            detected = enc
            break
        except Exception:
            continue
 
    if content is None:
        print("❌ Não foi possível detectar o encoding do arquivo.")
        input("\nPressione Enter para fechar...")
        return
 
    print(f"✅ Encoding detectado: {detected}")
 
    # Conta caracteres problemáticos antes
    problemas_antes = sum(1 for b in raw if b > 127)
    print(f"   Bytes não-ASCII encontrados: {problemas_antes}")
 
    # Salva em UTF-8
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
 
    # Verifica resultado
    with open(OUTPUT_FILE, "rb") as f:
        raw_novo = f.read()
 
    try:
        raw_novo.decode("utf-8")
        print(f"✅ app.py convertido para UTF-8 com sucesso!")
        print(f"   Tamanho original: {len(raw)} bytes")
        print(f"   Tamanho novo:     {len(raw_novo)} bytes")
        print(f"\n   Backup disponível em: {BACKUP_FILE}")
        print("   Agora envie o app.py convertido para o Mac.")
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        print(f"   Restaurando backup...")
        shutil.copy2(BACKUP_FILE, OUTPUT_FILE)
 
    input("\nPressione Enter para fechar...")
 
if __name__ == "__main__":
    main()
 