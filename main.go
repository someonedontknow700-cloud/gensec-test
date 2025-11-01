package main

import (
	"crypto/md5"
	"database/sql"
	"encoding/base64"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"time"

	_ "github.com/go-sql-driver/mysql"
)

// VULNERABILITY 1: Multiple Hardcoded Secrets (Gitleaks, Semgrep)
const (
	API_KEY         = "sk_live_51KxYzAbCdEfGhIjKlMnOpQr"
	AWS_SECRET      = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
	GITHUB_TOKEN    = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh"
	JWT_SECRET      = "my-super-secret-jwt-key-12345"
	STRIPE_KEY      = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
	DATABASE_PASSWD = "root_password_super_secret_123"
)

var (
	adminPassword = "supersecretpassword123!"
	privateKey    = []byte("-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASC")
)

// VULNERABILITY 2: Command Injection (Semgrep G204)
func getSystemStatus(w http.ResponseWriter, r *http.Request) {
	host := r.URL.Query().Get("host")
	// Allows arbitrary command execution
	cmd := exec.Command("sh", "-c", "ping -c 1 "+host)
	out, _ := cmd.CombinedOutput()
	fmt.Fprintf(w, "Output: %s\n", out)
}

// VULNERABILITY 3: Another Command Injection with bash
func searchLogs(w http.ResponseWriter, r *http.Request) {
	searchTerm := r.URL.Query().Get("search")
	// bash -c allows command chaining
	cmd := exec.Command("bash", "-c", "grep -r "+searchTerm+" /var/log")
	output, _ := cmd.CombinedOutput()
	fmt.Fprintf(w, "Search results:\n%s", output)
}

// VULNERABILITY 4: SQL Injection (Semgrep)
func getUser(w http.ResponseWriter, r *http.Request) {
	// Hardcoded credentials in connection string
	db, _ := sql.Open("mysql", "root:"+DATABASE_PASSWD+"@tcp(127.0.0.1:3306)/dbname")
	defer db.Close()

	userID := r.URL.Query().Get("id")
	// Using parameterized query to prevent SQL injection
	query := "SELECT name, email, password FROM users WHERE id = ?"
	rows, err := db.Query(query, userID)
	if err != nil {
		// VULNERABILITY 5: Error message disclosure (Semgrep G104)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		log.Printf("SQL Error exposed: %s", err.Error())
		return
	}
	defer rows.Close()

	for rows.Next() {
		var name, email, password string
		rows.Scan(&name, &email, &password)
		// VULNERABILITY 6: Sensitive data in response
		fmt.Fprintf(w, "User: %s, Email: %s, Password Hash: %s\n", name, email, password)
	}
}

// VULNERABILITY 7: Weak Cryptography - MD5 (Semgrep)
func hashPassword(password string) string {
	// MD5 is cryptographically broken
	hasher := md5.New()
	hasher.Write([]byte(password))
	return fmt.Sprintf("%x", hasher.Sum(nil))
}

// VULNERABILITY 8: Path Traversal (Semgrep G103, G304)
func readFile(w http.ResponseWriter, r *http.Request) {
	filename := r.URL.Query().Get("file")
	// No validation - can read /etc/passwd, private keys, etc.
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		fmt.Fprintf(w, "Error: %s\n", err)
		return
	}
	fmt.Fprintf(w, "File contents:\n%s", data)
}

// VULNERABILITY 9: Insecure Random (Semgrep)
func generateToken() string {
	// Using time-based seed is predictable
	token := strconv.FormatInt(time.Now().UnixNano(), 10)
	return base64.StdEncoding.EncodeToString([]byte(token))
}

// VULNERABILITY 10: XSS - Unescaped HTML Output (Semgrep)
func displayMessage(w http.ResponseWriter, r *http.Request) {
	message := r.URL.Query().Get("msg")
	// Direct HTML output without escaping
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprintf(w, "<html><body><h1>Message: %s</h1></body></html>", message)
}

// VULNERABILITY 11: Weak CORS Policy (Semgrep)
func corsHandler(w http.ResponseWriter, r *http.Request) {
	// Allows any origin - CSRF attacks possible
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "*")
	w.Header().Set("Access-Control-Allow-Headers", "*")
	fmt.Fprintf(w, "CORS is wide open!")
}

// VULNERABILITY 12: Sensitive Data in Logs (Semgrep)
func loginUser(w http.ResponseWriter, r *http.Request) {
	username := r.URL.Query().Get("user")
	password := r.URL.Query().Get("pass")

	// Logging passwords and secrets
	log.Printf("Login attempt - User: %s, Password: %s", username, password)
	log.Printf("Using API Key: %s", API_KEY)

	if password == adminPassword {
		fmt.Fprintf(w, "Login successful! Token: %s\n", JWT_SECRET)
	}
}

// VULNERABILITY 13: Weak Password Validation (Logic)
func validatePassword(password string) bool {
	// Only requires 4 characters - way too weak
	return len(password) > 4
}

// VULNERABILITY 14: Race Condition (Semgrep)
var requestCount = 0

