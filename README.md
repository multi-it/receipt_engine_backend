# Receipt Management API

REST API for creating and managing receipts with user authentication.

## Features

- User registration and authentication with JWT tokens
- Receipt creation and management
- Receipt filtering and pagination
- Public receipt text view
- PostgreSQL data storage
- Comprehensive test coverage
- Docker containerization

## Technologies

- **FastAPI** - Modern web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **JWT** - Authentication tokens
- **Alembic** - Database migrations
- **Pytest** - Testing framework
- **Docker** - Containerization

## Quick Start

```
git clone https://github.com/multi-it/receipt_engine_backend
cd receipt_engine_backend
./10_up_with_docker_compose.sh
./20_run_pytest.sh
./30_demo_system_with_curl.sh
```

### Local Development

1. Clone repository:

```
git clone https://github.com/multi-it/receipt_engine_backend
cd receipt_engine_backend
```

2. Create virtual environment:

```
python -m venv venv
source venv/bin/activate # Linux/macOS
venv\Scripts\activate # Windows
```

3. Install dependencies:

```
pip install -e .
pip install -e ".[test]" # For testing
```

4. Configure environment variables:

```
cp .env.example .env
```

# Edit .env file with your settings

5. Apply migrations:

```
alembic upgrade head
```

6. Run server:

```
uv run uvicorn main:app --reload
```

### Docker Deployment

1. Start all services:

```
docker-compose up -d
```

2. Apply migrations (if needed):

```
docker-compose exec app alembic upgrade head
```

## API Documentation

After starting the server, documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

Run all tests:
```
uv run pytest
```

Run with coverage:

```
uv run pytest --cov=app tests/
```

## Project Structure

```
receipt_engine_backend/
├── app/                    # Main application code
│   ├── api/               # API endpoints
│   ├── auth/              # Authentication and security
│   ├── database/          # Database connection and models
│   ├── domain/            # Domain entities and schemas
│   └── services/          # Business logic
├── tests/                 # Tests
├── alembic/               # Database migrations
├── docker-compose.yml     # Docker configuration
├── Dockerfile             # Docker image
└── main.py               # Application entry point
```

## API Endpoints

### Authentication
- POST /auth/register - User registration
- POST /auth/login - User login

### Receipts
- POST /receipts/ - Create receipt
- GET /receipts/ - Get receipts list with filtering and pagination
- GET /receipts/{id} - Get receipt by ID

### Public
- GET /public/receipts/{id} - Public receipt text view

## Usage Examples

### User Registration

```
curl -X POST "http://localhost:8000/auth/register"   -H "Content-Type: application/json"   -d '{
    "fullname": "Test User",
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```
other examples see in 
```
./30_demo_system_with_curl.sh
```

## Production Deployment

For production deployment, it's recommended to:

1. Use external PostgreSQL database
2. Configure SSL certificates
3. Use reverse proxy (nginx)
4. Set up monitoring and logging

## Support

For questions and support, please create an issue in the repository.
