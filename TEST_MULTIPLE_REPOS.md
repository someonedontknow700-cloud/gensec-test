# Testing Multiple Repositories

This guide shows you how to test the GenSec agent with multiple repositories running in parallel.

## ✅ What's Fixed

The agent now uses **unique workspace directories** for each repository, allowing multiple agent instances to run in parallel without file locking conflicts:

- **Repository 1** → `workspace-shivansh-source-gensec-test-cmd-3f531442`
- **Repository 2** → `workspace-shivansh-source-gensec-test-secret-0e991ddd`

Each repository gets its own isolated workspace, so they can run simultaneously.

## 🚀 Quick Test

### Option 1: Using the Test Script (Recommended)

**Windows PowerShell:**
```powershell
python test_multiple_repos.py
```

**Linux/Mac:**
```bash
python test_multiple_repos.py
```

This script automatically runs both repositories in parallel:
- `shivansh-source/gensec-test-cmd`
- `shivansh-source/gensec-test-secret`

### Option 2: Using GitHub Actions Workflow

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **GenSec Agent - Self-Healing** workflow
4. Click **Run workflow**
5. The workflow will automatically create separate agent instances for each repository in the matrix

The workflow matrix (in `.github/workflows/gensec.yml`) defines which repositories to scan:

```yaml
matrix:
  repo: 
    - 'shivansh-source/gensec-test-cmd'
    - 'shivansh-source/gensec-test-secret'
```

### Option 3: Manual Testing (One at a Time)

**Terminal 1:**
```bash
export GITHUB_TOKEN="your_token"
export GROQ_API_KEY="your_key"
export USER_PLAN="free"
export GITHUB_REPOS="shivansh-source/gensec-test-cmd"
python main.py
```

**Terminal 2:**
```bash
export GITHUB_TOKEN="your_token"
export GROQ_API_KEY="your_key"
export USER_PLAN="free"
export GITHUB_REPOS="shivansh-source/gensec-test-secret"
python main.py
```

## 📊 What to Expect

When running multiple repositories in parallel, you should see:

1. **Each repository gets its own workspace:**
   ```
   [shivansh-source/gensec-test-cmd] 📁 Workspace: workspace-shivansh-source-gensec-test-cmd-3f531442
   [shivansh-source/gensec-test-secret] 📁 Workspace: workspace-shivansh-source-gensec-test-secret-0e991ddd
   ```

2. **Both agents run independently:**
   - Agent 1 scans `gensec-test-cmd` → Creates PRs → Loops until fixed
   - Agent 2 scans `gensec-test-secret` → Creates PRs → Loops until fixed

3. **No conflicts:**
   - Each workspace is isolated
   - No file locking issues
   - Both can scan/fix/create PRs simultaneously

## 🔧 Customizing Repositories

To test different repositories, edit `test_multiple_repos.py`:

```python
# Repositories to test
REPOSITORIES = [
    "your-username/your-repo-1",
    "your-username/your-repo-2",
    "your-username/your-repo-3"
]
```

Or modify the GitHub Actions workflow matrix:

```yaml
matrix:
  repo: 
    - 'your-username/your-repo-1'
    - 'your-username/your-repo-2'
    - 'your-username/your-repo-3'
```

## ⚠️ Notes

- **Windows file locking:** On Windows, you may see warnings about file locking during cleanup. This is **non-critical** - the workspace will be cleaned on the next run.
- **Workspace directories:** Each repository's workspace is automatically cleaned up after each iteration, but if cleanup fails, the next iteration will handle it.
- **Parallel execution:** Each agent instance runs completely independently - failures in one repo don't affect others.

## ✅ Verification Checklist

- [ ] Both repositories start scanning simultaneously
- [ ] Each repository uses its own unique workspace directory
- [ ] No file locking conflicts between repositories
- [ ] Each agent creates PRs independently
- [ ] Both agents loop until their respective repositories are secure
- [ ] Agents complete successfully (exit code 0)

## 🐛 Troubleshooting

**Issue: File locking errors on Windows**
- **Solution:** This is expected and non-critical. The workspace will be cleaned on the next iteration.

**Issue: Both agents try to use the same workspace**
- **Solution:** Make sure you're using the latest version with unique workspace directories per repository.

**Issue: One agent fails but the other continues**
- **Solution:** This is expected behavior - each agent is independent. Check the logs for the failing agent.