func countRequests(w http.ResponseWriter, r *http.Request) {
	// No mutex protection - race condition
	requestCount++
	fmt.Fprintf(w, "Total requests: %d\n", requestCount)
}

// VULNERABILITY 15: Insecure Regex (ReDoS)
func validateEmail(email string) bool {
	// This regex is vulnerable to ReDoS attacks
	pattern := `^([a-zA-Z0-9_\-\.]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$`
	match, _ := regexp.MatchString(pattern, email)
	return match
}

// VULNERABILITY 16: Debug Endpoint Exposing Secrets (Custom)
func debugHandler(w http.ResponseWriter, r *http.Request) {
	// Exposes all secrets via debug endpoint
	fmt.Fprintf(w, "=== DEBUG INFO ===\n")
	fmt.Fprintf(w, "API_KEY: %s\n", API_KEY)
	fmt.Fprintf(w, "AWS_SECRET: %s\n", AWS_SECRET)
	fmt.Fprintf(w, "GITHUB_TOKEN: %s\n", GITHUB_TOKEN)
	fmt.Fprintf(w, "JWT_SECRET: %s\n", JWT_SECRET)
	fmt.Fprintf(w, "STRIPE_KEY: %s\n", STRIPE_KEY)
	fmt.Fprintf(w, "DATABASE_PASSWD: %s\n", DATABASE_PASSWD)
	fmt.Fprintf(w, "Admin Password: %s\n", adminPassword)
	fmt.Fprintf(w, "Private Key: %s\n", privateKey)
}

// VULNERABILITY 17: Exposed Headers with Secrets
func adminPanel(w http.ResponseWriter, r *http.Request) {
	// Secrets in HTTP headers
	w.Header().Set("X-Admin-Password", adminPassword)
	w.Header().Set("X-API-Key", API_KEY)
	w.Header().Set("X-JWT-Secret", JWT_SECRET)
	fmt.Fprintf(w, "Admin panel loaded")
}

// VULNERABILITY 18: Hardcoded Credentials in Function
func connectDatabase() *sql.DB {
	// More hardcoded credentials
	connectionString := "admin:admin123@tcp(localhost:3306)/production_db"
	db, err := sql.Open("mysql", connectionString)
	if err != nil {
		log.Printf("Database error (leaking internal info): %s", err)
	}
	return db
}

// VULNERABILITY 19: IDOR - Insecure Direct Object Reference
func getUserProfile(w http.ResponseWriter, r *http.Request) {
	// No authorization check - anyone can access any user's data
	userID := r.URL.Query().Get("uid")
	fmt.Fprintf(w, "Accessing user profile for UID: %s\n", userID)
	fmt.Fprintf(w, "SSN: 123-45-6789, Credit Card: 4532-1234-5678-9012")
}

// VULNERABILITY 20: Insecure File Upload (No validation)
func uploadFile(w http.ResponseWriter, r *http.Request) {
	file, header, _ := r.FormFile("file")
	defer file.Close()

	// No validation - can upload malicious files
	data, _ := ioutil.ReadAll(file)
	// Saves with user-controlled filename
	ioutil.WriteFile("uploads/"+header.Filename, data, 0644)
	fmt.Fprintf(w, "File uploaded: %s", header.Filename)
}

// VULNERABILITY 21: Missing Rate Limiting (Logic)
func apiEndpoint(w http.ResponseWriter, r *http.Request) {
	// No rate limiting - DDoS vulnerable
	fmt.Fprintf(w, "API response with secret: %s", API_KEY)
}

// VULNERABILITY 22: Unvalidated Redirect (Open Redirect)
func redirect(w http.ResponseWriter, r *http.Request) {
	target := r.URL.Query().Get("url")
	// No validation - phishing risk
	http.Redirect(w, r, target, http.StatusFound)
}

func main() {
	// Print all secrets to logs on startup
	log.Println("=== STARTING VULNERABLE SERVER ===")
	log.Printf("Admin Password: %s", adminPassword)
	log.Printf("API Key: %s", API_KEY)
	log.Printf("Database Password: %s", DATABASE_PASSWD)

	// Register all vulnerable handlers
	http.HandleFunc("/", readFile)
	http.HandleFunc("/status", getSystemStatus)
	http.HandleFunc("/search", searchLogs)
	http.HandleFunc("/user", getUser)
	http.HandleFunc("/cors", corsHandler)
	http.HandleFunc("/message", displayMessage)
	http.HandleFunc("/login", loginUser)
	http.HandleFunc("/count", countRequests)
	http.HandleFunc("/debug", debugHandler)
	http.HandleFunc("/admin", adminPanel)
	http.HandleFunc("/profile", getUserProfile)
	http.HandleFunc("/upload", uploadFile)
	http.HandleFunc("/api", apiEndpoint)
	http.HandleFunc("/redirect", redirect)

	// VULNERABILITY 23: HTTP without TLS (Semgrep G402)
	log.Println("Starting INSECURE HTTP server on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}