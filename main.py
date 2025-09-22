from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QInputDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QTabWidget,QFormLayout,QComboBox,QGroupBox
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QLabel, QLineEdit
import sys
import os
import cv2
import numpy as np
from ultralytics import YOLO

CLASS_NAMES = {
    0: "Caminhao (2C)",
    1: "Caminhao Duplo Direcional Trucado (4C)",
    2: "Caminhao Trator + Semi Reboque (2S3)",
    3: "Caminhao Trator Trucado + Semi Reboque (3J3)",
    4: "Caminhao Trator Trucado + Semi Reboque (3J4)",
    5: "Caminhao Trator Trucado + Semi Reboque (3S3)",
    6: "Caminhao Trucado (3C)",
    7: "Onibus (2CB)",
    8: "Onibus Trucado (3CB)",
    9: "Bitrem Articulado (3D4)",
    10: "Caminhao Trator Trucado + Semi Reboque (3I3)"
}

class Interface(QWidget):
    def __init__(self, start_callback):
        super().__init__()
        self.setWindowTitle("Configurações de Contagem")
        self.start_callback = start_callback
        self.setGeometry(100, 100, 400, 400)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.line_x=640
        self.link="rtsp://100.70.73.128:8554/live"
        self.root_directory=""
        self.dias_mes=""

        # ---------- Grupo 1: Modelo e Linha ----------
        grupo_modelo_linha = QGroupBox("Modelo e Linha de Contagem")
        layout_modelo = QHBoxLayout()

        self.botao_modelo = QPushButton("Selecionar Modelo YOLO")
        self.botao_modelo.clicked.connect(self.selecionar_modelo)
        layout_modelo.addWidget(self.botao_modelo)

        self.botao_linha = QPushButton("Definir Linha de Contagem (X)")
        self.botao_linha.clicked.connect(self.definir_linha_x)
        layout_modelo.addWidget(self.botao_linha)

        grupo_modelo_linha.setLayout(layout_modelo)
        self.layout.addWidget(grupo_modelo_linha)

        # ---------- Grupo 2: Configurações ----------
        grupo_config = QGroupBox("Configurações")
        layout_config = QFormLayout()

        # Modo de Processamento
        self.botao_modo = QPushButton("Selecionar Modo")
        self.botao_modo.clicked.connect(self.definir_modo)
        layout_config.addRow(QLabel("Modo de Processamento:"), self.botao_modo)

        # Sentido
        self.sentido_combo = QComboBox()
        self.sentido_combo.addItems(["Esquerda", "Direita"])
        layout_config.addRow(QLabel("Sentido da Contagem:"), self.sentido_combo)

        # Sazonalidade
        self.sazonalidade = QDoubleSpinBox()
        self.sazonalidade.setRange(0.0, 5.0)
        self.sazonalidade.setSingleStep(0.1)
        self.sazonalidade.setValue(1.0)
        layout_config.addRow(QLabel("Fator de Sazonalidade:"), self.sazonalidade)

        # Taxa de Crescimento
        self.input_taxa = QLineEdit("3.0")
        layout_config.addRow(QLabel("Taxa de Crescimento (%):"), self.input_taxa)

        # Carga
        self.spin_carga = QDoubleSpinBox()
        self.spin_carga.setRange(0.0, 1000.0)
        self.spin_carga.setSingleStep(0.1)
        layout_config.addRow(QLabel("Carga Considerada (%):"), self.spin_carga)

        # Sobrecarga
        self.spin_sobrecarga = QDoubleSpinBox()
        self.spin_sobrecarga.setRange(0.0, 100.0)
        self.spin_sobrecarga.setSingleStep(1.0)
        layout_config.addRow(QLabel("Sobrecarga (%):"), self.spin_sobrecarga)

        grupo_config.setLayout(layout_config)
        self.layout.addWidget(grupo_config)

        # ---------- Botão Final ----------
        self.botao_iniciar = QPushButton("Iniciar Contagem")
        self.botao_iniciar.clicked.connect(self.iniciar)
        self.layout.addWidget(self.botao_iniciar)

        

    def selecionar_modelo(self):
        modelo, _ = QFileDialog.getOpenFileName(self, "Selecionar Modelo YOLO", "", "Modelos (*.pt)")
        if modelo:
            self.model_path = modelo
            QMessageBox.information(self, "Modelo Selecionado", f"Modelo: {modelo}")

    def selecionar_diretorio(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Vídeos")
        if pasta:
            self.root_directory = pasta
            QMessageBox.information(self, "Pasta Selecionada", f"Pasta: {pasta}")

    def definir_linha_x(self):
        valor, ok = QInputDialog.getInt(self, "Definir Linha de Contagem", "Informe a coordenada X:", value=self.line_x)
        if ok:
            self.line_x = valor

    def definir_link(self):
        link, ok = QInputDialog.getText(self, "Definir Link de Streaming", "Informe o link:")
        if ok and link:
            self.link = link
            QMessageBox.information(self, "Link Selecionado", f"Streaming: {link}")


    def definir_modo(self):
        opcoes = ["Selecionar uma pasta apenas", "Definir quantidade de dias", "Selecionar mês inteiro","Contagem por Streaming"]
        modo, ok = QInputDialog.getItem(self, "Modo de Processamento", "Escolha o modo:", opcoes, editable=False)
        if ok:
            self.modo = modo
            # Após selecionar o modo, chama automaticamente as funções conforme o modo
            if modo == "Selecionar uma pasta apenas":
                self.selecionar_diretorio()
            elif modo == "Definir quantidade de dias":
                self.selecionar_diretorio()
                self.definir_dias_mes()
            elif modo == "Selecionar mês inteiro":
                self.selecionar_diretorio()
            elif modo == "Contagem por Streaming":
                self.definir_link()

    def definir_dias_mes(self):
        valor, ok = QInputDialog.getInt(self, "Definir Dias", "Informe a quantidade de dias do mês:", min=1, max=31)
        if ok:
            self.dias_mes = valor
            domingo, ok2 = QInputDialog.getInt(self, "Domingo Inicial", "Informe o número do domingo do mês para iniciar (1 = primeiro domingo, 2 = segundo, etc):", min=1, max=5)
            if ok2:
                self.dia_domingo = domingo

    def iniciar(self):
        if not self.model_path:
            QMessageBox.warning(self, "Erro", "Defina o modelo e o diretório de vídeos primeiro.")
            return
        self.sentido_crescente = self.sentido_combo.currentText()
        self.fator_sazonalidade = self.sazonalidade.value()
        self.carga = self.spin_carga.value()
        self.sobrecarga = self.spin_sobrecarga.value()
        self.start_callback(self.model_path, self.root_directory, self.line_x, self.dias_mes, self.sentido_crescente, self.fator_sazonalidade,self.input_taxa)
        self.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rastreamento e Contagem de Veículos")
        # self.showMaximized()

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)

        from PyQt5.QtWidgets import QTabWidget
        from PyQt5.QtWidgets import QPushButton, QFileDialog, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QGroupBox

        self.tabs = QTabWidget()

        layout_principal = QHBoxLayout()
        layout_principal.addWidget(self.video_label, stretch=4)
        layout_principal.addWidget(self.tabs, stretch=2)

        self.btn_pausar = QPushButton("Pausar")
        self.btn_pausar.setFixedSize(150, 60)
        self.btn_pausar.clicked.connect(self.pausar_video)

        self.btn_parar = QPushButton("Parar")
        self.btn_parar.setFixedSize(150, 60)
        self.btn_parar.clicked.connect(self.parar_video)

        self.btn_exportar = QPushButton("Exportar CSV")
        self.btn_exportar.setFixedSize(150, 60)
        self.btn_exportar.clicked.connect(self.exportar_csv)

        # Criar layout de botões centralizados
        layout_botoes = QHBoxLayout()
        layout_botoes.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout_botoes.addWidget(self.btn_pausar)
        layout_botoes.addWidget(self.btn_parar)
        layout_botoes.addWidget(self.btn_exportar)
        layout_botoes.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Criar caixa com borda para os botões
        grupo_botoes = QGroupBox()
        grupo_botoes.setTitle("Controles")
        grupo_botoes.setMinimumHeight(80)
        grupo_botoes.setStyleSheet("QGroupBox { border: 2px solid gray; border-radius: 5px; margin-top: 10px; padding: 10px; }")
        grupo_botoes.setLayout(layout_botoes)

        # Criar aba de contagem global
        self.total_decrescente_global = {name: 0 for name in CLASS_NAMES.values()}
        self.total_crescente_global = {name: 0 for name in CLASS_NAMES.values()}
        self.tabela_global = QTableWidget()
        self.tabela_global.setFixedSize(408, 300)
        self.tabela_global.setColumnCount(3)
        self.tabela_global.setHorizontalHeaderLabels(["Classe", "Decrescente", "Crescente"])
        self.tabela_global.verticalHeader().setVisible(False)
        self.tabela_global.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_global.setRowCount(len(CLASS_NAMES))
        for i, nome_classe in enumerate(CLASS_NAMES.values()):
            self.tabela_global.setItem(i, 0, QTableWidgetItem(nome_classe))
            self.tabela_global.setItem(i, 1, QTableWidgetItem("0"))
            self.tabela_global.setItem(i, 2, QTableWidgetItem("0"))
        self.tabela_global.resizeColumnsToContents()
        self.tabela_global.resizeRowsToContents()

        aba_global = QWidget()
        layout_aba_global = QVBoxLayout()
        layout_aba_global.addWidget(self.tabela_global)
        aba_global.setLayout(layout_aba_global)
        self.tabs.insertTab(0, aba_global, "Contagem Global")

        # Adicione os botões a um layout vertical completo abaixo do layout principal
        layout_principal = QHBoxLayout()
        layout_principal.addWidget(self.video_label, stretch=4)
        layout_principal.addWidget(self.tabs, stretch=2)

        layout_completo = QVBoxLayout()
        layout_completo.addLayout(layout_principal)
        layout_completo.addWidget(grupo_botoes)
        container = QWidget()
        container.setLayout(layout_completo)
        self.setCentralWidget(container)


        # Variáveis de controle de execução
        self.video_paused = False
        self.video_stopped = False

        # container = QWidget()
        # container.setLayout(layout_principal)
        # self.setCentralWidget(container)

        self.config_window = Interface(self.iniciar_processamento)
        self.config_window.show()
        self.hide()

    
    def salvar_tabela_txt(self):
        try:
            historico_txt = os.path.join(self.historico_dir, "contagem_global.txt")
            with open(historico_txt, 'w', encoding='utf-8') as f:
                f.write("Classe	Decrescente	Crescente")
                for i in range(self.tabela_global.rowCount()):
                    classe = self.tabela_global.item(i, 0).text()
                    decrescente = self.tabela_global.item(i, 1).text()
                    crescente = self.tabela_global.item(i, 2).text()
                    f.write(f"{classe}	{decrescente}	{crescente}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar TXT", str(e))

    
    def pausar_video(self):
        self.video_paused = not self.video_paused
        self.btn_pausar.setText("Continuar" if self.video_paused else "Pausar")

    def parar_video(self):
        self.video_stopped = True
        QMessageBox.information(self, "Processamento Interrompido", "Execução do vídeo interrompida pelo usuário.")

    def exportar_csv(self):
        """
        Gera um PDF com o Número N projetado para os próximos 10 anos,
        considerando crescimento composto de 3%/ano sobre o VMD ajustado
        por sazonalidade. Exibe N anual e N acumulado (ano a ano) por sentido.
        Não soma sentidos entre si.
        """
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from reportlab.pdfgen import canvas

        # --- Parâmetros de projeção ---
        try:
            taxa_crescimento = float(self.taxa.text()) / 100 # converte para decimal
        except ValueError:
            taxa_crescimento = 0.03  # fallback padrão (3%)
        horizonte_anos = 10
        fator_direcional = 1       # metade do tráfego por faixa usada na fórmula

        # --- Fatores de equivalência por classe (FE) ---
        LIMITE_EIXOS = {
            "SRS": 6,
            "SRD": 10,
            "TD" : 17,
            "TT" : 25.5
        }

        LIMITE_EIXOS_SOBRECARGA = {
            eixo: valor * (1+fator_sobrecarga)
            for eixo, valor in LIMITE_EIXOS.items()
        }

        LIMITE_EIXOS_SOBRECARGA_AASTHO = {
            eixo: valor * (1+fator_sobrecarga)
            for eixo, valor in LIMITE_EIXOS_SOBRECARGA.items()
        }
        
        
        FATORES_EQUIVALENCIA = {
            "Caminhao (2C)": 2.7218,
            "Caminhao Duplo Direcional Trucado (4C)": 2.2971,
            "Caminhao Trator + Semi Reboque (2S3)": 4.2817,
            "Caminhao Trator Trucado + Semi Reboque (3J3)": 6.0065,
            "Caminhao Trator Trucado + Semi Reboque (3J4)": 6.5,
            "Caminhao Trator Trucado + Semi Reboque (3S3)": 3.5296,
            "Caminhao Trucado (3C)": 1.9697,
            "Onibus (2CB)": 2.7218,
            "Onibus Trucado (3CB)": 1.9697,
            "Bitrem Articulado (3D4)": 5.2545,
            "Caminhao Trator Trucado + Semi Reboque (3I3)": 9.153
        }

        # Seleciona destino
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "numero_N_10anos.pdf", "PDF Files (*.pdf)")
        if not caminho:
            return

        try:
            # --- Totais observados por sentido ---
            total_dec = sum(self.total_decrescente_global.get(c, 0) for c in CLASS_NAMES.values())
            total_cre = sum(self.total_crescente_global.get(c, 0)   for c in CLASS_NAMES.values())

            if total_dec <= 0 and total_cre <= 0:
                QMessageBox.warning(self, "Sem dados", "Não há contagens para calcular o Número N.")
                return

            # --- Fator de sazonalidade ---
            fator_saz = getattr(self, "fator_sazonalide", 1.0) or 1.0  # fallback
            VMD_dec_base = total_dec / fator_saz
            VMD_cre_base = total_cre / fator_saz

            # --- Percentuais por classe ---
            perc_dec = {}
            perc_cre = {}
            for nome_classe in CLASS_NAMES.values():
                dec = self.total_decrescente_global.get(nome_classe, 0)
                cre = self.total_crescente_global.get(nome_classe, 0)
                perc_dec[nome_classe] = (dec / total_dec) if total_dec > 0 else 0.0
                perc_cre[nome_classe] = (cre / total_cre) if total_cre > 0 else 0.0

            # --- Listas de resultados ---
            anos = list(range(1, horizonte_anos + 1))
            N_dec_ano = []
            N_cre_ano = []
            N_dec_acum = []
            N_cre_acum = []

            soma_dec = 0.0
            soma_cre = 0.0

            for ano in anos:
                fator_cresc = (1.0 + taxa_crescimento) ** ano
                VMD_dec_ano = VMD_dec_base * fator_cresc
                VMD_cre_ano = VMD_cre_base * fator_cresc

                # N por sentido no ano = soma das classes
                n_dec = 0.0
                n_cre = 0.0
                for nome_classe in CLASS_NAMES.values():
                    fe = FATORES_EQUIVALENCIA.get(nome_classe, 1.0)
                    n_dec += 365 * VMD_dec_ano * perc_dec[nome_classe] * fe * fator_direcional
                    n_cre += 365 * VMD_cre_ano * perc_cre[nome_classe] * fe * fator_direcional

                N_dec_ano.append(n_dec)
                N_cre_ano.append(n_cre)

                soma_dec += n_dec
                soma_cre += n_cre
                N_dec_acum.append(soma_dec)
                N_cre_acum.append(soma_cre)

            # --- PDF ---
            pdf = canvas.Canvas(caminho)
            y = 800
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y, "Número N Projetado (10 anos, 3%/ano)")
            y -= 25
            pdf.setFont("Helvetica", 11)
            pdf.drawString(50, y, f"Fator de sazonalidade: {fator_saz}")
            y -= 15
            pdf.drawString(50, y, f"VMD base decrescente: {VMD_dec_base:.2f}")
            y -= 15
            pdf.drawString(50, y, f"VMD base crescente: {VMD_cre_base:.2f}")
            y -= 25

            # Cabeçalho tabela
            def draw_header(y_pos):
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(50,  y_pos, "Ano")
                pdf.drawString(100, y_pos, "N Dec")
                pdf.drawString(200, y_pos, "N Dec Acum")
                pdf.drawString(330, y_pos, "N Cres")
                pdf.drawString(440, y_pos, "N Cres Acum")
                pdf.setFont("Helvetica", 11)

            draw_header(y)
            y -= 18

            for ano, nd, nd_ac, nc, nc_ac in zip(anos, N_dec_ano, N_dec_acum, N_cre_ano, N_cre_acum):
                if y < 60:
                    pdf.showPage()
                    y = 800
                    draw_header(y)
                    y -= 18
                pdf.drawString(50,  y, f"{ano}")
                pdf.drawRightString(180, y, f"{nd:,.2e}")
                pdf.drawRightString(300, y, f"{nd_ac:,.2e}")
                pdf.drawRightString(420, y, f"{nc:,.2e}")
                pdf.drawRightString(540, y, f"{nc_ac:,.2e}")
                y -= 15

            pdf.save()
            QMessageBox.information(self, "Exportado", f"PDF gerado com sucesso em: {caminho}")

        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", str(e))



    def salvar_video_processado(self, historico_path, nome_video):
        with open(historico_path, "a", encoding="utf-8") as f:
            f.write(f"{nome_video}\n")


    def iniciar_processamento(self, model_path, root_directory, line_x, dias_mes,sentido_crescente,fator_sazonalidade,taxa):
        self.config_window.close()
        self.show()
        model = YOLO(model_path)
        self.fator_sazonalide=fator_sazonalidade
        self.taxa=taxa
        region_width = 40
        region_start = line_x - region_width // 2
        region_end = line_x + region_width // 2

        import os

        if self.config_window.modo != "Contagem por Streaming":
            self.historico_dir = os.path.join(root_directory, "_historico")
            os.makedirs(self.historico_dir, exist_ok=True)
            self.historico_path = os.path.join(self.historico_dir, "videos_processados.txt")

            # Carrega vídeos já processados
            self.videos_processados = set()
            if os.path.exists(self.historico_path):
                with open(self.historico_path, "r", encoding="utf-8") as f:
                    self.videos_processados = set(line.strip() for line in f)

            import_path = os.path.join(self.historico_dir, "contagem_global.txt")
            if os.path.exists(import_path):
                try:
                    with open(import_path, 'r', encoding='utf-8') as f:
                        linhas = f.readlines()[1:]  # pula cabeçalho
                        for i, linha in enumerate(linhas):
                            partes = linha.strip().split("	")
                            if len(partes) == 3:
                                classe, decrescente, crescente = partes
                                self.tabela_global.setItem(i, 1, QTableWidgetItem(decrescente))
                                self.tabela_global.setItem(i, 2, QTableWidgetItem(crescente))
                                self.total_decrescente_global[classe] = int(decrescente)
                                self.total_crescente_global[classe] = int(crescente)
                except Exception as e:
                    QMessageBox.warning(self, "Erro ao carregar contagem global", str(e))

        if sentido_crescente == "Esquerda":
            direcao_crescente = "esquerda"
            direcao_decrescente = "direita"
        else:
            direcao_crescente = "direita"
            direcao_decrescente = "esquerda"

        self.total_direita_global = {name: 0 for name in CLASS_NAMES.values()}
        self.total_esquerda_global = {name: 0 for name in CLASS_NAMES.values()}

        if self.config_window.modo == "Selecionar uma pasta apenas" or self.config_window.modo == "Selecionar mês inteiro":

            # Percorre todas as subpastas e arquivos do diretório selecionado
            for subdir, _, files in os.walk(root_directory):
                for file in files:
                    if file in self.videos_processados:
                        continue
                    if file.endswith(".avi"):
                        video_path = os.path.join(subdir, file)
                        cap = cv2.VideoCapture(video_path)
                        vehicle_tracks = {}
                        counted_vehicles = {}
                        cooldown_active = False
                        cooldown_start_frame = 0
                        COOLDOWN_DURATION_FRAMES = 3
                        DELAY_FRAMES = 50

                        while cap.isOpened():
                            ret, frame = cap.read()
                            if not ret:
                                break

                            current_frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                            results = model.track(frame, persist=True, tracker="botsort.yaml")

                            for obj in results[0].boxes:
                                if obj.id is None or obj.cls is None or obj.conf < 0.5:
                                    continue

                                classe = int(obj.cls)
                                if classe not in CLASS_NAMES:
                                    continue

                                id = int(obj.id)
                                bbox = obj.xyxy.cpu().numpy().flatten()
                                x1, y1, x2, y2 = map(int, bbox)
                                x_center = (x1 + x2) // 2
                                y_center = (y1 + y2) // 2

                                if id in vehicle_tracks:
                                    prev_x = vehicle_tracks[id]["x"]
                                    direction = None
                                    if region_start <= x_center <= region_end:
                                        if prev_x < region_start:
                                            direction = "direita"
                                        elif prev_x > region_end:
                                            direction = "esquerda"

                                        if direction:
                                            if id in counted_vehicles:
                                                last_dir = counted_vehicles[id]["direction"]
                                                last_frame = counted_vehicles[id]["frame"]
                                                if current_frame_number - last_frame < DELAY_FRAMES:
                                                    continue

                                            if not cooldown_active:
                                                class_name = CLASS_NAMES[classe]
                                                idx = list(CLASS_NAMES.values()).index(class_name)
                                                if direction == direcao_decrescente:
                                                    # self.total_decrescente_dia[class_name]   += 1   # por dia
                                                    self.total_decrescente_global[class_name] += 1  # global
                                                    # tabela_dia.setItem(idx, 1, QTableWidgetItem(str(self.total_decrescente_dia[class_name])))
                                                    self.tabela_global.setItem(idx, 1, QTableWidgetItem(str(self.total_decrescente_global[class_name])))
                                                else:
                                                    # self.total_crescente_dia[class_name]   += 1
                                                    self.total_crescente_global[class_name] += 1
                                                    # tabela_dia.setItem(idx, 2, QTableWidgetItem(str(self.total_crescente_dia[class_name])))
                                                    self.tabela_global.setItem(idx, 2, QTableWidgetItem(str(self.total_crescente_global[class_name])))

                                                counted_vehicles[id] = {"direction": direction, "frame": current_frame_number}
                                                cooldown_active = True
                                                cooldown_start_frame = current_frame_number

                                vehicle_tracks[id] = {"x": x_center, "frame": current_frame_number}

                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.circle(frame, (x_center, y_center), 4, (0, 0, 255), -1)
                                cv2.putText(frame, CLASS_NAMES[classe], (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                            if cooldown_active and current_frame_number - cooldown_start_frame > COOLDOWN_DURATION_FRAMES:
                                cooldown_active = False

                            cv2.line(frame, (region_start, 0), (region_start, frame.shape[0]), (0, 0, 255), 2)
                            cv2.line(frame, (region_end, 0), (region_end, frame.shape[0]), (0, 0, 255), 2)

                            total_right = sum(self.total_decrescente_global.values())
                            total_left = sum(self.total_crescente_global.values())
                            cv2.rectangle(frame, (5, 5), (400, 40), (0, 0, 0), -1)
                            cv2.putText(frame, f"Decrescente: {total_right}", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

                            cv2.rectangle(frame, (5, 45), (400, 80), (0, 0, 0), -1)
                            cv2.putText(frame, f"Crescente: {total_left}", (10, 70),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

                            # self.atualizar_tabela_contagem(total_direita, total_esquerda)

                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            h, w, ch = rgb_frame.shape
                            bytes_per_line = ch * w
                            qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                            self.video_label.setPixmap(QPixmap.fromImage(qimg))
                            QApplication.processEvents()

                        cap.release()
                        self.salvar_video_processado(self.historico_path, file)

        elif self.config_window.modo=="Definir quantidade de dias":
            from datetime import datetime, timedelta

            # def primeiro_domingo_do_mes(ano, mes):
            #     data = datetime(ano, mes, 1)
            #     while data.weekday() != 6:
            #         data += timedelta(days=1)
            #     return data

            subpastas_validas = [d for d in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, d)) and d.isdigit() and len(d) == 8]
            if not subpastas_validas:
                QMessageBox.warning(self, "Erro", "Nenhuma subpasta válida encontrada no formato AAAAMMDD.")
                return

            datas_validas = [datetime.strptime(d, "%Y%m%d") for d in subpastas_validas]
            datas_validas.sort()

            primeiro_domingo = next((d for d in datas_validas if d.weekday() == 6), None)
            if not primeiro_domingo:
                QMessageBox.warning(self, "Erro", "Nenhum domingo encontrado entre as subpastas.")
                return

            inicio = primeiro_domingo + timedelta(days=7 * (self.config_window.dia_domingo - 1))


            for dia in range(dias_mes):
                self.total_decrescente_dia = {name: 0 for name in CLASS_NAMES.values()}
                self.total_crescente_dia = {name: 0 for name in CLASS_NAMES.values()}
                data = inicio + timedelta(days=dia)
                nome_pasta = data.strftime("%Y%m%d")
                pasta_dia = os.path.join(root_directory, nome_pasta)
                if not os.path.isdir(pasta_dia):
                    continue
                tabela_dia = QTableWidget()
                tabela_dia.setFixedSize(408, 300)
                tabela_dia.setColumnCount(3)
                tabela_dia.setHorizontalHeaderLabels(["Classe", "Decrescente", "Crescente"])
                tabela_dia.verticalHeader().setVisible(False)
                tabela_dia.setEditTriggers(QTableWidget.NoEditTriggers)
                tabela_dia.setRowCount(len(CLASS_NAMES))
                for i, nome_classe in enumerate(CLASS_NAMES.values()):
                    tabela_dia.setItem(i, 0, QTableWidgetItem(nome_classe))
                    tabela_dia.setItem(i, 1, QTableWidgetItem("0"))
                    tabela_dia.setItem(i, 2, QTableWidgetItem("0"))
                tabela_dia.resizeColumnsToContents()
                tabela_dia.resizeRowsToContents()

                aba = QWidget()
                layout_aba = QVBoxLayout()
                layout_aba.addWidget(tabela_dia)
                aba.setLayout(layout_aba)
                self.tabs.addTab(aba, f"Dia {data.strftime('%d/%m/%Y')}")
                
                for hora in sorted(os.listdir(pasta_dia)):
                    pasta_hora = os.path.join(pasta_dia, hora)
                    if not os.path.isdir(pasta_hora):
                        continue
                    for file in os.listdir(pasta_hora):
                        if not file.endswith(".avi"):
                            continue
                        if file in self.videos_processados:
                            continue
                        
                        video_path = os.path.join(pasta_hora, file)
                        cap = cv2.VideoCapture(video_path)
                        vehicle_tracks = {}
                        counted_vehicles = {}
                        cooldown_active = False
                        cooldown_start_frame = 0
                        COOLDOWN_DURATION_FRAMES = 3
                        DELAY_FRAMES = 50

                        while cap.isOpened():
                            if self.video_stopped:
                                break
                            if self.video_paused:
                                QApplication.processEvents()
                                continue
                            ret, frame = cap.read()
                            if not ret:
                                break

                            current_frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                            results = model.track(frame, persist=True, tracker="botsort.yaml")

                            for obj in results[0].boxes:
                                if obj.id is None or obj.cls is None or obj.conf < 0.5:
                                    continue

                                classe = int(obj.cls)
                                if classe not in CLASS_NAMES:
                                    continue

                                id = int(obj.id)
                                bbox = obj.xyxy.cpu().numpy().flatten()
                                x1, y1, x2, y2 = map(int, bbox)
                                x_center = (x1 + x2) // 2
                                y_center = (y1 + y2) // 2

                                if id in vehicle_tracks:
                                    prev_x = vehicle_tracks[id]["x"]
                                    direction = None
                                    if region_start <= x_center <= region_end:
                                        if prev_x < region_start:
                                            direction = "direita"
                                        elif prev_x > region_end:
                                            direction = "esquerda"

                                        if direction:
                                            if id in counted_vehicles:
                                                last_dir = counted_vehicles[id]["direction"]
                                                last_frame = counted_vehicles[id]["frame"]
                                                if current_frame_number - last_frame < DELAY_FRAMES:
                                                    continue

                                            if not cooldown_active:
                                                class_name = CLASS_NAMES[classe]
                                                idx = list(CLASS_NAMES.values()).index(class_name)
                                                if direction == direcao_decrescente:
                                                    self.total_decrescente_dia[class_name]   += 1   # por dia
                                                    self.total_decrescente_global[class_name] += 1  # global
                                                    tabela_dia.setItem(idx, 1, QTableWidgetItem(str(self.total_decrescente_dia[class_name])))
                                                    self.tabela_global.setItem(idx, 1, QTableWidgetItem(str(self.total_decrescente_global[class_name])))
                                                else:
                                                    self.total_crescente_dia[class_name]   += 1
                                                    self.total_crescente_global[class_name] += 1
                                                    tabela_dia.setItem(idx, 2, QTableWidgetItem(str(self.total_crescente_dia[class_name])))
                                                    self.tabela_global.setItem(idx, 2, QTableWidgetItem(str(self.total_crescente_global[class_name])))

                                                counted_vehicles[id] = {"direction": direction, "frame": current_frame_number}
                                                cooldown_active = True
                                                cooldown_start_frame = current_frame_number

                                vehicle_tracks[id] = {"x": x_center, "frame": current_frame_number}

                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.circle(frame, (x_center, y_center), 4, (0, 0, 255), -1)
                                cv2.putText(frame, CLASS_NAMES[classe], (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                            if cooldown_active and current_frame_number - cooldown_start_frame > COOLDOWN_DURATION_FRAMES:
                                cooldown_active = False

                            cv2.line(frame, (region_start, 0), (region_start, frame.shape[0]), (0, 0, 255), 2)
                            cv2.line(frame, (region_end, 0), (region_end, frame.shape[0]), (0, 0, 255), 2)

                            total_right = sum(self.total_decrescente_global.values())
                            total_left = sum(self.total_crescente_global.values())
                            cv2.rectangle(frame, (5, 45), (400, 80), (0, 0, 0), -1)
                            cv2.putText(frame, f"Total Decrescente: {total_right}", (10, 70),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

                            cv2.rectangle(frame, (5, 5), (400, 40), (0, 0, 0), -1)
                            cv2.putText(frame, f"Total Crescente: {total_left}", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

                            # self.atualizar_tabela_contagem(total_direita, total_esquerda)

                            # Redimensionar apenas para exibição (sem alterar contagem)
                            exibicao_frame = cv2.resize(frame, (640, 360))  # ou outro tamanho menor

                            h, w, ch = exibicao_frame.shape
                            bytes_per_line = ch * w
                            qimg = QImage(exibicao_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                            self.video_label.setPixmap(QPixmap.fromImage(qimg))
                            QApplication.processEvents()

                        cap.release()
                        self.salvar_video_processado(self.historico_path, file)
                        self.salvar_tabela_txt()

        else:
            cap = cv2.VideoCapture(self.config_window.link, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not cap.isOpened():
                QMessageBox.critical(self, "Erro", "Não foi possível abrir o link de streaming.")
                return

            vehicle_tracks = {}
            counted_vehicles = {}
            cooldown_active = False
            cooldown_start_frame = 0
            COOLDOWN_DURATION_FRAMES = 3
            DELAY_FRAMES = 50

            while cap.isOpened():
                if self.video_stopped:
                    break
                if self.video_paused:
                    QApplication.processEvents()
                    continue

                ret, frame = cap.read()
                if not ret:
                    break

                current_frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                results = model.track(frame, persist=True, tracker="botsort.yaml")

                for obj in results[0].boxes:
                    if obj.id is None or obj.cls is None or obj.conf < 0.5:
                        continue

                    classe = int(obj.cls)
                    if classe not in CLASS_NAMES:
                        continue

                    id = int(obj.id)
                    bbox = obj.xyxy.cpu().numpy().flatten()
                    x1, y1, x2, y2 = map(int, bbox)
                    x_center = (x1 + x2) // 2
                    y_center = (y1 + y2) // 2

                    if id in vehicle_tracks:
                        prev_x = vehicle_tracks[id]["x"]
                        direction = None
                        if region_start <= x_center <= region_end:
                            if prev_x < region_start:
                                direction = "direita"
                            elif prev_x > region_end:
                                direction = "esquerda"

                            if direction:
                                if id in counted_vehicles:
                                    last_dir = counted_vehicles[id]["direction"]
                                    last_frame = counted_vehicles[id]["frame"]
                                    if current_frame_number - last_frame < DELAY_FRAMES:
                                        continue

                                if not cooldown_active:
                                    class_name = CLASS_NAMES[classe]
                                    if direction == direcao_decrescente:
                                        self.total_decrescente_global[class_name] += 1
                                    else:
                                        self.total_crescente_global[class_name] += 1

                                    idx = list(CLASS_NAMES.values()).index(class_name)
                                    self.tabela_global.setItem(idx, 1, QTableWidgetItem(str(self.total_decrescente_global[class_name])))
                                    self.tabela_global.setItem(idx, 2, QTableWidgetItem(str(self.total_crescente_global[class_name])))

                                    counted_vehicles[id] = {"direction": direction, "frame": current_frame_number}
                                    cooldown_active = True
                                    cooldown_start_frame = current_frame_number

                    vehicle_tracks[id] = {"x": x_center, "frame": current_frame_number}

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (x_center, y_center), 4, (0, 0, 255), -1)
                    cv2.putText(frame, CLASS_NAMES[classe], (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                if cooldown_active and current_frame_number - cooldown_start_frame > COOLDOWN_DURATION_FRAMES:
                    cooldown_active = False

                cv2.line(frame, (region_start, 0), (region_start, frame.shape[0]), (0, 0, 255), 2)
                cv2.line(frame, (region_end, 0), (region_end, frame.shape[0]), (0, 0, 255), 2)

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(qimg))
                QApplication.processEvents()

            cap.release()
            return


                
                

        QMessageBox.information(self, "Processamento Concluído", "Todos os vídeos foram processados com sucesso.")


    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MainWindow()
    sys.exit(app.exec_())
