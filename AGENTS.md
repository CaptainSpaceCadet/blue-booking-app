# AGENTS.md

## 🎯 Project Overview

**Blue-Booking Web Application** is a Django-based platform for TTRPG bluebooking - a technique allowing players to continue role-playing between game sessions through written scenes and character interactions.

**Repository**: https://github.com/CaptainSpaceCadet/blue-booking-app

---

## 🤖 Agent Instructions & Guidelines

### Project Context
This is a full-stack web application using Django + HTMX with modern frontend tooling. The application functions similarly to a collaborative blogging platform for gaming groups, allowing users to write in-character scenes, interact with NPCs, and continue storytelling between main game sessions.

### Key Technologies
- **Backend**: Django 6.0, Django-allauth (authentication), Django-htmx
- **Frontend**: HTMX, Alpine.js, Tailwind CSS, TypeScript, Webpack
- **Database**: PostgreSQL (production), SQLite (development)
- **Server**: Uvicorn (ASGI), Nginx (reverse proxy/static files)
- **Containerization**: Docker, Docker Compose
- **Testing**: pytest, coverage
- **Code Quality**: pylint, black

---

## 🏗️ Architecture

```
Browser
   ↓
Nginx (Port 80)
   ├── /static/ → Static files
   ├── /media/ → User uploads
   └── / → Reverse proxy
         ↓
   Uvicorn (ASGI Server)
         ↓
   Django Application
         ├── Apps:
         │   ├── core
         │   ├── accounts
         │   ├── campaigns
         │   ├── personas
         │   └── posts
         ├── Django-allauth (authentication)
         ├── Django-htmx (HTMX utilities)
         ├── Django-tailwind (CSS)
         └── Webpack Loader (JS bundling)
         ↓
   PostgreSQL Database
```

---

## 🚀 Development Setup

### Local Development (No Docker)

```bash
# Clone repository
git clone https://github.com/CaptainSpaceCadet/blue-booking-app.git
cd blue-booking-app

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
npm install

# Set up environment
cp .env.example .env
# Edit .env with your settings (DEBUG=True for development)

# Run migrations
python manage.py migrate

# Build frontend (development mode)
python manage.py tailwind start &  # Tailwind watch mode
npx webpack --mode=development --watch  # Webpack watch mode

# Run server
python manage.py runserver
```

### Docker Development

```bash
# Build and start all services
docker compose up -d --build

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Access services
# App: http://localhost (via Nginx)
# Direct: http://localhost:8000
# pgAdmin: http://localhost:5050
```

---

## 📁 Project Structure

```
blue-booking-app/
├── apps/                          # Django apps
│   ├── accounts/                  # User authentication & profiles
│   ├── campaigns/                 # Campaign management
│   ├── core/                      # Core functionality
│   ├── personas/                  # Character/persona management
│   └── posts/                     # Bluebooking posts
├── assets/                        # Frontend assets (Webpack)
├── blue_booking_app/              # Django project configuration
│   ├── settings.py                # Main settings
│   ├── urls.py                    # URL configuration
│   └── asgi.py                    # ASGI configuration
├── static/                        # Static files
├── templates/                     # Django templates
├── theme/                         # Django-tailwind theme
├── docker/                        # Docker files
│   ├── web/
│   └── nginx/
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile                     # Main Docker image
├── nginx.conf                     # Nginx configuration
├── entrypoint.sh                  # Container entrypoint
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
├── package.json                   # Node.js dependencies
└── .env.production                # Production environment variables
```

---

## 🔄 Development Workflow

### Git Branches
- **`main`**: Production-ready code
- **`develop`**: Integration branch (default base)
- **`feature/*`**: New features
- **`fix/*`**: Bug fixes
- **`hotfix/*`**: Production hotfixes

### Commit Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add user authentication
fix: resolve login redirect issue
docs: update API documentation
style: format code with black
refactor: restructure campaign module
test: add unit tests for forms
chore: update dependencies
```

### Pull Request Process
1. Create branch from `develop`
2. Write tests for new functionality
3. Run test suite: `pytest`
4. Run code quality checks: `pylint` and `black`
5. Create PR with clear description
6. Pass CI/CD checks
7. Get code review approval
8. Merge to `develop`

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
coverage run -m pytest
coverage report
coverage html  # View at htmlcov/index.html
```

