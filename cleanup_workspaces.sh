#!/bin/bash
# Bash script to clean up old workspace directories

echo "================================================"
echo "Cleaning up old workspace directories"
echo "================================================"

# Find all workspace directories
workspace_dirs=$(find . -maxdepth 1 -type d -name "workspace*" | sort)

if [ -z "$workspace_dirs" ]; then
    echo ""
    echo "✅ No workspace directories found to clean"
    exit 0
fi

count=$(echo "$workspace_dirs" | wc -l)
echo ""
echo "📋 Found $count workspace directory(ies):"
echo "$workspace_dirs" | while read -r dir; do
    echo "   - $(basename "$dir")"
done

echo ""
echo "Cleaning up..."

# Remove each directory
cleaned=0
failed=0

echo "$workspace_dirs" | while read -r dir; do
    if rm -rf "$dir" 2>/dev/null; then
        echo "✅ Cleaned: $(basename "$dir")"
        cleaned=$((cleaned + 1))
    else
        echo "❌ Failed to clean: $(basename "$dir")"
        failed=$((failed + 1))
    fi
done

# Final summary
echo ""
echo "================================================"
echo "📊 Cleanup Summary"
echo "================================================"
echo "✅ Cleaned: $cleaned directory(ies)"
if [ $failed -gt 0 ]; then
    echo "❌ Failed: $failed directory(ies)"
fi
echo "================================================"
echo ""

if [ $failed -eq 0 ]; then
    echo "✅ All workspaces cleaned successfully!"
    exit 0
else
    echo "⚠️  Some workspaces could not be cleaned"
    exit 1
fi

