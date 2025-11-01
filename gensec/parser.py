import os
import json
from gensec.constants import REPORT_FILE, WORKSPACE_DIR

def get_vulnerability_info():
    print("🤖 (Parser): Consolidating and prioritizing reports...")
    
    all_findings = []
    
    severity_keywords = {
        "Gitleaks": 0, "Secret": 0,
        "Command Injection": 1,
        "SQL Injection": 2,
        "CRITICAL": 3,
        "Hardcoded": 4, "Hardcoded Secret": 4,
        "HIGH": 5,
        "Weak Crypto": 6, "MD5": 6, "TLS": 7,
        "MEDIUM": 8,
        "XSS": 9, "Sensitive": 10
    }
    
    # --- 1. Parse Semgrep Report ---
    try:
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r', encoding='utf-8') as f:
                report = json.load(f)
            print("ℹ️  (Parser): Parsing Semgrep report...")
            for finding in report.get("results", []):
                relative_path = finding.get("path", "unknown/file").replace(f"{WORKSPACE_DIR}/", "", 1)
                all_findings.append({
                    "check_id": finding.get("check_id", "semgrep-finding"),
                    "message": finding.get("extra", {}).get("message", "Unknown"),
                    "snippet": finding.get("extra", {}).get("lines", "N/A"),
                    "line": finding.get("start", {}).get("line", 0),
                    "path": relative_path,
                    "raw_severity": finding.get("extra", {}).get("severity", "UNKNOWN"),
                    "tool": "semgrep"
                })
    except Exception as e:
        print(f"⚠️  (Parser): Could not parse {REPORT_FILE}. {e}")

    # --- 2. Parse Gitleaks Report (Pro) ---
    try:
        if os.path.exists("report-gitleaks.json"):
            with open("report-gitleaks.json", 'r', encoding='utf-8') as f:
                report = json.load(f)
            print("ℹ️  (Parser): Parsing Gitleaks report...")
            for finding in report: # Gitleaks report is a list
                relative_path = finding.get("File", "unknown/file").replace(f"{WORKSPACE_DIR}/", "", 1)
                all_findings.append({
                    "check_id": f"gitleaks.{finding.get('RuleID')}",
                    "message": f"Gitleaks found: {finding.get('Description')}",
                    "snippet": finding.get('Secret'),
                    "line": finding.get('StartLine'),
                    "path": relative_path,
                    "raw_severity": "CRITICAL",
                    "tool": "gitleaks"
                })
    except Exception as e:
        print(f"⚠️  (Parser): Could not parse report-gitleaks.json. {e}")

    # --- 3. Parse Trivy Report (Pro) ---
    try:
        if os.path.exists("report-trivy.json"):
            with open("report-trivy.json", 'r', encoding='utf-8') as f:
                report = json.load(f)
            print("ℹ️  (Parser): Parsing Trivy report...")
            results = report.get("Results", []) if isinstance(report, dict) else []
            if results:
                for target in results:
                    relative_path = target.get("Target", "unknown/file").replace(f"{WORKSPACE_DIR}/", "", 1)
                    # This is for SCA (e.g., go.mod)
                    if target.get("Vulnerabilities"): 
                        for vuln in target.get("Vulnerabilities", []):
                            all_findings.append({
                                "check_id": f"trivy.{vuln.get('VulnerabilityID')}",
                                "message": f"Trivy SCA: {vuln.get('Title')} in {vuln.get('PkgName')}",
                                "snippet": f"Installed: {vuln.get('InstalledVersion')}, Fixed: {vuln.get('FixedVersion')}",
                                "line": 0,
                                "path": relative_path, # Path to go.mod, etc.
                                "raw_severity": vuln.get('Severity', "UNKNOWN"),
                                "tool": "trivy-sca"
                            })
                    # This is for Filesystem Misconfigurations
                    if target.get("Misconfigurations"): 
                        for misconfig in target.get("Misconfigurations", []):
                             all_findings.append({
                                "check_id": f"trivy.{misconfig.get('ID')}",
                                "message": f"Trivy FS: {misconfig.get('Title')}",
                                "snippet": misconfig.get('Description'),
                                "line": misconfig.get('StartLine', 0),
                                "path": relative_path,
                                "raw_severity": misconfig.get('Severity', "UNKNOWN"),
                                "tool": "trivy-fs"
                            })
    except Exception as e:
        print(f"⚠️  (Parser): Could not parse report-trivy.json. {e}")

    # --- 4. Prioritize All Findings ---
    
    # --- THIS IS THE CRITICAL FIX ---
    if not all_findings:
        print("❌ (Parser): No findings were consolidated from reports. Skipping.")
        return None
    # --- END OF FIX ---

    print(f"🤖 (Parser): Prioritizing {len(all_findings)} total findings...")
    
    prioritized_findings = []
    for finding in all_findings:
        priority_score = 999
        for keyword, score in severity_keywords.items():
            if keyword.lower() in finding["message"].lower() or keyword.lower() in finding["check_id"].lower():
                priority_score = score
                break
        
        severity_map = {"CRITICAL": 3, "HIGH": 5, "MEDIUM": 8, "LOW": 10, "WARNING": 6}
        severity_score = severity_map.get(finding["raw_severity"], 999)
        
        finding["priority"] = min(priority_score, severity_score)
        prioritized_findings.append(finding)

    prioritized_findings.sort(key=lambda x: x["priority"])
    best_finding = prioritized_findings[0]
    
    print(f"\n✅ (Parser): Highest priority: {best_finding['check_id']} (Tool: {best_finding['tool']})")
    print(f"   File: {best_finding['path']} (Line: {best_finding['line']})")
    print(f"   Message: {best_finding['message'][:100]}...")
    
    return best_finding