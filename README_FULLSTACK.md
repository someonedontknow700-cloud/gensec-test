# GenSec Full Stack Application

A modern web application for automated security vulnerability scanning and fixing with AI.

## Architecture

- **Backend**: FastAPI server exposing GenSec functionality via REST API
- **Frontend**: React + Vite + TailwindCSS modern UI
- **AI**: Groq LLM for intelligent vulnerability fixes
- **Scanner**: Semgrep for multi-language security scanning

## Prerequisites

- Python 3.8+
- Node.js 16+
- GitHub Personal Access Token (with `repo` scope)
- Groq API Key

## Setup

### 1. Backend Setup

```bash
# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
# Install Node dependencies
cd frontend
npm install
cd ..
```

### 3. Environment Variables

You can either:
- Set them in your shell before starting
- Or enter them in the web UI

Required variables:
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GROQ_API_KEY`: Your Groq API key

## Running the Application

### Option 1: Using Scripts (Recommended)

**Terminal 1 - Start Backend:**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**Terminal 2 - Start Frontend:**
```bash
chmod +x start_frontend.sh
./start_frontend.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
export PATH="$PWD/.venv/bin:$PATH"
python api_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

1. Open http://localhost:5173 in your browser
2. Enter your repository (format: `owner/repo`)
3. Enter your GitHub token
4. Enter your Groq API key
5. Select plan tier (free/pro/enterprise)
6. Click "Start Security Scan"
7. Watch real-time progress and logs
8. View created pull requests with fixes

## Features

- ✅ Real-time scan progress monitoring
- ✅ Live activity logs
- ✅ Automatic PR creation for fixes
- ✅ Multi-language security scanning
- ✅ AI-powered vulnerability fixes
- ✅ Beautiful modern UI with glassmorphism
- ✅ Responsive design
- ✅ Dark mode optimized

## API Endpoints

- `POST /scan` - Start a new security scan
- `GET /status/{job_id}` - Get scan status
- `GET /jobs` - List all scan jobs
- `DELETE /jobs/{job_id}` - Delete a job

## Tech Stack

### Backend
- FastAPI
- Uvicorn
- Groq AI
- Semgrep
- PyGithub

### Frontend
- React 19
- Vite
- TailwindCSS
- Axios
- Lucide Icons

## Security Notes

- Never commit your API keys or tokens
- Tokens are only stored in memory during the scan
- Use environment variables for production deployments
- GitHub tokens should have minimal required permissions

## Troubleshooting

### Backend Issues

**Semgrep not found:**
```bash
export PATH="$PWD/.venv/bin:$PATH"
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

### Frontend Issues

**Dependencies not installed:**
```bash
cd frontend
npm install
```

**Port 5173 already in use:**
```bash
# Edit vite.config.js and change the port
```

### CORS Issues

The backend is configured to allow requests from:
- http://localhost:5173
- http://localhost:3000

If you need to add more origins, edit `api_server.py`:
```python
allow_origins=["http://localhost:5173", "http://your-custom-port"]
```

## Development

### Backend Development

The backend uses FastAPI with auto-reload:
```bash
uvicorn api_server:app --reload
```

### Frontend Development

Vite provides hot module replacement:
```bash
cd frontend
npm run dev
```

## Production Deployment

### Backend

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend
npm run build
# Serve the dist/ folder with your web server
```

## License

Same as GenSec project

## Support

For issues and questions, please open an issue on GitHub.
