#!/bin/bash

# Create necessary directories if they don't exist
mkdir -p .github/workflows
mkdir -p src/components/{core,dashboard,layout,error}
mkdir -p src/{hooks,pages,services,theme,types,utils}

# Make the setup script executable
chmod +x setup-repo.sh

# Create directories for future components
mkdir -p src/components/{customers,orders,inspections,installations,inventory,reports}

# Copy documentation to appropriate location
if [ ! -d "docs" ]; then
  mkdir docs
fi

# Organize files
echo "Organizing project files..."

# Ensure all TypeScript config files are in place
if [ ! -f "tsconfig.json" ]; then
  echo "TypeScript config missing. Please check the project setup."
  exit 1
fi

# Ensure Vite config is present
if [ ! -f "vite.config.ts" ]; then
  echo "Vite config missing. Please check the project setup."
  exit 1
fi

# Run formatting
echo "Running code formatter..."
npm run format || echo "Formatting skipped - npm not installed yet"

# Check if git is initialized
if [ ! -d ".git" ]; then
  echo "Running repository setup..."
  ./setup-repo.sh
else
  echo "Git repository already initialized"
fi

echo "Project preparation complete! You can now proceed with:"
echo "1. npm install"
echo "2. npm run dev"
echo "3. git push (if not already done by setup-repo.sh)"
