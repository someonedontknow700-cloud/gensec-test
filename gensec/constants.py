import os
import hashlib

# --- FILE CONFIGURATION ---
# VULNERABLE_FILE_PATH = "vulnerable_app.go"  <-- DELETE THIS
REPORT_FILE = "report.json"
# FIXED_FILE_PATH = "fixed_app.go"            <-- DELETE THIS

# Generate unique workspace directory per repository to avoid conflicts when running multiple agents
def get_workspace_dir(repo_name=None):
    """
    Get workspace directory for a repository.
    Each repository gets its own workspace to allow parallel execution.
    """
    if repo_name:
        # Create unique directory name from repo name
        # Replace / with - and hash to ensure uniqueness
        safe_name = repo_name.replace('/', '-').replace('\\', '-')
        # Use short hash to avoid long paths on Windows
        repo_hash = hashlib.md5(repo_name.encode()).hexdigest()[:8]
        return f"workspace-{safe_name}-{repo_hash}"
    return "workspace"  # Default fallback

# For backward compatibility, get workspace from environment or repo
GITHUB_REPOS_ENV = os.environ.get("GITHUB_REPOS", "")
if GITHUB_REPOS_ENV:
    # Take first repo from list for default workspace
    first_repo = GITHUB_REPOS_ENV.split(',')[0].strip()
    WORKSPACE_DIR = get_workspace_dir(first_repo)
else:
    WORKSPACE_DIR = "workspace"

# --- API KEY CONFIGURATION ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- MULTI-REPO CONFIG ---
GITHUB_REPOS = os.environ.get("GITHUB_REPOS", "shivansh-source/gensec-test-repo").split(',')

# Default user plan
USER_PLAN = os.environ.get("USER_PLAN", "free").lower()
if USER_PLAN not in ["free", "pro", "enterprise"]:
    USER_PLAN = "free"