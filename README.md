# 📘 Blue-Booking Web Application 📘

[Bluebooking](https://thealexandrian.net/wordpress/40005/roleplaying-games/ptolus-running-the-campaign-bluebooking) is a traditional TTRPG technique allowing for role-playing outside of main game sessions. This web application brings that experience online, functioning similarly to a collaborative blogging platform for gaming groups.

## 📋 Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Docker Setup](#docker-setup)
- [Contribution Guide](#contribution-guide)
- [Testing & QA](#testing--qa)
- [Troubleshooting](#troubleshooting)

## ⚙️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML** | Standard markup language |
| **Tailwind CSS** | Utility-first CSS framework for styling |
| **HTMX** | Dynamic page updates without full reloads |
| **TypeScript** | Typed JavaScript for better editor support |
| **Alpine.js** | Lightweight JavaScript framework for interactivity |
| **Webpack** | Module bundler for JavaScript/TypeScript |

### Backend
| Technology | Purpose |
|------------|---------|
| **Django** | Full-featured Python web framework |
| **Django-allauth** | Authentication and account management |
| **Django-htmx** | HTMX utilities for Django |
| **Django-tailwind** | Tailwind CSS integration |
| **Django-webpack-loader** | Webpack integration |

### Server Infrastructure
| Component | Purpose |
|-----------|---------|
| **Uvicorn** | ASGI server for async Django |
| **Nginx** | Reverse proxy and static file server |
| **PostgreSQL** | Production database |
| **SQLite** | Development database |

### Testing & Quality Assurance
| Tool | Purpose |
|------|---------|
| **pytest** | Testing framework |
| **coverage** | Test coverage reporting |
| **pylint** | Code quality linting |
| **black** | Code formatting |

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Client["Client Side"]
        Browser["User Browser"]
        HTMX["HTMX for Dynamic Updates"]
        Alpine["Alpine.js for Interactivity"]
        Tailwind["Tailwind CSS Styling"]
    end

    subgraph Docker["Docker Container Environment"]
        subgraph Nginx["Nginx Proxy"]
            StaticServer["Static File Server"]
            ReverseProxy["Reverse Proxy"]
        end

        subgraph WebApp["Django Application"]
            Uvicorn["Uvicorn ASGI Server"]
            DjangoApp["Django App with Webpack Loader"]
            TailwindCSS["Django-tailwind"]
        end
    end

    subgraph DatabaseLayer["Database Layer"]
        Postgres[("PostgreSQL<br>Production")]
        SQLite[("SQLite<br>Development")]
    end

    Browser --> Nginx
    Nginx --> StaticServer
    Nginx --> ReverseProxy
    ReverseProxy --> Uvicorn
    Uvicorn --> DjangoApp
    DjangoApp --> TailwindCSS
    DjangoApp --> DatabaseLayer
    DatabaseLayer --> Postgres
    DatabaseLayer --> SQLite
```

## 🚀 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn
- Git

### Quick Start

<details>
<summary><b>Click to expand: Local Development Setup</b></summary>

#### 1. Clone the Repository
```bash
git clone https://github.com/CaptainSpaceCadet/blue-booking-app.git
cd blue-booking-app
```

#### 2. Set Up Python Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Install Node.js Dependencies
```bash
npm install
```

#### 5. Configure Environment Variables
Create a `.env` file in the project root:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-development-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Optional: Use PostgreSQL locally
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

#### 6. Run Database Migrations
```bash
python manage.py migrate
```

#### 7. Build Frontend Assets
```bash
# Tailwind CSS (watch mode for development)
python manage.py tailwind start &

# Webpack (watch mode for development)
npx webpack --mode=development --watch &

# Or build once
python manage.py tailwind build
npx webpack --mode=development
```

#### 8. Start the Development Server
```bash
python manage.py runserver
```

Access the application at: http://localhost:8000

#### 9. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

</details>

## 🐳 Docker Setup

<details>
<summary><b>Click to expand: Docker Development & Production</b></summary>

### Prerequisites
- Docker Desktop 4.28+
- Docker Compose V2

### Development with Docker

#### 1. Clone the Repository
```bash
git clone https://github.com/CaptainSpaceCadet/blue-booking-app.git
cd blue-booking-app
```

#### 2. Configure Environment
Create `.env.production` (for production) or `.env` (auto-loaded):

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# PostgreSQL Settings
POSTGRES_USER=blue_booking_user
POSTGRES_PASSWORD=your-strong-password-here
POSTGRES_DB=blue_booking_db

# pgAdmin Settings (optional)
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=your-pgadmin-password

# Database URL (auto-generated from above)
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
```

#### 3. Build and Start Containers
```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Check running containers
docker compose ps
```

#### 4. Run Database Migrations
```bash
docker compose exec web python manage.py migrate
```

#### 5. Create Superuser
```bash
docker compose exec web python manage.py createsuperuser
```

#### 6. Access Services
| Service | URL |
|---------|-----|
| Django App (via Nginx) | http://localhost |
| Django App (Direct) | http://localhost:8000 |
| pgAdmin | http://localhost:5050 |

#### 7. Common Docker Commands
```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v

# Rebuild after changes
docker compose up -d --build

# SSH into web container
docker compose exec web bash

# Run Django commands
docker compose exec web python manage.py [command]

# Backup database
docker compose exec db pg_dump -U blue_booking_user blue_booking_db > backup.sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U blue_booking_user blue_booking_db
```

### Production Deployment with Docker

#### 1. Build Production Images
```bash
# Build optimized production images
docker compose -f docker-compose.yml build --no-cache
```

#### 2. Deploy
```bash
# Start in production mode
DEBUG=False docker compose up -d

# Or use a production-specific compose file
docker compose -f docker-compose.prod.yml up -d
```

#### 3. Monitoring
```bash
# View logs
docker compose logs -f

# Check resource usage
docker stats

# Monitor database
docker compose exec db psql -U blue_booking_user -d blue_booking_db
```

### Production Optimizations

| Feature | Implementation |
|---------|---------------|
| **Static Files** | Nginx serves from STATIC_ROOT |
| **Database** | PostgreSQL with persistent volumes |
| **Caching** | Redis (optional) or Django cache |
| **Workers** | Multiple Uvicorn workers |
| **Health Checks** | Database health checks |
| **Security** | Non-root user in containers |

</details>

## 🧪 Testing & QA

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
coverage run -m pytest
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html
```

### Code Quality
```bash
# Lint code
pylint blue_booking_app

# Format code
black .

# Check formatting
black --check .
```

### Pre-commit Hooks (Optional)
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 🤝 Contribution Guide

### Git Workflow

#### Branch Strategy
```mermaid
gitGraph
    commit
    branch develop
    checkout develop
    commit
    branch feature/new-feature
    checkout feature/new-feature
    commit
    commit
    checkout develop
    merge feature/new-feature
    checkout main
    merge develop tag: "v1.0.0"
```

| Branch | Purpose | From | To |
|--------|---------|------|----|
| `main` | Production-ready code | - | - |
| `develop` | Integration branch | `main` | `main` |
| `feature/*` | New features | `develop` | `develop` |
| `fix/*` | Bug fixes | `develop` | `develop` |
| `hotfix/*` | Production hotfixes | `main` | `main` & `develop` |

### Commit Conventions
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: add user authentication
fix: resolve login redirect issue
docs: update API documentation
style: format code with black
refactor: restructure campaign module
test: add unit tests for forms
chore: update dependencies
```

### Pull Request Process
1. Create feature/fix branch from `develop`
2. Write tests for new functionality
3. Run test suite: `pytest`
4. Run code quality checks: `pylint` and `black`
5. Create PR with clear description
6. Pass CI/CD checks (GitHub Actions)
7. Get code review approval
8. Merge to `develop`

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><b>Static Files Not Loading</b></summary>

**Solution:**
```bash
# Rebuild static files
python manage.py tailwind build
npx webpack --mode=production
python manage.py collectstatic --noinput

# Or with Docker
docker compose exec web python manage.py collectstatic --noinput
```
</details>

<details>
<summary><b>Database Connection Issues</b></summary>

**Solution:**
```bash
# Check if PostgreSQL is running
docker compose ps db

# Check logs
docker compose logs db

# Reset database (WARNING: deletes data)
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
```
</details>

<details>
<summary><b>Webpack Build Failing</b></summary>

**Solution:**
```bash
# Clean and rebuild
rm -rf assets/webpack_bundles/
rm -rf node_modules/
npm install
npx webpack --mode=development
```
</details>

<details>
<summary><b>Port Conflicts</b></summary>

**Solution:**
```bash
# Check what's using port 80/8000/5432
sudo lsof -i :80
sudo lsof -i :8000

# Change ports in docker-compose.yml
ports:
  - "8080:80"  # Change host port
```
</details>

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [HTMX Documentation](https://htmx.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Webpack Documentation](https://webpack.js.org/concepts/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments
- [The Alexandrian](https://thealexandrian.net/) for the bluebooking concept
