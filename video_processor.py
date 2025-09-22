from constants import CLASS_NAMES

class VideoProcessor:
    def __init__(self, model_path, root_directory, line_x, dias_mes, sentido, sazonalidade, taxa):
        self.model_path = model_path
        self.root_directory = root_directory
        self.line_x = line_x
        self.dias_mes = dias_mes
        self.sentido = sentido
        self.sazonalidade = sazonalidade
        self.taxa = taxa
        print(f"[INFO] Modelo: {self.model_path}")
        print(f"[INFO] Linha de contagem: {self.line_x}")
        print(f"[INFO] Sentido: {self.sentido}")
        print(f"[INFO] Taxa: {self.taxa}%")
        # TODO: carregar modelo YOLO + implementar tracking
