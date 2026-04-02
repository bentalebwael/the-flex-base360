{
  description = "Base360 Development Environment - Full-stack Property Management System";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        # Python 3.11 (minimal, no extra packages to avoid conflicts)
        python = pkgs.python311;

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python backend dependencies
            python
            uv  # Fast Python package installer and resolver

            # Node.js frontend dependencies (npm is included with nodejs_20)
            nodejs_20

            # Database and services
            postgresql_15
            redis

            # Docker and container tools
            docker
            docker-compose

            # Development tools
            git
            gnumake
            jq
            curl
            wget

            # SSL/TLS tools
            openssl

            # Additional utilities
            which
            gnused
            coreutils
          ];

          shellHook = ''
            echo "🚀 Base360 Development Environment Activated"
            echo ""
            echo "Available tools:"
            echo "  - Python ${python.version} (with uv package manager)"
            echo "  - Node.js $(node --version)"
            echo "  - PostgreSQL $(postgres --version | head -n1)"
            echo "  - Redis $(redis-server --version)"
            echo "  - Docker $(docker --version)"
            echo ""
            echo "Project structure:"
            echo "  📁 Current directory (New_devs_App)"
            echo "    ├── backend/     (Python FastAPI)"
            echo "    ├── frontend/    (React TypeScript)"
            echo "    └── database/    (PostgreSQL schemas)"
            echo ""
            echo "Quick start commands:"
            echo "  make uv-install  - Install Python dependencies"
            echo "  make back        - Run backend server"
            echo "  make front       - Run frontend dev server"
            echo ""
            echo "  Or use docker-compose:"
            echo "  docker-compose up - Start all services"
            echo ""

            # Set up environment variables
            export PYTHONPATH="$PWD/backend:$PYTHONPATH"
            export NODE_ENV=development

            # Add local bin directories to PATH
            export PATH="$PWD/backend/.venv/bin:$PATH"
            export PATH="$PWD/frontend/node_modules/.bin:$PATH"

            # PostgreSQL configuration
            export PGDATA="$PWD/.nix-postgres"
            export PGHOST="localhost"
            export PGPORT="5433"
            export PGDATABASE="propertyflow"
            export PGUSER="postgres"
            export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/propertyflow"

            # Redis configuration
            export REDIS_URL="redis://localhost:6380/0"

            # Python/uv configuration
            export UV_PYTHON="${python.interpreter}"
            export UV_PROJECT_ENVIRONMENT="$PWD/backend/.venv"

            # Create .venv if it doesn't exist
            if [ ! -d "backend/.venv" ]; then
              echo "📦 Creating Python virtual environment..."
              cd backend && ${pkgs.uv}/bin/uv venv && cd ..
            fi

            # Install frontend dependencies if needed
            if [ ! -d "frontend/node_modules" ]; then
              echo "📦 Installing frontend dependencies..."
              cd frontend && npm install && cd ..
            fi

            echo "✅ Environment ready!"
          '';

          # Environment variables
          env = {
            # Prevent Python from writing bytecode
            PYTHONDONTWRITEBYTECODE = "1";
            # Force UTF-8 encoding
            PYTHONIOENCODING = "utf-8";
            # Enable Python development mode
            PYTHONDEVMODE = "1";
          };
        };

        # Additional shells for specific purposes
        devShells.backend = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            uv
            postgresql_15
            redis
          ];

          shellHook = ''
            echo "🐍 Backend Development Shell"
            export PYTHONPATH="$PWD/backend:$PYTHONPATH"
            export UV_PYTHON="${python.interpreter}"
            cd backend
          '';
        };

        devShells.frontend = pkgs.mkShell {
          buildInputs = with pkgs; [
            nodejs_20
          ];

          shellHook = ''
            echo "⚛️  Frontend Development Shell"
            cd frontend
          '';
        };
      }
    );
}
