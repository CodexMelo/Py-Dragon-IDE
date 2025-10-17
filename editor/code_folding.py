from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QTextBlockUserData



class CodeFoldingArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setMouseTracking(True)
        self.setFixedWidth(16)
        
    def sizeHint(self):
        return QSize(16, 0)
        
    def paintEvent(self, event):
        """Pinta os indicadores de folding - VERSÃO CORRIGIDA"""
        try:
            painter = QPainter(self)
            if not painter.isActive():
                return
                
            # Preenche o fundo com cor mais suave
            painter.fillRect(event.rect(), QColor(40, 40, 45))
            
            block = self.editor.firstVisibleBlock()
            block_number = block.blockNumber()
            top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            bottom = top + self.editor.blockBoundingRect(block).height()
            
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    # Desenha o indicador de folding se a linha for dobrável
                    if self.is_block_foldable(block):
                        rect = QRect(4, int(top) + 4, 8, 8)  # Indicador menor
                        
                        # Cor do indicador mais suave
                        painter.setPen(QColor(120, 120, 120))
                        painter.setBrush(QColor(60, 60, 65))
                        painter.drawRect(rect)
                        
                        # Sinal de + ou -
                        painter.setPen(QColor(180, 180, 180))
                        painter.drawLine(rect.left() + 2, rect.center().y(), rect.right() - 2, rect.center().y())
                        
                        # Só desenha a linha vertical se não estiver dobrado
                        if not self.is_block_folded(block):
                            painter.drawLine(rect.center().x(), rect.top() + 2, rect.center().x(), rect.bottom() - 2)
                
                block = block.next()
                top = bottom
                bottom = top + self.editor.blockBoundingRect(block).height()
                block_number += 1
                
        except Exception as e:
            print(f"Erro no paintEvent do folding: {e}")

    def is_block_foldable(self, block):
        """Verifica se um bloco pode ser dobrado - MAIS PRECISO"""
        try:
            text = block.text().strip()
            
            # Apenas linhas que realmente iniciam estruturas de bloco
            return (text.startswith('class ') or 
                    text.startswith('def ') or 
                    text.startswith('async def') or
                    (text.startswith('if ') and text.endswith(':')) or
                    (text.startswith('for ') and text.endswith(':')) or
                    (text.startswith('while ') and text.endswith(':')) or
                    (text.startswith('with ') and text.endswith(':')) or
                    text == 'try:' or
                    (text.startswith('elif ') and text.endswith(':')) or
                    text == 'else:' or
                    text == 'except:' or
                    text == 'finally:')
        except:
            return False

    def is_block_folded(self, block):
        """Verifica se um bloco está dobrado - MÉTODO ADICIONADO"""
        try:
            user_data = block.userData()
            if user_data and hasattr(user_data, 'is_folded'):
                return user_data.is_folded()
            return False
        except:
            return False

    def mousePressEvent(self, event):
        """Manipula clique nos indicadores de folding - CORRIGIDO"""
        if event.button() == Qt.LeftButton:
            # Encontra o bloco clicado - CORREÇÃO PARA PySide6
            block = self.editor.firstVisibleBlock()
            top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            bottom = top + self.editor.blockBoundingRect(block).height()
            
            while block.isValid():
                # PySide6 usa position() em vez de pos()
                if (event.position().y() >= top and event.position().y() <= bottom and 
                    self.is_block_foldable(block)):
                    self.toggle_fold(block)
                    break
                
                block = block.next()
                top = bottom
                bottom = top + self.editor.blockBoundingRect(block).height()

    def toggle_fold(self, block):
        """Alterna o estado de folding de um bloco - CORRIGIDO"""
        if not self.is_block_foldable(block):
            return
            
        try:
            # Obtém ou cria dados do usuário para o bloco
            user_data = block.userData()
            if not user_data or not hasattr(user_data, 'set_folded'):
                # Cria novos dados de folding se não existirem
                user_data = FoldData()
                block.setUserData(user_data)
            
            # Alterna estado
            currently_folded = self.is_block_folded(block)
            user_data.set_folded(not currently_folded)
            
            # Aplica o folding
            self.apply_folding(block, not currently_folded)
            
            # Atualiza a visualização
            self.update()
            self.editor.viewport().update()
            
        except Exception as e:
            print(f"Erro ao alternar folding: {e}")

    def apply_folding(self, start_block, fold):
        """Aplica folding a partir de um bloco - VERSÃO MELHORADA"""
        try:
            start_text = start_block.text()
            start_indent = len(start_text) - len(start_text.lstrip())
            current_block = start_block.next()
            
            blocks_to_fold = []
            
            while current_block.isValid():
                current_text = current_block.text()
                if not current_text.strip():  # Linha vazia
                    current_block = current_block.next()
                    continue
                    
                current_indent = len(current_text) - len(current_text.lstrip())
                
                # Se a indentação for menor ou igual, para
                if current_indent <= start_indent:
                    break
                    
                # Marca bloco para ser dobrado
                blocks_to_fold.append(current_block)
                current_block = current_block.next()
            
            # Aplica folding a todos os blocos de uma vez
            for block in blocks_to_fold:
                block.setVisible(not fold)
                
        except Exception as e:
            print(f"Erro ao aplicar folding: {e}")




class FoldData(QTextBlockUserData):
    
    def __init__(self):
        super().__init__()
        self._folded = False
        self._fold_level = 0
    
    def is_folded(self):
        return self._folded
    
    def set_folded(self, folded):
        self._folded = folded
    
    def get_fold_level(self):
        return self._fold_level
    
    def set_fold_level(self, level):
        self._fold_level = level
            