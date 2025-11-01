"""
Language detection utilities for GenSec.
Detects programming language and framework from file paths and code.
"""

def detect_language_from_path(file_path):
    """
    Detect programming language from file extension.
    Returns (language, framework) tuple.
    """
    if not file_path:
        return 'unknown', None
    
    file_path_lower = file_path.lower()
    
    # Python detection
    if file_path_lower.endswith('.py'):
        # Framework detection based on path patterns
        if 'django' in file_path_lower or 'settings.py' in file_path_lower or 'urls.py' in file_path_lower:
            return 'python', 'django'
        elif 'flask' in file_path_lower or 'app.py' in file_path_lower:
            return 'python', 'flask'
        elif 'fastapi' in file_path_lower or 'main.py' in file_path_lower:
            return 'python', 'fastapi'
        else:
            return 'python', None
    
    # JavaScript/TypeScript detection
    elif file_path_lower.endswith(('.js', '.jsx')):
        if 'react' in file_path_lower or file_path_lower.endswith('.jsx'):
            return 'javascript', 'react'
        elif 'node' in file_path_lower or 'server' in file_path_lower:
            return 'javascript', 'nodejs'
        else:
            return 'javascript', None
    elif file_path_lower.endswith(('.ts', '.tsx')):
        if 'react' in file_path_lower or file_path_lower.endswith('.tsx'):
            return 'javascript', 'react'
        else:
            return 'javascript', 'typescript'
    
    # Java detection
    elif file_path_lower.endswith('.java'):
        if 'spring' in file_path_lower or 'controller' in file_path_lower or 'service' in file_path_lower:
            return 'java', 'spring-boot'
        else:
            return 'java', None
    
    # C# detection
    elif file_path_lower.endswith(('.cs', '.cshtml')):
        if 'controller' in file_path_lower or 'startup.cs' in file_path_lower:
            return 'csharp', 'dotnet'
        else:
            return 'csharp', None
    
    # Go detection
    elif file_path_lower.endswith('.go'):
        return 'go', None
    
    # Default to unknown
    return 'unknown', None


def get_language_name(language, framework=None):
    """Get display name for language and framework."""
    lang_names = {
        'python': 'Python',
        'javascript': 'JavaScript',
        'java': 'Java',
        'csharp': 'C#',
        'go': 'Go'
    }
    
    lang_display = lang_names.get(language, language.capitalize())
    
    if framework:
        framework_names = {
            'django': 'Django',
            'flask': 'Flask',
            'fastapi': 'FastAPI',
            'react': 'React',
            'nodejs': 'Node.js',
            'typescript': 'TypeScript',
            'spring-boot': 'Spring Boot',
            'dotnet': '.NET'
        }
        framework_display = framework_names.get(framework, framework)
        return f"{lang_display} ({framework_display})"
    
    return lang_display

