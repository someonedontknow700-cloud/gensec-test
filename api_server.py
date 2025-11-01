from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import sys
from gensec import github_utils, scanner, parser, fixer, verifier, constants
import asyncio
from datetime import datetime
import uuid

app = FastAPI(title="GenSec API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for scan jobs
scan_jobs: Dict[str, Dict] = {}

class ScanRequest(BaseModel):
    repository: str
    user_plan: str = "free"
    github_token: Optional[str] = None
    groq_api_key: Optional[str] = None

class ScanStatus(BaseModel):
    job_id: str
    status: str
    repository: str
    user_plan: str
    started_at: str
    completed_at: Optional[str] = None
    iterations: int = 0
    current_iteration: int = 0
    vulnerabilities_found: int = 0
    prs_created: List[str] = []
    error: Optional[str] = None
    logs: List[str] = []

def add_log(job_id: str, message: str):
    """Add a log message to a job"""
    if job_id in scan_jobs:
        scan_jobs[job_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

async def run_scan_iteration(job_id: str, repo_name: str, user_plan: str):
    """Run a single scan iteration"""
    try:
        add_log(job_id, f"Starting iteration {scan_jobs[job_id]['current_iteration'] + 1}")
        add_log(job_id, f"Cloning repository: {repo_name}")
        
        # Clone repository
        result = github_utils.clone_repo(repo_name)
        if not result or len(result) < 3:
            raise Exception(f"Failed to clone {repo_name}")
        
        repo, original_sha, workspace_dir = result
        add_log(job_id, f"Repository cloned successfully to {workspace_dir}")
        
        # Run scanner
        add_log(job_id, "Running security scanners...")
        has_vulns = scanner.run_scanner(user_plan)
        
        if not has_vulns:
            add_log(job_id, "No vulnerabilities found! Repository is secure.")
            scan_jobs[job_id]["status"] = "completed"
            scan_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            return False  # No more iterations needed
        
        add_log(job_id, "Vulnerabilities detected, analyzing...")
        
        # Parse vulnerability
        finding = parser.get_vulnerability_info()
        if not finding:
            add_log(job_id, "Failed to parse vulnerability information")
            return True  # Continue to next iteration
        
        scan_jobs[job_id]["vulnerabilities_found"] += 1
        add_log(job_id, f"Found vulnerability: {finding['check_id']} in {finding['path']}")
        
        # Check for existing PR
        try:
            has_open_pr, existing_pr_number = github_utils.has_open_gensec_pr(repo_name)
            if has_open_pr:
                add_log(job_id, f"PR #{existing_pr_number} already exists, waiting for merge...")
                return True  # Continue to next iteration
        except Exception as e:
            add_log(job_id, f"Could not check for existing PRs: {e}")
        
        # Read vulnerable file
        vulnerable_file_path = finding['path']
        full_local_path = os.path.join(constants.WORKSPACE_DIR, vulnerable_file_path)
        
        with open(full_local_path, 'r', encoding='utf-8') as f:
            full_code = f.read()
        
        # Generate fix
        add_log(job_id, "Generating AI-powered fix...")
        fixed_code = fixer.run_fixer_agent(full_code, finding)
        if not fixed_code:
            add_log(job_id, "Failed to generate fix")
            return True
        
        add_log(job_id, "Fix generated successfully")
        
        # Write fix
        with open(full_local_path, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
        
        # Verify fix
        add_log(job_id, "Verifying fix...")
        if not verifier.run_verifier(finding['check_id'], user_plan, vulnerable_file_path):
            add_log(job_id, "Verification failed")
            return True
        
        add_log(job_id, "Verification passed")
        
        # Create PR
        add_log(job_id, "Creating pull request...")
        pr = github_utils.create_github_pull_request(
            repo=repo,
            original_sha=original_sha,
            message=finding['message'],
            file_path=vulnerable_file_path,
            fixed_code_content=fixed_code
        )
        
        if pr:
            pr_url = pr.html_url
            scan_jobs[job_id]["prs_created"].append(pr_url)
            add_log(job_id, f"PR created: {pr_url}")
        else:
            add_log(job_id, "Failed to create PR")
        
        return True  # Continue to next iteration
        
    except Exception as e:
        add_log(job_id, f"Error: {str(e)}")
        scan_jobs[job_id]["error"] = str(e)
        return True
    finally:
        # Cleanup
        workspace_to_clean = locals().get('workspace_dir', None) or constants.WORKSPACE_DIR
        if workspace_to_clean and os.path.exists(workspace_to_clean):
            github_utils.robust_cleanup_workspace(workspace_to_clean)

async def run_continuous_scan(job_id: str, repo_name: str, user_plan: str):
    """Run continuous scan loop"""
    max_iterations = 10  # Limit for safety
    
    scan_jobs[job_id]["status"] = "running"
    
    for iteration in range(max_iterations):
        scan_jobs[job_id]["current_iteration"] = iteration + 1
        
        should_continue = await run_scan_iteration(job_id, repo_name, user_plan)
        
        if not should_continue:
            break
        
        # Wait before next iteration
        await asyncio.sleep(5)
    
    if scan_jobs[job_id]["status"] == "running":
        scan_jobs[job_id]["status"] = "completed"
        scan_jobs[job_id]["completed_at"] = datetime.now().isoformat()

@app.get("/")
async def root():
    return {
        "message": "GenSec API Server",
        "version": "1.0.0",
        "endpoints": ["/scan", "/status/{job_id}", "/jobs"]
    }

@app.post("/scan", response_model=Dict)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new security scan"""
    
    # Set environment variables if provided
    if request.github_token:
        os.environ["GITHUB_TOKEN"] = request.github_token
    if request.groq_api_key:
        os.environ["GROQ_API_KEY"] = request.groq_api_key
    
    # Validate required environment variables
    if not os.environ.get("GITHUB_TOKEN") or not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="GITHUB_TOKEN and GROQ_API_KEY are required"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    scan_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "repository": request.repository,
        "user_plan": request.user_plan,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "iterations": 0,
        "current_iteration": 0,
        "vulnerabilities_found": 0,
        "prs_created": [],
        "error": None,
        "logs": []
    }
    
    # Start scan in background
    background_tasks.add_task(run_continuous_scan, job_id, request.repository, request.user_plan)
    
    return {
        "job_id": job_id,
        "message": "Scan started",
        "repository": request.repository
    }

@app.get("/status/{job_id}", response_model=ScanStatus)
async def get_scan_status(job_id: str):
    """Get status of a scan job"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return scan_jobs[job_id]

@app.get("/jobs")
async def list_jobs():
    """List all scan jobs"""
    return {
        "jobs": list(scan_jobs.values()),
        "total": len(scan_jobs)
    }

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    if job_id not in scan_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del scan_jobs[job_id]
    return {"message": "Job deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
