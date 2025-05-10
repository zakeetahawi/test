#!/bin/bash

# Initialize git repository
git init

# Add remote origin
git remote add origin https://github.com/zakeetahawi/reacttest.git

# Create and checkout development branch
git checkout -b development

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: React CRM System

- Added base React application structure
- Implemented installation tracking system
- Added dashboard components
- Added Material-UI theming with RTL support
- Updated documentation"

# Push to GitHub
git push -u origin development

echo "Repository has been initialized and code has been pushed to GitHub."
