from PySide6.QtCore import QObject
from PySide6.QtGui import QTextCursor, QColor


class CodeIndicators:
    """Sistema de indicadores visuais para o editor de código"""
    
    def __init__(self, editor):
        self.editor = editor
        self.setup_indicators()
        
    def setup_indicators(self):
        """Configura todos os indicadores visuais"""
        self.setup_line_highlight()
        self.setup_indentation_guides()
        self.setup_current_scope_highlight()
        self.setup_error_indicators()
        
    def setup_line_highlight(self):
        """Configura destaque da linha atual"""
        # Isso será conectado ao sinal cursorPositionChanged
        pass
    
    def setup_indentation_guides(self):
        """Configura guias de indentação"""
        # Guias de indentação são desenhados no paintEvent
        pass
    
    def setup_current_scope_highlight(self):
        """Configura destaque do escopo atual"""
        pass
    
    def setup_error_indicators(self):
        """Configura indicadores de erro"""
        pass
    
    def highlight_current_line(self):
        """Destaca a linha atual do cursor - CORRIGIDO"""
        try:
            extra_selections = []
            
            if not self.editor.isReadOnly():
                selection = QTextEdit.ExtraSelection()
                line_color = QColor(45, 45, 48)
                selection.format.setBackground(line_color)
                
                # CORREÇÃO: Usar a constante correta do Qt
                selection.format.setProperty(QTextFormat.FullWidthSelection, True)
                
                selection.cursor = self.editor.textCursor()
                selection.cursor.clearSelection()
                extra_selections.append(selection)
            
            self.editor.setExtraSelections(extra_selections)
        except Exception as e:
            print(f"Erro no highlight da linha: {e}")
    
    def highlight_matching_words(self):
        """Destaca palavras idênticas à seleção atual"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            if len(selected_text) > 1 and selected_text.isalnum():
                self.highlight_all_occurrences(selected_text)
    
    def highlight_all_occurrences(self, text):
        """Destaca todas as ocorrências de um texto"""
        extra_selections = []
        cursor = self.editor.textCursor()
        document = self.editor.document()
        
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(86, 156, 214, 50))  # Azul translúcido
        
        # Busca todas as ocorrências
        search_cursor = QTextCursor(document)
        while not search_cursor.isNull() and not search_cursor.atEnd():
            search_cursor = document.find(text, search_cursor)
            if not search_cursor.isNull():
                selection = QTextEdit.ExtraSelection()
                selection.format = highlight_format
                selection.cursor = search_cursor
                extra_selections.append(selection)
        
        self.editor.setExtraSelections(extra_selections)


