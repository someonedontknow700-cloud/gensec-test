import os
from groq import Groq
from gensec.constants import GROQ_API_KEY, GROQ_MODEL
from gensec.language_detector import detect_language_from_path, get_language_name

def _get_base_prompt(file_path, language, framework, full_code):
    """Generate language-specific base prompt."""
    lang_name = get_language_name(language, framework)
    
    return f"""
You are GenSec, an elite AI DevSecOps agent specialized in {lang_name} security fixes.
Your mission is to fix *ONLY ONE* specific security vulnerability in the following {lang_name} file.
File to fix: `{file_path}`
You must not change any other part of the code, even if you see other bugs.
Your goal is to create a minimal, correct patch for only the single bug I describe.
IMPORTANT: You must provide *ONLY* the *ENTIRE* fixed {lang_name} file. Do not provide any other text,
explanation, or markdown fences (```) around the code. Start with the file's original first line
and end with the last line of the file.
THE FULL VULNERABLE FILE (`{file_path}`):
---
{full_code}
---
"""
    
def _determine_vulnerability_type(check_id, issue, tool):
    """Determine the vulnerability type from check_id and issue."""
    issue_lower = issue.lower()
    
    if 'gitleaks' in tool or 'secret' in issue_lower or 'hardcoded' in issue_lower:
        return 'secret'
    elif 'G204' in check_id or 'command' in issue_lower or 'exec' in issue_lower or 'shell' in issue_lower:
        return 'command_injection'
    elif 'sql' in issue_lower or 'string-formatted-query' in check_id or 'query' in issue_lower:
        return 'sql_injection'
    elif 'G103' in check_id or 'path' in issue_lower or 'traversal' in issue_lower:
        return 'path_traversal'
    elif 'G402' in check_id or 'cors' in issue_lower:
        return 'cors'
    elif 'G104' in check_id or 'sensitive' in issue_lower or 'log' in issue_lower:
        return 'sensitive_data'
    else:
        return 'default'

def _get_language_specific_task_prompt(language, framework, vuln_type, check_id, issue, snippet, line):
    """Get language-specific task prompt based on vulnerability type."""
    
    # Route to language-specific expert
    if language == 'python':
        return _get_python_task_prompt(framework, vuln_type, issue, snippet, line)
    elif language == 'javascript':
        return _get_javascript_task_prompt(framework, vuln_type, issue, snippet, line)
    elif language == 'java':
        return _get_java_task_prompt(framework, vuln_type, issue, snippet, line)
    elif language == 'csharp':
        return _get_csharp_task_prompt(framework, vuln_type, issue, snippet, line)
    elif language == 'go':
        return _get_go_task_prompt(vuln_type, issue, snippet, line)
    else:
        # Default fallback
        return _get_generic_task_prompt(vuln_type, issue, snippet, line)

def _get_python_task_prompt(framework, vuln_type, issue, snippet, line):
    """Python-specific task prompts (Django, Flask, FastAPI)."""
    expert_name = f"Python ({framework.capitalize() if framework else 'Generic'}) {vuln_type.replace('_', ' ').title()} Expert"
    print(f"ℹ️  (Fixer): Selected '{expert_name}'")
    
    if vuln_type == 'secret':
        if framework == 'django':
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using Django settings pattern:
    -   BAD: SECRET_KEY = "sk_live_12345..."
    -   GOOD: SECRET_KEY = os.getenv("SECRET_KEY", settings.SECRET_KEY)
    -   Or use: from django.conf import settings; SECRET_KEY = settings.SECRET_KEY
3.  For API keys, use: api_key = os.getenv("API_KEY") or use Django's settings.py
4.  Ensure 'os' is imported: import os
5.  You MUST NOT fix any other bugs.
6.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
        elif framework == 'flask':
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using Flask config pattern:
    -   BAD: app.config['SECRET_KEY'] = "sk_live_12345..."
    -   GOOD: app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    -   Or: app.config.from_object(os.getenv('FLASK_ENV', 'Development'))
3.  For environment variables: api_key = os.environ.get("API_KEY")
4.  Ensure 'os' is imported: import os
5.  You MUST NOT fix any other bugs.
6.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
        elif framework == 'fastapi':
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using FastAPI/Pydantic settings pattern:
    -   BAD: API_KEY = "sk_live_12345..."
    -   GOOD: from pydantic_settings import BaseSettings; class Settings(BaseSettings): api_key: str; settings = Settings()
    -   Or simple: API_KEY = os.getenv("API_KEY")
