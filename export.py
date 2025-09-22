import csv

def exportar_csv(filepath, dados):
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            for linha in dados:
                writer.writerow(linha)
        print(f"[OK] CSV exportado para {filepath}")
    except Exception as e:
        print(f"[ERRO] Falha ao exportar CSV: {e}")
