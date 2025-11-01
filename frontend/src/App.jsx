import { useState, useEffect } from 'react'
import axios from 'axios'
import { Shield, AlertTriangle, CheckCircle, Loader, Github, Key, Play, FileText, GitPullRequest, Clock } from 'lucide-react'
const API_URL = 'http://localhost:8000'

function App() {
  const [repository, setRepository] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [groqApiKey] = useState(import.meta.env.VITE_GROQ_API_KEY || '')
  const [userPlan, setUserPlan] = useState('free')
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [repositories, setRepositories] = useState([])
  const [fetchingRepos, setFetchingRepos] = useState(false)

  // Poll for status updates
  useEffect(() => {
    if (!jobId) return

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/status/${jobId}`)
        setStatus(response.data)
        
        if (response.data.status === 'completed' || response.data.error) {
          clearInterval(interval)
          setLoading(false)
        }
      } catch (err) {
        console.error('Error fetching status:', err)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId])

  const fetchRepositories = async (token) => {
    if (!token || token.length < 10) return
    
    setFetchingRepos(true)
    setError(null)
    
    try {
      const response = await axios.get('https://api.github.com/user/repos', {
        headers: {
          'Authorization': `token ${token}`,
          'Accept': 'application/vnd.github.v3+json'
        },
        params: {
          per_page: 100,
          sort: 'updated',
          affiliation: 'owner,collaborator,organization_member'
        }
      })
      
      const repos = response.data.map(repo => repo.full_name)
      setRepositories(repos)
      if (repos.length > 0) {
        setRepository(repos[0])
      }
    } catch (err) {
      setError('Failed to fetch repositories. Please check your GitHub token.')
      setRepositories([])
    } finally {
      setFetchingRepos(false)
    }
  }

  const handleTokenChange = (token) => {
    setGithubToken(token)
    if (token.length > 10) {
      fetchRepositories(token)
    } else {
      setRepositories([])
      setRepository('')
    }
  }

  const startScan = async () => {
    setError(null)
    setLoading(true)
    setStatus(null)
    
    try {
      const response = await axios.post(`${API_URL}/scan`, {
        repository,
        user_plan: userPlan,
        github_token: githubToken,
        groq_api_key: groqApiKey
      })
      
      setJobId(response.data.job_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scan')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <Shield className="w-16 h-16 text-purple-400" />
          </div>
          <h1 className="text-5xl font-bold text-white mb-2">GenSec Agent</h1>
          <p className="text-gray-300 text-lg">AI-Powered Security Vulnerability Scanner & Auto-Fixer</p>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Configuration Card */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-8 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
              <Key className="w-6 h-6 mr-2" />
              Configuration
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  <Key className="w-4 h-4 inline mr-2" />
                  GitHub Token
                </label>
                <input
                  type="password"
                  value={githubToken}
                  onChange={(e) => handleTokenChange(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="ghp_xxxxxxxxxxxx"
                />
                {fetchingRepos && (
                  <p className="text-sm text-gray-400 mt-2 flex items-center">
                    <Loader className="w-4 h-4 animate-spin mr-2" />
                    Fetching your repositories...
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  <Github className="w-4 h-4 inline mr-2" />
                  Select Repository
                </label>
                {repositories.length > 0 ? (
                  <select
                    value={repository}
                    onChange={(e) => setRepository(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {repositories.map((repo) => (
                      <option key={repo} value={repo} className="bg-slate-800">
                        {repo}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={repository}
                    onChange={(e) => setRepository(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="Enter GitHub token to load repositories or type manually (owner/repo)"
                    disabled={fetchingRepos}
                  />
                )}
                {repositories.length > 0 && (
                  <p className="text-sm text-green-400 mt-2">
                    ✓ Found {repositories.length} repositories
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Plan Tier
                </label>
                <select
                  value={userPlan}
                  onChange={(e) => setUserPlan(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="free">Free</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>

              <button
                onClick={startScan}
                disabled={loading || !repository || !githubToken}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 flex items-center justify-center space-x-2 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    <span>Scanning...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    <span>Start Security Scan</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-8">
              <div className="flex items-center text-red-200">
                <AlertTriangle className="w-5 h-5 mr-2" />
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Status Card */}
          {status && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
                <FileText className="w-6 h-6 mr-2" />
                Scan Status
              </h2>

              <div className="space-y-4">
                {/* Status Badge */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Status:</span>
                  <span className={`px-4 py-2 rounded-full font-semibold ${
                    status.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                    status.status === 'running' ? 'bg-blue-500/20 text-blue-300' :
                    status.status === 'queued' ? 'bg-yellow-500/20 text-yellow-300' :
                    'bg-gray-500/20 text-gray-300'
                  }`}>
                    {status.status === 'running' && <Loader className="w-4 h-4 inline animate-spin mr-2" />}
                    {status.status === 'completed' && <CheckCircle className="w-4 h-4 inline mr-2" />}
                    {status.status.toUpperCase()}
                  </span>
                </div>

                {/* Repository */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Repository:</span>
                  <span className="text-white font-mono">{status.repository}</span>
                </div>

                {/* Iteration */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Current Iteration:</span>
                  <span className="text-white font-semibold">{status.current_iteration}</span>
                </div>

                {/* Vulnerabilities Found */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Vulnerabilities Found:</span>
                  <span className={`font-semibold ${status.vulnerabilities_found > 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {status.vulnerabilities_found}
                  </span>
                </div>

                {/* PRs Created */}
                {status.prs_created && status.prs_created.length > 0 && (
                  <div>
                    <span className="text-gray-300 block mb-2">Pull Requests Created:</span>
                    <div className="space-y-2">
                      {status.prs_created.map((pr, idx) => (
                        <a
                          key={idx}
                          href={pr}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center text-purple-400 hover:text-purple-300 transition-colors"
                        >
                          <GitPullRequest className="w-4 h-4 mr-2" />
                          PR #{idx + 1}
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Logs */}
                {status.logs && status.logs.length > 0 && (
                  <div>
                    <span className="text-gray-300 block mb-2 flex items-center">
                      <Clock className="w-4 h-4 mr-2" />
                      Activity Log:
                    </span>
                    <div className="bg-black/30 rounded-lg p-4 max-h-64 overflow-y-auto font-mono text-sm">
                      {status.logs.map((log, idx) => (
                        <div key={idx} className="text-gray-300 mb-1">{log}</div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Error */}
                {status.error && (
                  <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                    <div className="flex items-center text-red-200">
                      <AlertTriangle className="w-5 h-5 mr-2" />
                      <span>{status.error}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-400">
          <p>Powered by Groq AI & Semgrep Security Scanner</p>
        </div>
      </div>
    </div>
  )
}

export default App
