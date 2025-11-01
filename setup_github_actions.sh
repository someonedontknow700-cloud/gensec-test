#!/bin/bash

echo "🚀 GenSec GitHub Actions Setup"
echo "================================"
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Not a git repository. Initializing..."
    git init
    echo "✅ Git repository initialized"
fi

# Show current remote
echo "📡 Current git remote:"
git remote -v
echo ""

# Ask for repository
read -p "Enter your GitHub repository (e.g., username/repo): " REPO

if [ -z "$REPO" ]; then
    echo "❌ Repository name cannot be empty"
    exit 1
fi

# Update remote
echo "🔧 Updating git remote..."
git remote remove origin 2>/dev/null
git remote add origin "https://github.com/$REPO.git"
echo "✅ Remote set to: https://github.com/$REPO.git"
echo ""

# Show what will be committed
echo "📋 Files to be committed:"
git status --short
echo ""

# Commit and push
read -p "Push to GitHub? (y/n): " CONFIRM

if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    echo "📦 Adding files..."
    git add .
    
    echo "💾 Committing..."
    git commit -m "Add GenSec security scanner with GitHub Actions workflow"
    
    echo "⬆️  Pushing to GitHub..."
    git push -u origin main || git push -u origin master
    
    echo ""
    echo " Successfully pushed to GitHub!"
    echo ""
    echo " Next steps:"
    echo "1. Go to https://github.com/$REPO/settings/secrets/actions"
    echo "2. Add secret: GROQ_API_KEY = your-groq-api-key-here"
    echo "3. Go to https://github.com/$REPO/actions"
    echo "4. Click 'GenSec Security Scanner' and run the workflow"
    echo ""
else
    echo " Push cancelled"
fi
