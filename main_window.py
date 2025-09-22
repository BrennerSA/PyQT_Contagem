from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from video_processor import VideoProcessor

class MainWindow(QMainWindow):
    def __init__(self, model_path, root_directory, line_x, dias_mes, sentido, sazonalidade, taxa):
        super().__init__()
        self.setWindowTitle("Sistema de Contagem de Veículos")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Inicializa processamento
        self.processor = VideoProcessor(
            model_path, root_directory, line_x, dias_mes, sentido, sazonalidade, taxa
        )

        aba_contagem = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Processamento de vídeo iniciado..."))
        aba_contagem.setLayout(layout)

        self.tabs.addTab(aba_contagem, "Contagem")
