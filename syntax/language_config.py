from typing import Dict, List



class LanguageConfig:
    def __init__(self):
        self.supported_languages = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.sql': 'SQL',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.md': 'Markdown',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.txt': 'Text'
        }

    def get_language_from_extension(self, file_path):
        if not file_path:
            return 'Text'
        _, ext = os.path.splitext(file_path)
        return self.supported_languages.get(ext.lower(), 'Text')