3.  For secrets: import os; secret = os.getenv("SECRET")
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
        else:
            # Generic Python
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using environment variables:
    -   BAD: api_key = "sk_live_12345..."
    -   GOOD: import os; api_key = os.getenv("API_KEY")
3.  Ensure 'os' is imported if not already.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sql_injection':
        if framework == 'django':
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using Django ORM (preferred) or parameterized queries:
    -   BAD: User.objects.extra(where=["name = '%s'" % name])
    -   GOOD: User.objects.filter(name=name)  # Django ORM
    -   OR: from django.db import connection; cursor.execute("SELECT * FROM users WHERE name = %s", [name])
3.  NEVER use string formatting with SQL. Always use ORM or parameterized queries (%s placeholder).
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
        elif framework == 'flask':
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using SQLAlchemy ORM or parameterized queries:
    -   BAD: db.execute(f"SELECT * FROM users WHERE name = '{name}'")
    -   GOOD: User.query.filter_by(name=name).all()  # SQLAlchemy ORM
    -   OR: db.execute("SELECT * FROM users WHERE name = %s", (name,))  # Parameterized
3.  Use ? placeholders for SQLite, %s for PostgreSQL/MySQL.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using parameterized queries:
    -   BAD: cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
    -   GOOD: cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
3.  Use ? for SQLite, %s for PostgreSQL/MySQL.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'command_injection':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Command Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Command Injection.
2.  Fix using subprocess with list arguments (NEVER shell=True):
    -   BAD: os.system(f"ping -c 1 {host}") or subprocess.call(f"ping {host}", shell=True)
    -   GOOD: import subprocess; subprocess.run(["ping", "-c", "1", host])
3.  Always pass command and args as a list, never as a string.
4.  You MUST ensure subprocess is imported.
5.  You MUST NOT fix any other bugs.
6.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'path_traversal':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Path Traversal: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Path Traversal vulnerability.
2.  Fix using os.path.join and os.path.abspath:
    -   BAD: file_path = "/app/static/" + user_input
    -   GOOD: 
        import os
        base_dir = "/app/static"
        safe_path = os.path.join(base_dir, os.path.basename(user_input))
        abs_path = os.path.abspath(safe_path)
        if not abs_path.startswith(os.path.abspath(base_dir)):
            raise ValueError("Invalid path")
3.  You MUST ensure "os" is imported.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'cors':
        if framework == 'django':
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix using django-cors-headers settings (preferred) or manual headers:
    -   BAD: response["Access-Control-Allow-Origin"] = "*"
    -   GOOD in settings.py:
        CORS_ALLOWED_ORIGINS = [os.getenv("ALLOWED_ORIGIN")]
    -   OR manual: response["Access-Control-Allow-Origin"] = os.getenv("ALLOWED_ORIGIN")
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
        elif framework == 'flask':
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix using Flask-CORS (preferred) or manual headers:
    -   BAD: response.headers['Access-Control-Allow-Origin'] = '*'
    -   GOOD: from flask_cors import CORS; CORS(app, resources={{r"/*": {{"origins": os.getenv("ALLOWED_ORIGIN")}}}})
    -   OR: response.headers['Access-Control-Allow-Origin'] = os.getenv("ALLOWED_ORIGIN")
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix by replacing wildcard with environment variable:
    -   BAD: headers['Access-Control-Allow-Origin'] = '*'
    -   GOOD: import os; headers['Access-Control-Allow-Origin'] = os.getenv("ALLOWED_ORIGIN")
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sensitive_data':
        return f"""
THE VULNERABILITY:
A Semgrep scan found sensitive data leak: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* sensitive data leak (e.g., logging password, token, or error details).
2.  Fix by removing sensitive information from logs/errors:
    -   BAD: logging.info(f"Login failed for {user} with password {password}")
    -   GOOD: logging.info(f"Login failed for user: {user}")
    -   BAD: raise Exception(str(err))  # where err contains sensitive data
    -   GOOD: raise Exception("Authentication failed")  # Generic error
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""
    
    else:  # default
        return f"""
