# Git Workflow for Raspberry Pi Temperature Monitor

## Repository Structure

This repository contains a complete temperature monitoring system for Raspberry Pi with the following key components:

- **collector/**: Temperature data collection service with plugin system
- **server/**: Web server and API for data visualization
- **scripts/**: Management and utility scripts
- **config/**: Configuration files
- **docs/**: Documentation and setup guides

## Important Notes

### Ignored Files
The following are automatically ignored by git:
- `data/` directory (contains runtime database and logs)
- `*.log`, `*.db`, `*.sqlite*` files
- Python cache files (`__pycache__/`, `*.pyc`)
- IDE and OS files

### Version Control Best Practices

1. **Configuration Files**: The main `config/config.json` is tracked, but avoid committing sensitive data
2. **Scripts**: All scripts are tracked and should be executable
3. **Documentation**: Keep documentation updated with code changes
4. **Data Files**: Never commit runtime data, logs, or database files

## Common Git Commands

### Daily Workflow
```bash
# Check status
git status

# Add specific files
git add filename.py

# Add all changes (be careful!)
git add .

# Commit changes
git commit -m "Description of changes"

# View history
git log --oneline
```

### Working with Changes
```bash
# See what changed
git diff

# See staged changes
git diff --cached

# Unstage files
git reset filename.py

# Discard local changes (careful!)
git checkout -- filename.py
```

### Branching (for development)
```bash
# Create and switch to new branch
git checkout -b feature-branch

# Switch between branches
git checkout master
git checkout feature-branch

# Merge branch back to master
git checkout master
git merge feature-branch

# Delete branch
git branch -d feature-branch
```

## File Permissions

Several files need to be executable and should maintain their permissions:
- All files in `scripts/` directory
- `collector/temperature_collector.py`
- `server/web_server.py`

Git tracks these permissions, so they should be preserved across clones.

## Release Management

When making significant changes:

1. Update version information in README.md
2. Update documentation if APIs change
3. Test thoroughly with `scripts/test_system.py`
4. Create meaningful commit messages
5. Consider tagging releases:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   ```

## Backup and Remote Repositories

To backup to a remote repository:
```bash
# Add remote
git remote add origin https://github.com/username/pi-temp-monitor.git

# Push to remote
git push -u origin master

# Push tags
git push --tags
```

## Troubleshooting

### File Permissions Lost
If executable permissions are lost:
```bash
chmod +x scripts/*.sh
chmod +x collector/temperature_collector.py
chmod +x server/web_server.py
git add -u  # Updates permissions in git
git commit -m "Fix file permissions"
```

### Accidentally Committed Data Files
If you accidentally commit data files:
```bash
# Remove from git but keep local file
git rm --cached data/temperature_data.db

# Commit the removal
git commit -m "Remove data file from git"
```

### Large Repository Size
If repository becomes large due to data files:
```bash
# Clean up history (use with caution)
git filter-branch --index-filter 'git rm --cached --ignore-unmatch data/*' HEAD
```
