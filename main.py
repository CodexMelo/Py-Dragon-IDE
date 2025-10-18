import sys
import os
import traceback
from pathlib import Path

# Configurar path antes de importar PySide6
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
from PySide6.QtNetwork import QLocalSocket, QLocalServer

# Import absoluto    
from core.application import IDE


class SingleApplication:
    def __init__(self, app_id):
        self.app_id = app_id
        self.server = None
        self.socket = QLocalSocket()
        self.ide_window = None

    def is_running(self):
        """Verifica se já existe uma instância rodando"""
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        if socket.waitForConnected(500):
            socket.disconnectFromServer()
            return True
        return False

    def run(self, ide_instance=None):
        """Tenta executar a aplicação"""
        if self.is_running():
            print("⚠️ Outra instância já está em execução")
            # Envia mensagem para instância existente
            self.send_activate_signal()
            return False
            
        # Remove servidor anterior se existir
        QLocalServer.removeServer(self.app_id)
        
        # Cria novo servidor
        self.server = QLocalServer()
        if not self.server.listen(self.app_id):
            print(f"❌ Não foi possível iniciar servidor: {self.server.errorString()}")
            return False
            
        self.ide_window = ide_instance
        self.server.newConnection.connect(self.handle_new_connection)
        print("✅ Servidor de instância única iniciado")
        return True

    def send_activate_signal(self):
        """Envia sinal para ativar instância existente"""
        try:
            socket = QLocalSocket()
            socket.connectToServer(self.app_id)
            if socket.waitForConnected(1000):
                socket.write(b"activate")
                socket.flush()
                socket.waitForBytesWritten(1000)
                socket.disconnectFromServer()
                print("✅ Sinal de ativação enviado")
        except Exception as e:
            print(f"❌ Erro ao enviar sinal: {e}")

    def handle_new_connection(self):
        """Manipula nova conexão do launcher"""
        try:
            connection = self.server.nextPendingConnection()
            if connection and connection.waitForReadyRead(1000):
                data = connection.readAll().data().decode('utf-8').strip()
                connection.disconnectFromServer()
                
                if data == "activate" and self.ide_window:
                    # Ativa a janela existente
                    QTimer.singleShot(100, self.activate_window)
                    
        except Exception as e:
            print(f"❌ Erro na conexão: {e}")

    def activate_window(self):
        """Ativa a janela do IDE"""
        if self.ide_window:
            self.ide_window.show()
            self.ide_window.raise_()
            self.ide_window.activateWindow()
            print("✅ Janela do IDE ativada")


def setup_encoding():
    """Configura encoding UTF-8 de forma segura"""
    try:
        if os.name == 'nt':
            if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def handle_exception(exc_type, exc_value, exc_traceback):
    """Handler global para exceções não capturadas"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    print("❌ Erro não capturado:", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    
    # Mostra dialog de erro se possível
    try:
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None,
                "Erro Crítico",
                f"Ocorreu um erro inesperado:\n\n{str(exc_value)}\n\n"
                f"Verifique o console para mais detalhes."
            )
    except:
        pass


def main():
    """Função principal da aplicação - APENAS START"""
    # Configurar handler de exceções
    sys.excepthook = handle_exception
    
    # Configurar encoding
    setup_encoding()
    
    # Criar QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Py Dragon Studio IDE")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PyDragonStudio")
    
    # Verificar instância única
    single_app = SingleApplication("py_dragon_studio_ide")
    
    if not single_app.run():
        print("🚫 Aplicação já está em execução. Saindo.")
        sys.exit(0)

    try:
        # Criar janela principal - O IDE que cuida dos plugins
        window = IDE()
        single_app.ide_window = window
        
        # Mostrar janela
        window.show()
        
        print("🚀 Py Dragon Studio IDE iniciado!")
        
        # Executar aplicação
        exit_code = app.exec()
        
        # Limpeza final
        if single_app.server:
            single_app.server.close()
            
        print("👋 Aplicação finalizada")
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Erro crítico na inicialização: {e}")
        traceback.print_exc()
        
        # Tentar mostrar dialog de erro
        try:
            QMessageBox.critical(
                None, 
                "Erro de Inicialização", 
                f"Falha ao iniciar o IDE:\n{str(e)}\n\n"
                f"Verifique se todas as dependências estão instaladas."
            )
        except:
            pass
            
        sys.exit(1)


if __name__ == "__main__":
    main()