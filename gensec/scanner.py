import os
import subprocess
import json
from gensec.constants import REPORT_FILE, WORKSPACE_DIR

def run_scanner(user_plan):
    print(f"🤖 (Scanner): Running scanners for plan: {user_plan} on {WORKSPACE_DIR}...")
    try:
        # Clean up old reports
        for f in [REPORT_FILE, "report-gitleaks.json", "report-trivy.json"]:
            if os.path.exists(f):
                os.remove(f)

        # --- 1. Run Semgrep (All Plans) - Multi-Language Support ---
        print("ℹ️  (Scanner): Running Semgrep with multi-language support...")
        semgrep_command = [
            "semgrep",
            # Use only verified working rulesets
            "--config", "p/owasp-top-ten",      # OWASP Top 10 (all languages)
            "--config", "p/security-audit",     # Security audit (all languages)
            "--config", "p/python",             # Python security
            "--config", "p/javascript",         # JavaScript/TypeScript security
            "--config", "p/typescript",         # TypeScript security
            "--config", "p/java",               # Java security
            "--config", "p/golang",             # Go security
            "--config", "p/django",             # Django-specific
            "--config", "p/flask",              # Flask-specific
            "--config", "p/react",              # React-specific
            "--error",                          # Exit with error code if findings are found
            "--verbose"                         # Show more details
        ]
        if user_plan in ["pro", "enterprise"]:
            print("ℹ️  (Scanner): Adding Pro Semgrep rules (CWE Top 25, additional security checks)...")
            semgrep_command.extend([
                "--config", "p/cwe-top-25",     # CWE Top 25 vulnerabilities
            ])
        
        semgrep_command.extend([
            "--json", "-o", REPORT_FILE,
            "--exclude", ".git",                # Exclude the .git folder
            "--exclude", "node_modules",        # Exclude node_modules
            "--exclude", "*.min.js",            # Exclude minified files
            "--max-target-bytes", "5000000",    # Scan files up to 5MB
            WORKSPACE_DIR                       # Scan the whole directory
        ]) 
        
        # We check for returncode 1, which means "findings found"
        print(f"🔍 (Scanner): Running semgrep scan...")
        result = subprocess.run(semgrep_command, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode not in [0, 1]:
            print(f"⚠️  (Scanner): Semgrep failed with return code {result.returncode}")
            print(f"⚠️  (Scanner): STDERR: {result.stderr.strip()}")
        else:
            print(f"✅ (Scanner): Semgrep completed with return code {result.returncode}")

        # --- 2. Run Pro Scanners ---
        if user_plan in ["pro", "enterprise"]:
            print("ℹ️  (Scanner): Running Gitleaks...")
            gitleaks_command = [
                "gitleaks", "detect",
                "--source", WORKSPACE_DIR,
                "--report-format", "json",
                "--report-path", "report-gitleaks.json"
            ]
            result = subprocess.run(gitleaks_command, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                 print(f"⚠️  (Scanner): Gitleaks failed. STDERR: {result.stderr.strip()}")

            print("ℹ️  (Scanner): Running Trivy (Filesystem)...")
            trivy_command = [
                "trivy", "fs",
                "--format", "json",
                "--output", "report-trivy.json",
                WORKSPACE_DIR
            ]
            result = subprocess.run(trivy_command, capture_output=True, text=True, encoding='utf-8')
            if result.returncode != 0:
                 print(f"⚠️  (Scanner): Trivy failed. STDERR: {result.stderr.strip()}")

        # --- 3. Check for any findings (IMPROVED LOGIC) ---
        found_vulns = False
        for report_path in [REPORT_FILE, "report-gitleaks.json", "report-trivy.json"]:
            if os.path.exists(report_path) and os.path.getsize(report_path) > 50:
                try:
                    with open(report_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Semgrep check: "results" key exists and is not empty
                    if isinstance(data, dict) and data.get("results"):
                        print(f"✅ (Scanner): Found {len(data['results'])} vulnerabilities in {report_path}")
                        found_vulns = True
                        break
                        
                    # Gitleaks check: data is a list and is not empty
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✅ (Scanner): Found {len(data)} vulnerabilities in {report_path}")
                        found_vulns = True
                        break
                        
                    # Trivy check: "Results" key exists and is not empty
                    if isinstance(data, dict) and data.get("Results"):
                        print(f"✅ (Scanner): Found vulnerabilities in {report_path}")
                        found_vulns = True
                        break
                        
                except Exception as e:
                    print(f"⚠️  (Scanner): Could not parse {report_path}. {e}")
        
        if found_vulns:
            print("✅ (Scanner): Scan complete. At least one vulnerability was found.")
            return True
        else:
            print("✅ (Scanner): Scan complete. No vulnerabilities found.")
            return False
            
    except Exception as e:
        print(f"❌ (Scanner): Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return False
