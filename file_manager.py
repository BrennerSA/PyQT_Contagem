import os

def salvar_historico(filepath, dados):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(dados))
        print(f"[OK] Histórico salvo em {filepath}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar histórico: {e}")
