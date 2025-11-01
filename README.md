# GenSec Agent - Security Vulnerability Scanner & Auto-Fixer

## Architecture: One Agent Per Repository

**Important:** Each agent instance handles **ONE repository only**. This provides:
- **Isolation**: Failures in one repo don't affect others
- **Parallelization**: Multiple repos scan simultaneously via GitHub Actions matrix
- **Resource Efficiency**: Each agent focuses on a single repository
- **Better Monitoring**: Separate logs and status for each repository

### How It Works

1. **GitHub Actions Matrix**: Creates separate jobs for each repository in the matrix
2. **Each Job = One Agent**: Each job spawns an independent agent instance
3. **Single Repo Focus**: Each agent scans only its assigned repository
4. **Parallel Execution**: All agents run simultaneously (if using matrix strategy)

### Repository Configuration

Set repositories in `.github/workflows/gensec.yml`:
```yaml
matrix:
  repo: 
    - 'owner/repo-1'
    - 'owner/repo-2'
    - 'owner/repo-3'
```

Each repository gets its own agent instance.

### Environment Variables

Each agent instance requires:
- `GITHUB_REPOS`: Single repository (format: `owner/repo`)
- `USER_PLAN`: `free`, `pro`, or `enterprise`
- `GITHUB_TOKEN`: GitHub authentication token
- `GROQ_API_KEY`: Groq API key for AI-powered fixes

### Features

- ✅ Multi-language support (Python, JavaScript, Java, C#, Go)
- ✅ Framework-specific fixes (Django, Flask, FastAPI, React, Node.js, Spring Boot, .NET)
- ✅ Automatic PR creation with fixes
- ✅ Continuous loop until all vulnerabilities fixed
- ✅ Isolated agent instances per repository
- ✅ Pro-tier scanning (Gitleaks, Trivy, advanced Semgrep rules)

### Continuous Loop Behavior

**Each agent instance runs in a continuous loop until all vulnerabilities are fixed:**

**Key Insight**: Fresh clone each iteration automatically shows the current state:
- If PR was merged → Fresh clone includes the fix → Vulnerability is gone → Finds next one
- If PR is still open → Fresh clone shows same vulnerability → Checks if PR exists → Waits if exists

**Example Flow:**

1. **Iteration 1**:
   - Fresh clone → Sees current code
   - Scans → **Vulnerability #1 found** in `api/handlers.go`
   - Generates fix → **Creates PR #1**
   - Wait 1 minute → Next iteration

2. **Iteration 2** (PR #1 still open):
   - Fresh clone → Still sees vulnerability #1 (PR not merged yet)
   - Scans → **Same vulnerability found**
   - Checks → **PR #1 exists for this vulnerability**
   - **Waits** → Next iteration (small delay to allow merge)

3. **User merges PR #1** (during iteration 2)

4. **Iteration 3**:
   - Fresh clone → **Includes merged PR #1 fix** (automatically!)
   - Scans → **Vulnerability #1 is gone**, finds **Vulnerability #2** in `utils/validator.py`
   - Generates fix → **Creates PR #2**
   - Wait 1 minute → Next iteration

5. **Iteration 4** (PR #2 still open):
   - Fresh clone → Still sees vulnerability #2
   - Scans → **Same vulnerability found**
   - Checks → **PR #2 exists**
   - **Waits** → Next iteration

6. **User merges PR #2** → **Iteration 5**:
   - Fresh clone → **Includes merged PR #2 fix**
   - Scans → **Vulnerability #2 is gone**, finds **Vulnerability #3**
   - Creates **PR #3**
   - ... **Loop continues** ...

7. **Iteration N** (when all vulnerabilities are fixed):
   - Fresh clone → **Includes all merged fixes**
   - Scans → **No vulnerabilities found**
   - Message: "🎉 No vulnerabilities found! Repository is secure - stopping checks"
   - **Loop ends** ✅

### Loop Characteristics

- **Continuous**: Agent runs in a loop without waiting for scheduled triggers
- **Fresh Clone**: Each iteration does a fresh clone - automatically sees merged PRs
- **No Wait Time**: Loops immediately after PR creation (small delay for PR merge)
- **Self-Healing**: Automatically detects merged PRs via fresh clone → Finds next vulnerability
- **Stops When Secure**: Loop ends when scanner finds no vulnerabilities
- **Isolated**: Each repository's loop is independent (one agent per repo)
- **Parallel**: Multiple repos loop simultaneously, each handling its own repository

### Usage

**Via GitHub Actions:**
- Manual trigger via `workflow_dispatch` (recommended)
- Optional: Scheduled scan daily at 1 AM
- Each repo runs in parallel via matrix strategy
- **Each agent instance loops continuously for its repository until all vulnerabilities are fixed**
- Agent automatically detects merged PRs via fresh clone each iteration

**Via API/Backend:**
- Each backend request spawns a new agent instance for one repository
- Pass `GITHUB_REPOS` environment variable with single repo name
- Agent runs in continuous loop until all vulnerabilities fixed
- Fresh clone each iteration automatically shows merged PRs