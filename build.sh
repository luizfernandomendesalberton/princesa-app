#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create database tables (will run on first deploy)
python -c "
import app
app.init_db()
print('✅ Database initialized successfully!')
"