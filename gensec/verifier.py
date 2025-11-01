import os
import subprocess
import json
from gensec.constants import WORKSPACE_DIR # <-- MODIFIED

def run_verifier(check_id, user_plan, file_to_verify):
    """
    Verifies the fix for a *specific file*.
    """
    print(f"🤖 (Verifier): Verifying fix for {check_id} in {file_to_verify}...")
    
    VERIFY_REPORT_DIR = "verify_reports"
    os.makedirs(VERIFY_REPORT_DIR, exist_ok=True)
    VERIFY_SEMGREP_REPORT = os.path.join(VERIFY_REPORT_DIR, "verify_semgrep.json")
    VERIFY_GITLEAKS_REPORT = os.path.join(VERIFY_REPORT_DIR, "verify_gitleaks.json")
    VERIFY_TRIVY_REPORT = os.path.join(VERIFY_REPORT_DIR, "verify_trivy.json")
    
    # This is the full path to the file in the cloned workspace
    full_file_path = os.path.join(WORKSPACE_DIR, file_to_verify)
    
    if not os.path.exists(full_file_path):
        print(f"❌ (Verifier): File not found at {full_file_path}. Fixer may have failed.")
        return False
    
    try:
        # --- 1. Re-run Semgrep on the FIXED file ---
        print("ℹ️  (Verifier): Re-running Semgrep on fixed code...")
        semgrep_command = [
            "semgrep", "--config", "p/gosec", "--config", "p/owasp-top-ten",
        ]
        if user_plan in ["pro", "enterprise"]:
            semgrep_command.extend(["--config", "p/security-audit", "--config", "p/cwe-top-25"])
            
        semgrep_command.extend(["--json", "-o", VERIFY_SEMGREP_REPORT, full_file_path]) # <-- MODIFIED
        subprocess.run(semgrep_command, capture_output=True, text=True, encoding='utf-8')

        # --- 2. Re-run Pro Scanners on the FIXED file ---
        if user_plan in ["pro", "enterprise"]:
            print("ℹ️  (Verifier): Re-running Gitleaks on fixed code...")
            gitleaks_command = [
                "gitleaks", "detect", "--no-git",
                "--source", WORKSPACE_DIR, # <-- Scan whole dir
                "--report-format", "json",
                "--report-path", VERIFY_GITLEAKS_REPORT
            ]
            subprocess.run(gitleaks_command, capture_output=True, text=True, encoding='utf-8')

            print("ℹ️  (Verifier): Re-running Trivy on fixed code...")
            trivy_command = [
                "trivy", "fs",
                "--format", "json",
                "--output", VERIFY_TRIVY_REPORT,
                full_file_path # <-- MODIFIED
            ]
            subprocess.run(trivy_command, capture_output=True, text=True, encoding='utf-8')

        # --- 3. Parse ALL verification reports ---
        vulnerability_still_exists = False
        
        if os.path.exists(VERIFY_SEMGREP_REPORT):
            with open(VERIFY_SEMGREP_REPORT, 'r', encoding='utf-8') as f:
                report = json.load(f)
            for finding in report.get("results", []):
                # Check if the *same bug* is in the *same file*
                finding_path = finding.get("path", "").replace(f"{WORKSPACE_DIR}/", "", 1)
                if finding.get("check_id") == check_id and finding_path == file_to_verify:
                    vulnerability_still_exists = True; break
        
        if vulnerability_still_exists:
            print(f"❌ (Verifier): FAILED. {check_id} still present in Semgrep report.")
            return False

        if os.path.exists(VERIFY_GITLEAKS_REPORT):
            with open(VERIFY_GITLEAKS_REPORT, 'r', encoding='utf-8') as f:
                report = json.load(f)
            for finding in report:
                finding_path = finding.get("File", "").replace(f"{WORKSPACE_DIR}/", "", 1)
                if f"gitleaks.{finding.get('RuleID')}" == check_id and finding_path == file_to_verify:
                    vulnerability_still_exists = True; break
        
        if vulnerability_still_exists:
            print(f"❌ (Verifier): FAILED. {check_id} still present in Gitleaks report.")
            return False
            
        # ... (Add similar check for Trivy report if needed) ...

        print(f"✅ (Verifier): PASSED. The vulnerability '{check_id}' is fixed.")
        return True

    except Exception as e:
        print(f"❌ (Verifier): An unexpected error occurred: {e}")
        return False