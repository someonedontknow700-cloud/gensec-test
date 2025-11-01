# GitHub Actions Setup Guide

## Setup Instructions

### 1. Push Code to Your Repository

```bash
cd /home/vivek/Downloads/gensec-backup

# Initialize git if needed
git init

# Add your repository as remote (replace with your repo)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Or if already exists, update it
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Add all files
git add .

# Commit
git commit -m "Add GenSec security scanner with GitHub Actions"

# Push to GitHub
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to your repository on GitHub:
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

#### Required Secrets:

**GROQ_API_KEY**
your-groq-api-key-here

**GITHUB_TOKEN** (Optional - GitHub provides this automatically)
- GitHub automatically provides `GITHUB_TOKEN` for workflows
- If you need custom permissions, create a Personal Access Token:
{{ ... }}
  - Generate new token (classic)
  - Select scopes: `repo` (full control)
  - Copy the token and add as secret named `GITHUB_TOKEN`

### 3. Enable GitHub Actions

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. If prompted, click **"I understand my workflows, go ahead and enable them"**

### 4. Run the Workflow

#### Manual Trigger:
1. Go to **Actions** tab
2. Click **GenSec Security Scanner** workflow
3. Click **Run workflow** button
4. Select branch (usually `main`)
5. Click **Run workflow**

#### Automatic Trigger:
- The workflow runs automatically daily at 2 AM (if schedule is enabled)
- You can modify the schedule in `.github/workflows/gensec-scan.yml`

### 5. View Results

After the workflow runs:
1. Go to **Actions** tab
2. Click on the workflow run
3. View the logs to see:
   - Vulnerabilities found
   - Fixes generated
   - Pull requests created
4. Download the scan report artifact

### 6. Review Pull Requests

The scanner will automatically create pull requests for each vulnerability:
1. Go to **Pull requests** tab
2. Review the AI-generated fixes
3. Merge the PRs to fix vulnerabilities
4. The scanner will automatically detect merged PRs and move to the next vulnerability

## Workflow Files

### Simple Workflow (Recommended)
- File: `.github/workflows/gensec-scan.yml`
- Scans the current repository
- Creates PRs for fixes
- Runs on manual trigger or schedule

### Advanced Multi-Repo Workflow
- File: `.github/workflows/gensec.yml`
- Scans multiple repositories in parallel
- Each repo gets its own agent instance
- Configure repositories in the `matrix` section

## Troubleshooting

### Workflow not showing up?
- Make sure the workflow file is in `.github/workflows/` directory
- Push the changes to GitHub
- Enable Actions in repository settings

### Workflow fails with "GROQ_API_KEY not found"?
- Add the `GROQ_API_KEY` secret in repository settings
- Make sure the secret name matches exactly

### No PRs created?
- Check if `GITHUB_TOKEN` has write permissions
- Repository settings → Actions → General → Workflow permissions
- Select "Read and write permissions"

### Scan times out?
- Increase timeout in workflow file: `timeout 600 python main.py`
- Or remove timeout for unlimited scanning

## Configuration

### Scan Different Repository

Edit `.github/workflows/gensec-scan.yml`:
```yaml
env:
  GITHUB_REPOS: 'owner/different-repo'  # Change this
```

### Change Plan Tier

```yaml
env:
  USER_PLAN: 'pro'  # Options: free, pro, enterprise
```

### Adjust Schedule

```yaml
on:
  schedule:
    - cron: '0 8 * * 1'  # Every Monday at 8 AM
```

## Example: Quick Setup for Your Repository

```bash
# 1. Navigate to project
cd /home/vivek/Downloads/gensec-backup

# 2. Update git remote to YOUR repository
git remote set-url origin https://github.com/someonedontknow700-cloud/gensec-test.git

# 3. Push to GitHub
git add .
git commit -m "Add GenSec scanner with GitHub Actions"
git push -u origin main

# 4. Go to GitHub and add GROQ_API_KEY secret
# 5. Go to Actions tab and run the workflow
```

## Support

For issues or questions:
- Check the workflow logs in Actions tab
- Review the scan report artifacts
- Ensure all secrets are configured correctly