THE VULNERABILITY:
A Semgrep scan found this issue: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate and fix *only* this one specific vulnerability using Python best practices.
2.  You MUST NOT fix any other bugs in the file.
3.  Return the *ENTIRE* corrected Python file.
FULL FIXED CODE:
"""

def _get_javascript_task_prompt(framework, vuln_type, issue, snippet, line):
    """JavaScript-specific task prompts (Node.js, React)."""
    expert_name = f"JavaScript ({framework.capitalize() if framework else 'Generic'}) {vuln_type.replace('_', ' ').title()} Expert"
    print(f"ℹ️  (Fixer): Selected '{expert_name}'")
    
    if vuln_type == 'secret':
        if framework == 'nodejs':
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using Node.js environment variables or dotenv:
    -   BAD: const apiKey = "sk_live_12345..."
    -   GOOD: const apiKey = process.env.API_KEY
    -   OR with dotenv: require('dotenv').config(); const apiKey = process.env.API_KEY
3.  For Express apps: Use app.set('secret', process.env.SECRET_KEY)
4.  Ensure dotenv is configured if using .env file.
5.  You MUST NOT fix any other bugs.
6.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
        elif framework == 'react':
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using React environment variables (REACT_APP_ prefix):
    -   BAD: const apiKey = "sk_live_12345..."
    -   GOOD: const apiKey = process.env.REACT_APP_API_KEY
3.  IMPORTANT: Frontend secrets should be in .env.local with REACT_APP_ prefix.
4.  Never expose real secrets in frontend - use proxy API for sensitive operations.
5.  You MUST NOT fix any other bugs.
6.  Return the *ENTIRE* corrected JavaScript/JSX file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using environment variables:
    -   BAD: const apiKey = "sk_live_12345..."
    -   GOOD: const apiKey = process.env.API_KEY || require('dotenv').config()
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sql_injection':
        if framework == 'nodejs':
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using parameterized queries with placeholder:
    -   BAD: db.query(`SELECT * FROM users WHERE name = '${name}'`)
    -   GOOD: db.query("SELECT * FROM users WHERE name = ?", [name])  # MySQL
    -   OR: db.query("SELECT * FROM users WHERE name = $1", [name])  # PostgreSQL
3.  For Sequelize ORM: User.findOne({{ where: {{ name: name }} }})
4.  NEVER use template literals or string concatenation for SQL queries.
5.  You MUST NOT fix any other bugs.
6.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using parameterized queries:
    -   BAD: query(`SELECT * FROM users WHERE name = '${name}'`)
    -   GOOD: query("SELECT * FROM users WHERE name = ?", [name])
3.  Use ? for MySQL/SQLite, $1 for PostgreSQL.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'command_injection':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Command Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Command Injection.
2.  Fix using child_process.spawn with array arguments:
    -   BAD: exec(`ping -c 1 ${host}`) or execSync(`ping ${host}`)
    -   GOOD: const {{ spawn }} = require('child_process'); spawn('ping', ['-c', '1', host])
3.  NEVER use exec/execSync with user input. Always use spawn with array arguments.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'path_traversal':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Path Traversal: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Path Traversal vulnerability.
2.  Fix using path.join and path.resolve:
    -   BAD: const filePath = "/app/static/" + userInput
    -   GOOD: 
        const path = require('path');
        const baseDir = "/app/static";
        const safePath = path.join(baseDir, path.basename(userInput));
        const absPath = path.resolve(safePath);
        if (!absPath.startsWith(path.resolve(baseDir))) {{
            throw new Error("Invalid path");
        }}
3.  You MUST ensure "path" module is imported.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'cors':
        if framework == 'nodejs':
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix using cors middleware with allowlist:
    -   BAD: app.use(cors()) or app.use(cors({{ origin: '*' }}))
    -   GOOD: 
        const cors = require('cors');
        app.use(cors({{
            origin: process.env.ALLOWED_ORIGIN || 'http://localhost:3000'
        }}))
    -   OR: app.use((req, res, next) => {{
            const origin = req.headers.origin;
            if (origin === process.env.ALLOWED_ORIGIN) {{
                res.header('Access-Control-Allow-Origin', origin);
            }}
            next();
        }})
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix by replacing wildcard with environment variable:
    -   BAD: headers['Access-Control-Allow-Origin'] = '*'
    -   GOOD: headers['Access-Control-Allow-Origin'] = process.env.ALLOWED_ORIGIN
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sensitive_data':
        return f"""
