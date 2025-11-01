import os
import sys
from gensec import github_utils, scanner, parser, fixer, verifier, constants
import time
import shutil

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    import io
    import codecs
    # Set UTF-8 encoding for stdout/stderr on Windows
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def scan_single_repo_iteration(repo_name, user_plan):
    """
    Single scan iteration for a repository.
    Fresh clone automatically shows current state (merged PRs are included).
    
    Returns:
        (success: bool, finding: dict, pr_url: str, error: str, should_continue: bool)
        should_continue: True if we should continue looping, False if done
    """
    user_plan = user_plan.lower()
    if user_plan not in ["free", "pro", "enterprise"]:
        user_plan = "free"
    
    finding = None
    pr_url = None
    error = None
    
    try:
        # 1. CLONE (fresh clone shows current state - merged PRs are automatically included)
        print(f"\n{'='*60}")
        print(f"🔄 Iteration: Scanning {repo_name}")
        print(f"{'='*60}")
        print(f"📥 Cloning repository (fresh clone shows merged PRs)...", flush=True)
        result = github_utils.clone_repo(repo_name)
        if not result or len(result) < 3:
            error = f"Failed to clone {repo_name}"
            print(f"❌ {error}", flush=True)
            return (False, None, None, error, False)
        
        repo, original_sha, workspace_dir = result
        if not repo or not original_sha:
            error = f"Failed to clone {repo_name}"
            print(f"❌ {error}", flush=True)
            return (False, None, None, error, False)
        
        print(f"✅ Repository cloned successfully", flush=True)
        print(f"📁 Workspace: {workspace_dir}", flush=True)
        
        # 2. SCAN
        print(f"🔍 Running security scanners...", flush=True)
        if not scanner.run_scanner(user_plan):
            print(f"🎉 No vulnerabilities found in {repo_name}!", flush=True)
            print(f"✅ Repository is secure - all vulnerabilities fixed!", flush=True)
            return (True, None, None, None, False)  # Success - stop looping
        
        print(f"✅ Scan completed. Vulnerabilities found.", flush=True)
        
        # 3. PARSE
        print(f"📊 Analyzing scan results...", flush=True)
        finding = parser.get_vulnerability_info()
        if not finding:
            error = "Parser failed - no findings extracted"
            print(f"❌ {error}", flush=True)
            return (False, None, None, error, True)  # Continue despite parser error
        
        print(f"✅ Highest priority vulnerability identified:", flush=True)
        print(f"   🔴 Check ID: {finding['check_id']}", flush=True)
        print(f"   📄 File: {finding['path']}", flush=True)
        print(f"   📍 Line: {finding['line']}", flush=True)
        print(f"   💬 Message: {finding['message'][:100]}...", flush=True)
        
        # Check if a PR already exists for this exact vulnerability
        # (Same file and same check_id means same vulnerability)
        try:
            has_open_pr, existing_pr_number = github_utils.has_open_gensec_pr(repo_name)
            if has_open_pr:
                print(f"⏸️  GenSec PR #{existing_pr_number} is already OPEN for a vulnerability", flush=True)
                print(f"    Waiting for it to be merged... (fresh clone will show merge status)", flush=True)
                return (True, None, None, None, True)  # Continue - wait for merge
        except Exception as e:
            print(f"⚠️  Could not check for existing PRs: {e}. Proceeding anyway...", flush=True)
        
        # Read vulnerable file
        vulnerable_file_path = finding['path']
        full_local_path = os.path.join(constants.WORKSPACE_DIR, vulnerable_file_path)
        
        try:
            with open(full_local_path, 'r', encoding='utf-8') as f:
                full_code = f.read()
        except Exception as e:
            error = f"Error reading {vulnerable_file_path}: {e}"
            print(f"❌ {error}", flush=True)
            return (False, finding, None, error, True)
        
        vuln_id = finding['check_id']
        vuln_message = finding['message']
        
        # 4. FIX
        print(f"🔧 Generating AI-powered fix...", flush=True)
        fixed_code = fixer.run_fixer_agent(full_code, finding)
        if not fixed_code:
            error = "Fixer agent failed to generate fix"
            print(f"❌ {error}", flush=True)
            return (False, finding, None, error, True)
        
        print(f"✅ Fix generated successfully", flush=True)
        
        # Write fix to file
        try:
            with open(full_local_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            print(f"💾 Fix written to {vulnerable_file_path}", flush=True)
        except Exception as e:
            error = f"Error writing fix: {e}"
            print(f"❌ {error}", flush=True)
            return (False, finding, None, error, True)
        
        # 5. VERIFY
        print(f"✔️  Verifying that fix resolves vulnerability...", flush=True)
        if not verifier.run_verifier(vuln_id, user_plan, vulnerable_file_path):
            error = "Verification failed - fix does not resolve vulnerability"
            print(f"❌ {error}", flush=True)
            return (False, finding, None, error, True)
        
        print(f"✅ Verification passed - fix is valid", flush=True)
        
        # 6. CREATE PR
        print(f"📝 Creating pull request...", flush=True)
        pr = github_utils.create_github_pull_request(
            repo=repo,
            original_sha=original_sha,
            message=vuln_message,
            file_path=vulnerable_file_path,
            fixed_code_content=fixed_code
        )
        
        if not pr:
            error = "Failed to create pull request"
            print(f"❌ {error}", flush=True)
            return (False, finding, None, error, True)
        
        pr_url = pr.html_url
        pr_number = pr.number
        print(f"🎉 PR #{pr_number} created successfully: {pr_url}", flush=True)
        print(f"{'='*60}")
        
        return (True, finding, pr_url, None, True)  # Success - continue looping
        
    except Exception as e:
        error = f"Unexpected error: {str(e)}"
        print(f"❌ {error}", flush=True)
        import traceback
        traceback.print_exc()
        return (False, finding, None, error, True)
    
    finally:
        # Clean up workspace using robust cleanup
        workspace_to_clean = locals().get('workspace_dir', None) or constants.WORKSPACE_DIR
        if workspace_to_clean and os.path.exists(workspace_to_clean):
            github_utils.robust_cleanup_workspace(workspace_to_clean)

def main():
    """
    Main entry point with continuous loop.
    Each agent instance handles ONE repository and loops continuously until all vulnerabilities are fixed.
    
    Loop logic:
    - Fresh clone each iteration shows current state (merged PRs are automatically included)
    - If vulnerability found → create PR → wait (small delay) → clone again → check again
    - If no vulnerabilities found → stop (all fixed!)
    - If PR exists for same vulnerability → wait → clone again → check if merged
    """
    user_plan = constants.USER_PLAN
    if not constants.GROQ_API_KEY or not constants.GITHUB_TOKEN:
        print("❌ Missing GROQ_API_KEY or GITHUB_TOKEN.")
        sys.exit(1)
    
    print(f"ℹ️  Using Groq model: {constants.GROQ_MODEL}")
    
    # Get the single repository to scan
    repos_list = constants.GITHUB_REPOS
    if not repos_list or len(repos_list) == 0:
        print("❌ No repository specified in GITHUB_REPOS")
        sys.exit(1)
    
    # Each agent instance handles ONE repo
    repo_name = repos_list[0]
    
    print(f"\n{'='*80}")
    print(f"🤖 GenSec Agent - Continuous Loop Mode")
    print(f"{'='*80}")
    print(f"📋 Repository: {repo_name}")
    print(f"📦 Plan: {user_plan}")
    print(f"🔄 Mode: Continuous loop until all vulnerabilities are fixed")
    print(f"💡 Logic: Fresh clone each iteration shows merged PRs automatically")
    print(f"{'='*80}\n")
    
    # Continuous loop until all vulnerabilities are fixed
    iteration = 0
    max_iterations = 1000  # Safety limit (shouldn't reach this)
    loop_delay = 60  # 1 minute between iterations (allows time for PR merge)
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'#'*80}")
        print(f"# Iteration {iteration}")
        print(f"{'#'*80}")
        
        # Run one scan iteration
        success, finding, pr_url, error, should_continue = scan_single_repo_iteration(repo_name, user_plan)
        
        if not should_continue:
            # No vulnerabilities found - we're done!
            print(f"\n{'='*80}")
            print(f"✅ SUCCESS: All vulnerabilities fixed in {repo_name}!")
            print(f"{'='*80}")
            print(f"📊 Total iterations: {iteration}")
            print(f"🎉 Repository is now secure!")
            print(f"{'='*80}\n")
            sys.exit(0)
        
        if success and pr_url:
            print(f"✅ PR created: {pr_url}")
            print(f"⏳ Waiting {loop_delay} seconds before next scan (allows time for PR merge)...")
            time.sleep(loop_delay)
        elif success and not pr_url:
            # Open PR exists for same vulnerability - wait and check again
            print(f"⏳ Waiting {loop_delay} seconds before checking again...")
            time.sleep(loop_delay)
        elif error:
            print(f"⚠️  Error: {error}")
            print(f"⏳ Retrying in {loop_delay} seconds...")
            time.sleep(loop_delay)
    
    # Safety limit reached
    print(f"\n⚠️  Maximum iterations ({max_iterations}) reached. Stopping.")
    sys.exit(1)


if __name__ == "__main__":
    main()