### Code Quality
```bash
# Linting
pylint blue_booking_app

# Formatting
black .
black --check .  # Check only
```

---

## 🐳 Docker Environment

### Services
| Service | Port | Purpose |
|---------|------|---------|
| Nginx | 80 | Reverse proxy, static files |
| Django (Uvicorn) | 8000 | Application server |
| PostgreSQL | 5432 | Database |
| pgAdmin | 5050 | Database management UI |

### Environment Variables
Required variables in `.env.production`:
```env
# Django
DEBUG=False
SECRET_KEY=<your-secret-key>
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_USER=blue_booking_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=blue_booking_db
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

# pgAdmin (optional)
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=<pgadmin-password>
```

### Common Docker Commands
```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f [service]

# Run Django commands
docker compose exec web python manage.py [command]

# Stop
docker compose down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v

# Backup database
docker compose exec db pg_dump -U blue_booking_user blue_booking_db > backup.sql
```

---

## 🔧 Troubleshooting

### Static Files Not Loading
```bash
python manage.py tailwind build
npx webpack --mode=production
python manage.py collectstatic --noinput
```

### Docker PostgreSQL Not Starting
```bash
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
```

### Webpack Build Failing
```bash
rm -rf node_modules/ assets/webpack_bundles/
npm install
npx webpack --mode=development
```

### Nginx Bad Gateway
```bash
# Check if Django is running
docker compose ps web
docker compose logs web

# Test Django directly
curl http://localhost:8000

# Check Nginx configuration
docker compose exec nginx nginx -t
```

---

## 📚 Development Tips

### Adding a New Django App
```bash
python manage.py startapp new_app apps/new_app
# Add 'apps.new_app' to INSTALLED_APPS in settings.py
```

### Adding Static Assets
1. **For Tailwind**: Add classes in templates, run `python manage.py tailwind build`
2. **For JavaScript**: Import in TypeScript files, Webpack handles bundling

### Database Models
- Store models in `apps/<app_name>/models.py`
- Run `python manage.py makemigrations` then `python manage.py migrate`

### Templates
- Base templates in `templates/` directory
- App-specific templates in `apps/<app_name>/templates/`

---

## 🎯 Feature Areas

### Core App (`apps.core`)
- Shared utilities and base functionality
- Common models and mixins
- Site-wide components

### Accounts App (`apps.accounts`)
- User authentication (allauth)
- User profiles
- Profile management views
- Custom signup form

### Campaigns App (`apps.campaigns`)
- Campaign creation and management
- Campaign membership
- Campaign settings and roles
- Member limits (25 per campaign)

### Personas App (`apps.personas`)
- Character/persona creation
- Persona management
- Player-persona relationships
- Limit: 10 personas per player

### Posts App (`apps.posts`)
- Bluebooking post creation
- Post viewing and editing
- Character associations
- Threaded conversations

---

## 🔒 Security Considerations

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Production**:
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS`
   - Use PostgreSQL (not SQLite)
   - Enable HTTPS in production
3. **Django-allauth**: Configure social providers securely
4. **Docker**: Run as non-root user (appuser)

---

## 📖 Useful Commands Cheat Sheet

### Django
```bash
python manage.py runserver              # Development server
python manage.py migrate                 # Apply migrations
python manage.py makemigrations          # Create migrations
python manage.py createsuperuser         # Create admin user
python manage.py shell                   # Django shell
python manage.py tailwind build          # Build Tailwind CSS
python manage.py collectstatic           # Collect static files
```

### Frontend
```bash
npm install                              # Install Node dependencies
npx webpack --mode=development           # Build webpack (dev)
npx webpack --mode=production            # Build webpack (prod)
python manage.py tailwind start          # Tailwind watch mode
```

### Docker
```bash
docker compose up -d                     # Start services
docker compose down                      # Stop services
docker compose ps                        # List containers
docker compose logs -f web               # View web logs
docker compose exec web bash             # SSH into web container
```

---

## 📝 Final Notes

- **Always** run tests before creating a PR
- **Maintain** code quality standards (pylint score > 8.0, coverage > 80%)
- **Document** new features and API changes
- **Update** README.md when adding major features
- **Use** the issue tracker for bug reports and feature requests

---

**Built with ❤️ using Django, HTMX, and Tailwind CSS**