THE VULNERABILITY:
A Semgrep scan found sensitive data leak: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* sensitive data leak (e.g., logging password, token).
2.  Fix by removing sensitive information:
    -   BAD: console.log(`Login failed for ${{user}} with password ${{password}}`)
    -   GOOD: console.log(`Login failed for user: ${{user}}`)
    -   BAD: res.status(500).json({{ error: err.message }})  # where err contains sensitive data
    -   GOOD: res.status(500).json({{ error: "Internal server error" }})
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""
    
    else:  # default
        return f"""
THE VULNERABILITY:
A Semgrep scan found this issue: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate and fix *only* this one specific vulnerability using JavaScript best practices.
2.  You MUST NOT fix any other bugs in the file.
3.  Return the *ENTIRE* corrected JavaScript file.
FULL FIXED CODE:
"""

def _get_java_task_prompt(framework, vuln_type, issue, snippet, line):
    """Java-specific task prompts (Spring Boot)."""
    expert_name = f"Java ({framework.capitalize() if framework else 'Generic'}) {vuln_type.replace('_', ' ').title()} Expert"
    print(f"ℹ️  (Fixer): Selected '{expert_name}'")
    
    if vuln_type == 'secret':
        if framework == 'spring-boot':
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using Spring Boot @Value annotation or application.properties:
    -   BAD: private String apiKey = "sk_live_12345...";
    -   GOOD: @Value("${{api.key}}") private String apiKey;
    -   OR in application.properties: api.key=${{API_KEY:default_value}}
    -   OR: private String apiKey = System.getenv("API_KEY");
3.  For secrets, use @Value("${{app.secret}}") and define in application.yml
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using environment variables or System properties:
    -   BAD: String apiKey = "sk_live_12345...";
    -   GOOD: String apiKey = System.getenv("API_KEY");
    -   OR: String apiKey = System.getProperty("api.key");
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sql_injection':
        if framework == 'spring-boot':
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using Spring Data JPA (preferred) or PreparedStatement:
    -   BAD: jdbcTemplate.query("SELECT * FROM users WHERE name = '" + name + "'")
    -   GOOD: userRepository.findByName(name);  // Spring Data JPA
    -   OR: jdbcTemplate.query("SELECT * FROM users WHERE name = ?", new Object[]{{name}}, rowMapper)
    -   OR: PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE name = ?"); ps.setString(1, name);
3.  NEVER use string concatenation for SQL queries. Always use ? placeholders.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using PreparedStatement with ? placeholders:
    -   BAD: Statement stmt = conn.createStatement(); stmt.executeQuery("SELECT * FROM users WHERE name = '" + name + "'")
    -   GOOD: 
        PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE name = ?");
        ps.setString(1, name);
        ResultSet rs = ps.executeQuery();
3.  Use parameterized queries with ? placeholders.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'command_injection':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Command Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Command Injection.
2.  Fix using ProcessBuilder with list arguments:
    -   BAD: Runtime.getRuntime().exec("ping -c 1 " + host)
    -   GOOD: 
        ProcessBuilder pb = new ProcessBuilder("ping", "-c", "1", host);
        Process p = pb.start();
3.  NEVER use Runtime.exec() with string concatenation. Always use ProcessBuilder with separate arguments.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'path_traversal':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Path Traversal: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Path Traversal vulnerability.
2.  Fix using Paths.get() and Path.normalize():
    -   BAD: String filePath = "/app/static/" + userInput
    -   GOOD: 
        Path baseDir = Paths.get("/app/static");
        Path userPath = Paths.get(userInput).normalize();
        Path safePath = baseDir.resolve(userPath.getFileName());
        if (!safePath.startsWith(baseDir.normalize().toAbsolutePath())) {{
            throw new SecurityException("Invalid path");
        }}
3.  You MUST use java.nio.file.Paths and Path for path handling.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'cors':
        if framework == 'spring-boot':
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix using Spring @CrossOrigin or WebMvcConfigurer:
    -   BAD: response.setHeader("Access-Control-Allow-Origin", "*")
    -   GOOD:
        @CrossOrigin(origins = "${{allowed.origin}}")  // Controller level
        OR:
        @Configuration
        public class CorsConfig implements WebMvcConfigurer {{
            @Override
            public void addCorsMappings(CorsRegistry registry) {{
                registry.addMapping("/**")
                    .allowedOrigins(System.getenv("ALLOWED_ORIGIN"));
            }}
        }}
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix by replacing wildcard with environment variable:
    -   BAD: response.setHeader("Access-Control-Allow-Origin", "*")
    -   GOOD: response.setHeader("Access-Control-Allow-Origin", System.getenv("ALLOWED_ORIGIN"))
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sensitive_data':
        return f"""
THE VULNERABILITY:
A Semgrep scan found sensitive data leak: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* sensitive data leak (e.g., logging password, token).
2.  Fix by removing sensitive information:
    -   BAD: logger.info("Login failed for " + user + " with password " + password)
    -   GOOD: logger.info("Login failed for user: " + user)
    -   BAD: return ResponseEntity.status(500).body(err.getMessage())  # where err contains sensitive data
    -   GOOD: return ResponseEntity.status(500).body("Internal server error")
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""
    
    else:  # default
        return f"""
