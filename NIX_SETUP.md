# Nix Development Environment Setup

This document explains how to use the Nix flake development environment for the Base360 project.

## Prerequisites

1. **Install Nix** with flakes enabled:
   ```bash
   # On macOS/Linux
   curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
   ```

2. **Install direnv** (recommended for automatic environment loading):
   ```bash
   # macOS
   brew install direnv
   
   # Or with Nix
   nix profile install nixpkgs#direnv
   ```

3. **Configure direnv** in your shell:
   ```bash
   # For bash, add to ~/.bashrc:
   eval "$(direnv hook bash)"
   
   # For zsh, add to ~/.zshrc:
   eval "$(direnv hook zsh)"
   
   # For fish, add to ~/.config/fish/config.fish:
   direnv hook fish | source
   ```

## Quick Start

### Option 1: Using direnv (Recommended)

1. Navigate to the New_devs_App directory:
   ```bash
   cd /path/to/New_devs_App
   ```

2. Allow direnv to load the environment:
   ```bash
   direnv allow
   ```

3. The environment will automatically load! You'll see a welcome message with available commands.

### Option 2: Manual Nix Shell

If you prefer not to use direnv, you can manually enter the Nix shell:

```bash
cd /path/to/New_devs_App
nix develop
```

## What's Included

The Nix development environment provides:

### Backend (Python)
- Python 3.11
- `uv` - Fast Python package manager
- PostgreSQL 15 client tools
- Redis client tools

### Frontend (Node.js)
- Node.js 20
- npm, pnpm package managers

### Development Tools
- Git
- Make
- Docker & Docker Compose
- pre-commit
- curl, wget, jq
- OpenSSL

## Available Development Shells

### Default Shell (Full Stack)
```bash
nix develop
```
This loads everything you need for full-stack development.

### Backend Only
```bash
nix develop .#backend
```
Lighter shell with only Python and backend dependencies. Automatically changes to the `backend/` directory.

### Frontend Only
```bash
nix develop .#frontend
```
Lighter shell with only Node.js and frontend dependencies. Automatically changes to the `frontend/` directory.

## Environment Variables

The Nix shell automatically configures:

- `PYTHONPATH` - Includes backend directory
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `PGDATA`, `PGHOST`, `PGPORT` - PostgreSQL configuration
- `UV_PYTHON` - Python interpreter for uv
- `NODE_ENV=development`

## Getting Started with Development

Once in the Nix shell, you can use the project's Makefile commands:

### Install Dependencies

```bash
# Install Python backend dependencies
make uv-install

# Install frontend dependencies (done automatically on shell entry)
cd frontend && npm install
```

### Run Services Individually

```bash
# Run backend server (http://localhost:8000)
make back

# Run frontend dev server (http://localhost:3000)
make front
```

### Run with Docker Compose

```bash
# Start all services (backend, frontend, database, redis)
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop services
docker-compose down
```

## Database Setup

### Using Docker Compose (Recommended)
The easiest way is to use the provided Docker Compose setup:

```bash
docker-compose up db
```

This automatically:
- Creates the `propertyflow` database
- Runs `database/schema.sql` to set up tables
- Runs `database/seed.sql` to populate initial data

### Using Local PostgreSQL
If you prefer to run PostgreSQL locally:

```bash
# Initialize a local database
initdb -D .nix-postgres

# Start PostgreSQL
pg_ctl -D .nix-postgres -l logfile start

# Create database and load schema
createdb propertyflow
psql propertyflow < database/schema.sql
psql propertyflow < database/seed.sql
```

## Troubleshooting

### Direnv not loading automatically
```bash
# Check if direnv is properly hooked
direnv status

# Re-allow the directory
direnv allow
```

### Python dependencies not installing
```bash
# Clear the virtual environment and recreate
rm -rf backend/.venv
cd backend
uv venv
uv sync
```

### Node modules issues
```bash
# Clear and reinstall
rm -rf frontend/node_modules
cd frontend
npm install
```

### Nix flake evaluation errors
```bash
# Update flake inputs
nix flake update

# Check flake
nix flake check

# Rebuild environment
nix develop --rebuild
```

### Port conflicts
If ports 8000, 3000, 5433, or 6380 are already in use:

1. Check what's using the port:
   ```bash
   lsof -i :8000  # or :3000, :5433, :6380
   ```

2. Either stop the conflicting service or modify `docker-compose.yml` to use different ports.

## Updating Dependencies

### Update Nix Flake
```bash
nix flake update
```

### Update Python Dependencies
```bash
cd backend
# Edit pyproject.toml, then:
uv sync
```

### Update Frontend Dependencies
```bash
cd frontend
npm update
```

## Benefits of Using Nix

1. **Reproducibility** - Everyone gets the exact same development environment
2. **Isolation** - No conflicts with system packages
3. **Declarative** - Environment is defined in code (flake.nix)
4. **Cross-platform** - Works on macOS, Linux, and WSL2
5. **No global installs** - Everything is project-specific
6. **Fast switching** - Easy to switch between projects

## Additional Resources

- [Nix Flakes Documentation](https://nixos.wiki/wiki/Flakes)
- [direnv Documentation](https://direnv.net/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Project-specific README](ASSIGNMENT.md)

## Support

If you encounter issues with the Nix setup:

1. Check this documentation
2. Verify prerequisites are installed
3. Try rebuilding: `nix develop --rebuild`
4. Check the flake.nix file for environment configuration