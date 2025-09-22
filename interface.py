from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QInputDialog,
    QMessageBox, QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QFormLayout, QGroupBox
)

class Interface(QWidget):
    def __init__(self, start_callback):
        super().__init__()
        self.setWindowTitle("Configurações de Contagem")
        self.start_callback = start_callback
        self.setGeometry(100, 100, 400, 400)
        self.model_path = None
        self.line_x = 640
        self.link = "rtsp://100.70.73.128:8554/live"
        self.root_directory = ""
        self.dias_mes = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        grupo_modelo = QGroupBox("Modelo e Linha de Contagem")
        layout_modelo = QVBoxLayout()

        botao_modelo = QPushButton("Selecionar Modelo YOLO")
        botao_modelo.clicked.connect(self.selecionar_modelo)
        layout_modelo.addWidget(botao_modelo)

        botao_linha = QPushButton("Definir Linha de Contagem (X)")
        botao_linha.clicked.connect(self.definir_linha_x)
        layout_modelo.addWidget(botao_linha)

        grupo_modelo.setLayout(layout_modelo)
        layout.addWidget(grupo_modelo)

        grupo_config = QGroupBox("Configurações")
        layout_config = QFormLayout()

        self.sentido_combo = QComboBox()
        self.sentido_combo.addItems(["Esquerda", "Direita"])
        layout_config.addRow(QLabel("Sentido:"), self.sentido_combo)

        self.sazonalidade = QDoubleSpinBox()
        self.sazonalidade.setRange(0.0, 5.0)
        self.sazonalidade.setValue(1.0)
        layout_config.addRow(QLabel("Sazonalidade:"), self.sazonalidade)

        self.input_taxa = QLineEdit("3.0")
        layout_config.addRow(QLabel("Taxa Crescimento (%):"), self.input_taxa)

        grupo_config.setLayout(layout_config)
        layout.addWidget(grupo_config)

        botao_iniciar = QPushButton("Iniciar Contagem")
        botao_iniciar.clicked.connect(self.iniciar)
        layout.addWidget(botao_iniciar)

    def selecionar_modelo(self):
        modelo, _ = QFileDialog.getOpenFileName(self, "Selecionar Modelo YOLO", "", "Modelos (*.pt)")
        if modelo:
            self.model_path = modelo
            QMessageBox.information(self, "Modelo Selecionado", f"Modelo: {modelo}")

    def definir_linha_x(self):
        valor, ok = QInputDialog.getInt(self, "Linha", "Informe X:", value=self.line_x)
        if ok:
            self.line_x = valor

    def iniciar(self):
        if not self.model_path:
            QMessageBox.warning(self, "Erro", "Selecione o modelo primeiro.")
            return
        self.start_callback(
            self.model_path, self.root_directory, self.line_x,
            self.dias_mes, self.sentido_combo.currentText(),
            self.sazonalidade.value(), self.input_taxa.text()
        )
        self.close()