THE VULNERABILITY:
A Semgrep scan found this issue: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate and fix *only* this one specific vulnerability using Java best practices.
2.  You MUST NOT fix any other bugs in the file.
3.  Return the *ENTIRE* corrected Java file.
FULL FIXED CODE:
"""

def _get_csharp_task_prompt(framework, vuln_type, issue, snippet, line):
    """C#-specific task prompts (.NET)."""
    expert_name = f"C# (.NET) {vuln_type.replace('_', ' ').title()} Expert"
    print(f"ℹ️  (Fixer): Selected '{expert_name}'")
    
    if vuln_type == 'secret':
        if framework == 'dotnet':
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using .NET Configuration or environment variables:
    -   BAD: string apiKey = "sk_live_12345...";
    -   GOOD: string apiKey = Configuration["ApiKey"];  // appsettings.json
    -   OR: string apiKey = Environment.GetEnvironmentVariable("API_KEY");
    -   OR in appsettings.json: "ApiKey": "${{API_KEY}}"
3.  For secrets, use User Secrets or Azure Key Vault in production.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using environment variables:
    -   BAD: string apiKey = "sk_live_12345...";
    -   GOOD: string apiKey = Environment.GetEnvironmentVariable("API_KEY");
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sql_injection':
        if framework == 'dotnet':
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using Entity Framework Core (preferred) or parameterized queries:
    -   BAD: db.Database.ExecuteSqlRaw($"SELECT * FROM Users WHERE Name = '{{name}}'")
    -   GOOD: db.Users.Where(u => u.Name == name).ToList();  // EF Core
    -   OR: var users = db.Database.ExecuteSqlRaw("SELECT * FROM Users WHERE Name = {{0}}", name);
    -   OR: using var cmd = new SqlCommand("SELECT * FROM Users WHERE Name = @name", conn);
          cmd.Parameters.AddWithValue("@name", name);
3.  NEVER use string interpolation ($"...") for SQL. Use EF Core or @parameters.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using SqlCommand with @parameters:
    -   BAD: string sql = $"SELECT * FROM Users WHERE Name = '{{name}}'";
    -   GOOD: 
        string sql = "SELECT * FROM Users WHERE Name = @name";
        using var cmd = new SqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("@name", name);
3.  Use @parameterName for SQL Server parameters.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'command_injection':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Command Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Command Injection.
2.  Fix using ProcessStartInfo with separate arguments:
    -   BAD: Process.Start($"ping -c 1 {{host}}") or Process.Start("sh", "-c", $"ping {{host}}")
    -   GOOD: 
        ProcessStartInfo psi = new ProcessStartInfo {{
            FileName = "ping",
            Arguments = $"-c 1 {{host}}",
            UseShellExecute = false
        }};
        Process.Start(psi);
3.  Set UseShellExecute = false to prevent shell interpretation.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'path_traversal':
        return f"""
THE VULNERABILITY:
A Semgrep scan found Path Traversal: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Path Traversal vulnerability.
2.  Fix using Path.Combine and Path.GetFullPath:
    -   BAD: string filePath = "/app/static/" + userInput
    -   GOOD: 
        string baseDir = "/app/static";
        string fileName = Path.GetFileName(userInput);
        string safePath = Path.Combine(baseDir, fileName);
        string fullPath = Path.GetFullPath(safePath);
        if (!fullPath.StartsWith(Path.GetFullPath(baseDir))) {{
            throw new SecurityException("Invalid path");
        }}
3.  You MUST use System.IO.Path for path handling.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'cors':
        if framework == 'dotnet':
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix using .NET CORS middleware in Startup.cs or Program.cs:
    -   BAD: context.Response.Headers.Add("Access-Control-Allow-Origin", "*")
    -   GOOD:
        // In Startup.cs or Program.cs:
        services.AddCors(options => {{
            options.AddPolicy("AllowOrigin", policy => {{
                policy.WithOrigins(Configuration["AllowedOrigin"] ?? Environment.GetEnvironmentVariable("ALLOWED_ORIGIN"));
            }});
        }});
        app.UseCors("AllowOrigin");
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
        else:
            return f"""
