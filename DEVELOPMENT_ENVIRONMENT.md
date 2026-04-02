# Development Environment Setup with Nix

## What This Adds

This project now includes a complete Nix-based development environment that provides reproducible, isolated development setup across all platforms (macOS, Linux, WSL2).

## Files Added

### 1. `flake.nix`
The Nix flake configuration that defines the entire development environment including:
- Python 3.11 with `uv` package manager
- Node.js 20 for the frontend
- PostgreSQL 15 and Redis
- Docker and Docker Compose
- All necessary development tools

**Three development shells available:**
- `nix develop` - Full-stack environment (default)
- `nix develop .#backend` - Backend-only environment
- `nix develop .#frontend` - Frontend-only environment

### 2. `.envrc`
Direnv configuration that automatically loads the Nix environment when you `cd` into the project directory. No manual activation needed!

### 3. `NIX_SETUP.md`
Comprehensive documentation covering:
- How to install Nix and direnv
- Quick start instructions
- Troubleshooting guide
- All available commands and features

### 4. `Makefile` (Enhanced)
Merged and enhanced the existing Makefile with additional commands:
- All original commands preserved (`make back`, `make front`, `make uv-install`, `make pre-commit`)
- Added comprehensive help system (`make help`)
- Docker orchestration commands
- Database management
- Code quality tools (lint, format)
- Testing commands
- Nix-specific utilities

### 5. `.gitignore`
Ensures Nix artifacts and development files don't get committed:
- Nix directories (`.direnv/`, `.nix-postgres/`)
- Python and Node artifacts
- Environment files
- Build outputs

## Why Nix?

### Benefits for Your Interview
1. **Shows modern DevOps knowledge** - Nix/NixOS is increasingly popular in professional environments
2. **Demonstrates care for developer experience** - Makes onboarding new developers trivial
3. **Highlights reproducibility** - "Works on my machine" is solved
4. **Professional polish** - Shows attention to project infrastructure

### Technical Benefits
1. **Reproducibility** - Everyone gets exactly the same versions of all tools
2. **Isolation** - No conflicts with system packages or other projects
3. **Cross-platform** - Works identically on macOS, Linux, and WSL2
4. **Declarative** - Environment is code (Infrastructure as Code)
5. **No global installs** - Everything is project-scoped
6. **Fast context switching** - Easy to switch between projects

## Quick Start

### For Interview Reviewers

```bash
# 1. Install Nix (one-time setup)
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install

# 2. Install direnv (optional but recommended)
brew install direnv  # macOS
# OR
nix profile install nixpkgs#direnv

# 3. Set up direnv in your shell (add to ~/.zshrc or ~/.bashrc)
eval "$(direnv hook zsh)"  # or bash, fish, etc.

# 4. Enter the project directory
cd New_devs_App
direnv allow  # if using direnv

# 5. Everything is now installed and ready!
make help     # See all available commands
make dev      # Start development servers
```

### Without direnv

```bash
cd New_devs_App
nix develop   # Enters the development shell
make help
```

## What Happens Automatically

When you enter the Nix environment (via direnv or `nix develop`):

1. ✅ Python 3.11 is available
2. ✅ `uv` package manager is installed
3. ✅ Node.js 20 and npm are available
4. ✅ PostgreSQL and Redis client tools are ready
5. ✅ Python virtual environment is created (if needed)
6. ✅ Frontend dependencies are installed (if needed)
7. ✅ All environment variables are set correctly
8. ✅ Project paths are configured

## Integration with Existing Workflow

**All existing commands still work:**
```bash
make back           # Run backend (unchanged)
make front          # Run frontend (unchanged)
make uv-install     # Install Python deps (unchanged)
make pre-commit     # Install pre-commit hooks (unchanged)
```

**New commands available:**
```bash
make help           # See all commands
make dev            # Run both backend and frontend
make docker-up      # Start all services
make clean          # Clean build artifacts
make test           # Run all tests
make lint           # Lint code
make format         # Format code
```

## Docker Still Works

The Nix environment doesn't replace Docker - it complements it:

```bash
# Option 1: Use Nix environment for local development
nix develop
make dev

# Option 2: Use Docker Compose for full stack
make docker-up

# Option 3: Mix and match
# Use Nix for tools, Docker for services
```

## File Structure

```
New_devs_App/
├── flake.nix              # Nix development environment definition
├── .envrc                 # Direnv automatic activation
├── .gitignore             # Updated with Nix patterns
├── Makefile               # Enhanced with new commands
├── NIX_SETUP.md           # Detailed setup documentation
├── DEVELOPMENT_ENVIRONMENT.md  # This file
├── backend/               # Python FastAPI backend
├── frontend/              # React TypeScript frontend
└── database/              # PostgreSQL schemas
```

## Updating the Environment

```bash
# Update Nix packages
nix flake update

# Update Python dependencies
cd backend && uv sync

# Update Node dependencies
cd frontend && npm update
```

## Troubleshooting

See `NIX_SETUP.md` for detailed troubleshooting steps.

**Common issues:**
- If direnv isn't loading: `direnv allow`
- If packages seem outdated: `nix flake update`
- To rebuild from scratch: `nix develop --rebuild`
- To reset everything: `make reset`

## Notes for Interviewers

This setup demonstrates:
- Modern development practices (IaC, reproducible builds)
- Cross-platform thinking
- Developer experience considerations
- Documentation skills
- Understanding of build systems and package management
- Professional project structure

The Nix setup is **optional** - the project still works with traditional methods (manual installs, Docker, etc.). This just makes it easier and more reliable.
