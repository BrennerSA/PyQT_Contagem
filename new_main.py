import sys
from PyQt5.QtWidgets import QApplication
from interface import Interface
from main_window import MainWindow

def start_app(model_path, root_directory, line_x, dias_mes, sentido, sazonalidade, taxa):
    janela = MainWindow(model_path, root_directory, line_x, dias_mes, sentido, sazonalidade, taxa)
    janela.show()
    return janela

if __name__ == "__main__":
    app = QApplication(sys.argv)
    interface = Interface(start_app)
    interface.show()
    sys.exit(app.exec_())