THE VULNERABILITY:
A Semgrep scan found weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix by replacing wildcard with environment variable:
    -   BAD: response.Headers.Add("Access-Control-Allow-Origin", "*")
    -   GOOD: response.Headers.Add("Access-Control-Allow-Origin", Environment.GetEnvironmentVariable("ALLOWED_ORIGIN"))
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sensitive_data':
        return f"""
THE VULNERABILITY:
A Semgrep scan found sensitive data leak: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* sensitive data leak (e.g., logging password, token).
2.  Fix by removing sensitive information:
    -   BAD: logger.LogInformation($"Login failed for {{user}} with password {{password}}")
    -   GOOD: logger.LogInformation($"Login failed for user: {{user}}")
    -   BAD: return StatusCode(500, err.Message)  # where err contains sensitive data
    -   GOOD: return StatusCode(500, "Internal server error")
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""
    
    else:  # default
        return f"""
THE VULNERABILITY:
A Semgrep scan found this issue: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate and fix *only* this one specific vulnerability using C# best practices.
2.  You MUST NOT fix any other bugs in the file.
3.  Return the *ENTIRE* corrected C# file.
FULL FIXED CODE:
"""

def _get_go_task_prompt(vuln_type, issue, snippet, line):
    """Go-specific task prompts."""
    expert_name = f"Go {vuln_type.replace('_', ' ').title()} Expert"
    print(f"ℹ️  (Fixer): Selected '{expert_name}'")
    
    if vuln_type == 'secret':
        return f"""
THE VULNERABILITY:
A Gitleaks scan found a hardcoded secret: "{issue}"
This secret is on or near line {line}.
The secret's value is: {snippet}
Your task:
1.  Locate this *one* hardcoded secret.
2.  Fix using environment variables or config loader:
    -   BAD: var adminPassword = "sk_live_12345..."
    -   GOOD: var adminPassword = os.Getenv("ADMIN_PASSWORD")
    -   BETTER: var adminPassword = config.Get("ADMIN_PASSWORD")
3.  You MUST ensure the "os" package is imported if you use `os.Getenv()`.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Go file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'command_injection':
        return f"""
THE VULNERABILITY:
A Semgrep scan found a Command Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Command Injection.
2.  Fix by splitting the command from its arguments:
    -   BAD: exec.Command("sh", "-c", "ping -c 1 " + host)
    -   GOOD: exec.Command("ping", "-c", "1", host)
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Go file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sql_injection':
        return f"""
THE VULNERABILITY:
A Semgrep scan found an SQL Injection: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* SQL Injection.
2.  Fix using parameterized queries (with a `?` placeholder):
    -   BAD: db.Query("...WHERE id = '" + userID + "'")
    -   GOOD: db.Query("...WHERE id = ?", userID)
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Go file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'path_traversal':
        return f"""
THE VULNERABILITY:
A Semgrep scan found a Path Traversal: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* Path Traversal vulnerability.
2.  Fix it by cleaning the path and ensuring it's relative to a safe base directory:
    -   You MUST use `filepath.Clean()` on the user-provided path.
    -   You MUST check that the cleaned path is still within an allowed base directory.
    -   Example: path := filepath.Clean("/app/static/" + userInput)
    -   Example check: if !strings.HasPrefix(path, "/app/static/") {{ // handle error }}
3.  You MUST ensure "path/filepath" and "strings" are imported.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Go file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'cors':
        return f"""
THE VULNERABILITY:
A Semgrep scan found a weak CORS policy: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* CORS vulnerability.
2.  Fix it by replacing the wildcard `*` with a *configurable allowlist*:
    -   BAD: w.Header().Set("Access-Control-Allow-Origin", "*")
    -   GOOD:
        allowedOrigin := os.Getenv("ALLOWED_ORIGIN")
        if r.Header.Get("Origin") == allowedOrigin {{
            w.Header().Set("Access-Control-Allow-Origin", allowedOrigin)
        }}
