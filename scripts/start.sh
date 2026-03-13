#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/settings/.env"

# ──────────────────────────────────────────────
# STEP 1 — Check required env vars
# ──────────────────────────────────────────────
info "Step 1: Checking environment variables..."

if [ ! -f "$ENV_FILE" ]; then
    error "Missing .env file at $ENV_FILE. Copy settings/.env.example to settings/.env and fill in the values."
fi

while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    export "$key=$value"
done < "$ENV_FILE"

REQUIRED_VARS=(BLOG_SECRET_KEY BLOG_DEBUG BLOG_REDIS_URL BLOG_ALLOWED_HOSTS)
for var in "${REQUIRED_VARS[@]}"; do
    val=$(printenv "$var" || true)
    if [ -z "$val" ]; then
        error "Missing required environment variable: $var"
    fi
done

info "All required environment variables are set."

# ──────────────────────────────────────────────
# STEP 2 — Virtual environment & dependencies
# ──────────────────────────────────────────────
info "Step 2: Setting up virtual environment..."

cd "$PROJECT_ROOT"
VENV_DIR="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    info "Virtual environment created."
else
    warn "Virtual environment already exists, skipping."
fi

source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -r requirements/base.txt
info "Dependencies installed."

# ──────────────────────────────────────────────
# STEP 3 — Migrations
# ──────────────────────────────────────────────
info "Step 3: Running migrations..."
python manage.py migrate --no-input
info "Migrations complete."

# ──────────────────────────────────────────────
# STEP 4 — Static files
# ──────────────────────────────────────────────
info "Step 4: Collecting static files..."
python manage.py collectstatic --no-input --clear 2>/dev/null || true
info "Static files collected."

# ──────────────────────────────────────────────
# STEP 5 — Compile translations
# ──────────────────────────────────────────────
info "Step 5: Compiling translation files..."
python manage.py compilemessages 2>/dev/null || warn "compilemessages failed (gettext may not be installed)"

# ──────────────────────────────────────────────
# STEP 6 — Create superuser
# ──────────────────────────────────────────────
info "Step 6: Creating superuser..."
SUPERUSER_EMAIL="admin@blog.local"
SUPERUSER_PASSWORD="Admin1234!"

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$SUPERUSER_EMAIL',
        password='$SUPERUSER_PASSWORD',
        first_name='Admin',
        last_name='User',
    )
    print('Superuser created.')
else:
    print('Superuser already exists, skipping.')
"

# ──────────────────────────────────────────────
# STEP 7 — Seed test data
# ──────────────────────────────────────────────
info "Step 7: Seeding test data..."
python manage.py shell -c "
from apps.blog.models import Category, Tag, Post, Comment, PostStatus
from django.contrib.auth import get_user_model
User = get_user_model()

# Users
users_data = [
    ('alice@blog.local', 'Alice', 'Smith', 'en', 'UTC'),
    ('bob@blog.local',   'Bob',   'Jones', 'ru', 'Europe/Moscow'),
    ('carol@blog.local', 'Carol', 'Lee',   'kk', 'Asia/Almaty'),
]
for email, fn, ln, lang, tz in users_data:
    u, created = User.objects.get_or_create(email=email, defaults={
        'first_name': fn, 'last_name': ln,
        'preferred_language': lang, 'timezone': tz,
    })
    if created:
        u.set_password('Test1234!')
        u.save()
print(f'Users: {User.objects.count()}')

# Categories
cats_data = [
    ('Technology', 'Технологии', 'Технология', 'technology'),
    ('Science',    'Наука',      'Ғылым',      'science'),
    ('Culture',    'Культура',   'Мәдениет',   'culture'),
]
cats = []
for en, ru, kk, slug in cats_data:
    c, _ = Category.objects.get_or_create(slug=slug, defaults={
        'name_en': en, 'name_ru': ru, 'name_kk': kk,
    })
    cats.append(c)
print(f'Categories: {Category.objects.count()}')

# Tags
tags = []
for name in ['python', 'django', 'api', 'rest', 'async', 'redis']:
    t, _ = Tag.objects.get_or_create(slug=name, defaults={'name': name})
    tags.append(t)
print(f'Tags: {Tag.objects.count()}')

# Posts
admin = User.objects.get(email='admin@blog.local')
posts_data = [
    ('Hello World',        'hello-world',        PostStatus.PUBLISHED),
    ('Django REST Tips',   'django-rest-tips',   PostStatus.PUBLISHED),
    ('Async Python Guide', 'async-python-guide', PostStatus.PUBLISHED),
    ('Draft Post 1',       'draft-post-1',       PostStatus.DRAFT),
    ('Draft Post 2',       'draft-post-2',       PostStatus.DRAFT),
    ('Redis Pub/Sub',      'redis-pubsub',       PostStatus.PUBLISHED),
    ('Kazakh Culture',     'kazakh-culture',     PostStatus.PUBLISHED),
    ('Science Today',      'science-today',      PostStatus.PUBLISHED),
    ('Tech Trends 2024',   'tech-trends-2024',   PostStatus.PUBLISHED),
    ('API Design',         'api-design',         PostStatus.PUBLISHED),
    ('Testing Django',     'testing-django',     PostStatus.PUBLISHED),
    ('Celery Basics',      'celery-basics',      PostStatus.PUBLISHED),
]
all_posts = []
for title, slug, status in posts_data:
    p, _ = Post.objects.get_or_create(slug=slug, defaults={
        'title': title, 'body': f'Body of {title}. ' * 10,
        'author': admin, 'status': status,
        'category': cats[0],
    })
    p.tags.set(tags[:3])
    all_posts.append(p)
print(f'Posts: {Post.objects.count()}')

# Comments
pub_posts = [p for p in all_posts if p.status == PostStatus.PUBLISHED]
for post in pub_posts[:5]:
    for j in range(3):
        Comment.objects.get_or_create(
            post=post, author=admin,
            body=f'Comment {j+1} on post {post.slug}',
        )
print(f'Comments: {Comment.objects.count()}')
print('Seed complete.')
" 2>&1 | tail -20

# ──────────────────────────────────────────────
# STEP 8 — Start server
# ──────────────────────────────────────────────
info "Step 8: Starting development server..."

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  Blog API is ready!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  API:       http://localhost:8000/api/"
echo -e "  Swagger:   http://localhost:8000/api/docs/"
echo -e "  ReDoc:     http://localhost:8000/api/redoc/"
echo -e "  Admin:     http://localhost:8000/admin/"
echo -e "  Stats:     http://localhost:8000/api/stats/"
echo ""
echo -e "  Superuser: ${YELLOW}$SUPERUSER_EMAIL${NC}"
echo -e "  Password:  ${YELLOW}$SUPERUSER_PASSWORD${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

exec uvicorn settings.asgi:application --host 127.0.0.1 --port 8000 --reload