3.  You MUST ensure "os" is imported.
4.  You MUST NOT fix any other bugs.
5.  Return the *ENTIRE* corrected Go file.
FULL FIXED CODE:
"""
    
    elif vuln_type == 'sensitive_data':
        return f"""
THE VULNERABILITY:
A Semgrep scan found a sensitive data leak: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate this *one* sensitive data leak (e.g., logging a password, token, or error).
2.  Fix it by removing the sensitive variable from the log or error message:
    -   BAD: log.Printf("Failed login for user: %s, password: %s", user, pass)
    -   GOOD: log.Printf("Failed login for user: %s", user)
    -   BAD: http.Error(w, err.Error(), 500)
    -   GOOD: http.Error(w, "Internal server error", 500)
3.  You MUST NOT fix any other bugs.
4.  Return the *ENTIRE* corrected Go file.
FULL FIXED CODE:
"""
    
    else:  # default
        return f"""
THE VULNERABILITY:
A Semgrep scan found this issue: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate and fix *only* this one specific vulnerability using Go best practices.
2.  You MUST NOT fix any other bugs in the file.
3.  Return the *ENTIRE* corrected Go file.
FULL FIXED CODE:
"""

def _get_generic_task_prompt(vuln_type, issue, snippet, line):
    """Generic task prompt for unknown languages."""
    print(f"ℹ️  (Fixer): Selected 'Generic {vuln_type.replace('_', ' ').title()} Expert'")
    return f"""
THE VULNERABILITY:
A Semgrep scan found this issue: "{issue}"
It is on or near line {line}.
The vulnerable code snippet is:
{snippet}
Your task:
1.  Locate and fix *only* this one specific vulnerability.
2.  You MUST NOT fix any other bugs in the file.
3.  Return the *ENTIRE* corrected file.
FULL FIXED CODE:
"""

def run_fixer_agent(full_code, finding):
    if not GROQ_API_KEY:
        print("❌ (Fixer): GROQ_API_KEY not set.")
        return None # <-- MODIFIED: Return None

    print(f"🤖 (Fixer): Analyzing finding to select expert prompt...")

    check_id = finding.get('check_id', '')
    issue = finding.get('message', 'Unknown issue')
    snippet = finding.get('snippet', 'N/A')
    line = finding.get('line', 0)
    file_path = finding.get('path', 'the file')
    
    # Detect language and framework
    language, framework = detect_language_from_path(file_path)
    lang_display = get_language_name(language, framework)
    print(f"🌐 (Fixer): Detected language: {lang_display}")
    
    # Get language-specific base prompt
    base_prompt = _get_base_prompt(file_path, language, framework, full_code)
    
    # --- Pro-Tier Fix Router (Language-Aware) ---
    vuln_type = _determine_vulnerability_type(check_id, issue, finding.get('tool', ''))
    
    # Get language-specific task prompt
    task_prompt = _get_language_specific_task_prompt(
        language, framework, vuln_type, check_id, issue, snippet, line
    )
    
    final_prompt = base_prompt + task_prompt
    print(f"🤖 (Fixer): Sending prompt to Groq ({GROQ_MODEL})...")
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": final_prompt}],
            model=GROQ_MODEL, 
            max_tokens=8192,
            temperature=0.0
        )

        fixed_code = chat_completion.choices[0].message.content.strip()
        print("✅ (Fixer): Fix generated.")

        # Clean up potential markdown fences (support all languages)
        lang_map = {
            'python': ['```python', '```py'],
            'javascript': ['```javascript', '```js', '```jsx', '```typescript', '```ts', '```tsx'],
            'java': ['```java'],
            'csharp': ['```csharp', '```cs'],
            'go': ['```go']
        }
        extensions = lang_map.get(language, [])
        for ext in extensions:
            if fixed_code.startswith(ext):
                fixed_code = fixed_code[len(ext):]
        if fixed_code.startswith("```"):
            fixed_code = fixed_code[3:]
        if fixed_code.endswith("```"):
            fixed_code = fixed_code[:-3]
        
        fixed_code = fixed_code.strip()

        if not fixed_code:
            print(f"⚠️ (Fixer): Groq returned an empty fix.")
            return None # <-- MODIFIED
        
        # --- MODIFIED: Return the code, don't write to file ---
        return fixed_code
        
    except Exception as e:
        print(f"❌ (Fixer): Error: {e}")
        return None # <-- MODIFIED