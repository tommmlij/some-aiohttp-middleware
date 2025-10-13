# some-aiohttp-middleware

![Static Badge](https://img.shields.io/badge/Python-3.8%2B-brightgreen?logo=python)
![PyPI - Version](https://img.shields.io/pypi/v/some-aiohttp-middleware?logo=pypi&logoColor=yellow&color=brightgreen)
![PyPI - License](https://img.shields.io/pypi/l/some-aiohttp-middleware)
[![codecov](https://codecov.io/gh/tommmlij/some-aiohttp-middleware/graph/badge.svg?token=GDLHRPUVCG)](https://codecov.io/gh/tommmlij/some-aiohttp-middleware)
![Static Badge](https://img.shields.io/badge/mypy-checked-blue)
![Static Badge](https://img.shields.io/badge/flake8-linted-green)

A flexible and powerful middleware framework for aiohttp applications. This package provides a collection of reusable middlewares for common tasks like authentication, database connections, AWS services integration, and more.

## Features

- 🔐 **Authentication Middleware**: Support for Admin Auth (Bearer tokens) and Basic Auth
- 🗄️ **Database Integration**: PostgreSQL with SQLAlchemy async sessions
- ☁️ **AWS Services**: Easy integration with S3 and DynamoDB
- 🧩 **Extensible Base**: Create custom middleware by extending `MiddlewareBase`
- 🎯 **Flexible Application**: Use as app-level middleware or view decorators
- ⚡ **Async-First**: Built for modern async Python applications
- 🛡️ **Type Safe**: Fully typed with Pydantic validation

## Installation

```bash
pip install some-aiohttp-middleware
```

Or using Poetry:

```bash
poetry add some-aiohttp-middleware
```

## Quick Start

### Basic Usage with Middleware

```python
from aiohttp import web
from some_aiohttp_middleware import BasicAuth

# Create your app
app = web.Application()

# Add middleware
auth = BasicAuth(users={"admin": "password123"})
app.middlewares.append(auth.middleware())

# Your routes...
app.router.add_routes(...)
```

### Using as View Decorator

```python
from aiohttp import web
from some_aiohttp_middleware import AdminAuth

class ProtectedView(web.View):
    @AdminAuth.decorate(admin_token="your-secret-token")
    async def get(self):
        return web.json_response({"message": "Access granted!"})
```

## Available Middleware

### AdminAuth

Bearer token authentication middleware for admin endpoints.

**Usage:**

```python
from some_aiohttp_middleware import AdminAuth

# As middleware
auth = AdminAuth(admin_token="your-secret-token")
app.middlewares.append(auth.middleware())

# Or from app config
auth = AdminAuth(token_location=["admin_token"])  # Looks for app.config.admin_token
app.middlewares.append(auth.middleware())
```

**Features:**
- Bearer token validation
- Configurable token location in app config
- Proper HTTP error responses (401, 422)

### BasicAuth

HTTP Basic Authentication middleware with username/password validation.

**Usage:**

```python
from some_aiohttp_middleware import BasicAuth

# Direct user dictionary
users = {
    "admin": "password123",
    "user1": "secret456"
}
auth = BasicAuth(users=users)
app.middlewares.append(auth.middleware())

# Or from app config
auth = BasicAuth(users_location=["users"])  # Looks for app.config.users
app.middlewares.append(auth.middleware())
```

**Features:**
- Base64-encoded Basic Auth
- User dictionary validation
- Adds `request.authorization` with decoded credentials
- Proper HTTP error responses

### DB (PostgreSQL)

Database connection middleware using SQLAlchemy async sessions.

**Setup:**

```python
from some_aiohttp_middleware import Postgres, DB, DBConfig

# Configure database
db_config = DBConfig(
    host="localhost",
    port=5432,
    username="postgres",
    password="postgres",
    database="mydb",
    pool_size_max=50,
    pool_overflow=10
)

# Initialize Postgres context
postgres = Postgres(config=db_config, name="default")

# Add to app lifecycle
app.cleanup_ctx.append(postgres.ctx)

# Use middleware
db = DB()
app.middlewares.append(db.middleware(db_name="default"))
```

**Usage in handlers:**

```python
async def my_handler(request):
    # Access the session
    session = request["db_session"]["default"]
    
    # Use SQLAlchemy
    result = await session.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
    
    return web.json_response({"user": user.name})
```

**Features:**
- Automatic session management
- Connection pooling
- Multiple database support
- Automatic cleanup on exceptions

### S3

AWS S3 integration middleware using aioboto3.

**Setup:**

```python
from some_aiohttp_middleware import S3, S3Config

# Configure S3 bucket(s)
app.config.s3 = [
    S3Config(name="uploads", bucket="my-uploads-bucket", region="us-east-1"),
    S3Config(name="assets", bucket="my-assets-bucket", region="eu-west-1")
]

# Use middleware
s3 = S3()
app.middlewares.append(s3.middleware())
```

**Usage in handlers:**

```python
async def upload_handler(request):
    # Access S3 bucket
    bucket = request.app["s3"]["buckets"]["uploads"]
    
    # Upload file
    await bucket.upload_fileobj(file_data, "path/to/file.txt")
    
    return web.json_response({"status": "uploaded"})
```

**Environment Variables:**
- `S_UPLOADS_BUCKET`: Bucket name for "uploads"
- `S_UPLOADS_REGION`: Region for "uploads" (default: us-east-1)

### DynamoDB

AWS DynamoDB integration middleware.

**Setup:**

```python
from some_aiohttp_middleware import DynamoDB, DynamoDBConfig

# Configure DynamoDB table(s)
app.config.dynamodb = {
    "users": DynamoDBConfig(name="users", table="users-table", region="us-east-1"),
    "sessions": DynamoDBConfig(name="sessions", table="sessions-table", region="us-west-2")
}

# Use middleware
dynamodb = DynamoDB()
app.middlewares.append(dynamodb.middleware())
```

**Usage in handlers:**

```python
async def get_user(request):
    # Access DynamoDB client
    async with request["dynamodb"]["users"] as client:
        response = await client.get_item(
            TableName="users-table",
            Key={"id": {"S": "user123"}}
        )
    
    return web.json_response(response["Item"])
```

## Creating Custom Middleware

Extend the `MiddlewareBase` class to create your own middleware:

```python
from some_aiohttp_middleware import MiddlewareBase
from aiohttp.web import Request

class MyCustomMiddleware(MiddlewareBase):
    @staticmethod
    async def handle(request: Request, **kwargs) -> Request:
        # Pre-processing logic
        request["custom_data"] = "some value"
        return request
    
    @staticmethod
    async def unhandle(request: Request, response, **kwargs):
        # Post-processing/cleanup logic
        print(f"Request completed with status {response.status}")
        return response

# Use it
middleware = MyCustomMiddleware()
app.middlewares.append(middleware.middleware())
```

**Key Methods:**
- `handle(request, **kwargs)`: Called before the request handler (pre-processing)
- `unhandle(request, response, **kwargs)`: Called after the request handler (post-processing/cleanup)
- `middleware()`: Returns the aiohttp middleware function
- `decorate()`: Can be used as a view decorator

## Configuration

Most middleware support configuration through:

1. **Direct parameters**: Pass values when creating the middleware instance
2. **App config**: Store configuration in `app.config` and reference by location
3. **Environment variables**: Many configs support environment variable loading via Pydantic

### Example: Using App Config

```python
from aiohttp import web
from pydantic import BaseModel
from some_aiohttp_middleware import AdminAuth, BasicAuth

class AppConfig(BaseModel):
    admin_token: str = "secret-admin-token"
    users: dict[str, str] = {"admin": "password"}

app = web.Application()
app.config = AppConfig()

# Middleware will read from app.config
admin_auth = AdminAuth(token_location=["admin_token"])
basic_auth = BasicAuth(users_location=["users"])

app.middlewares.append(admin_auth.middleware())
app.middlewares.append(basic_auth.middleware())
```

## Requirements

- Python >= 3.9
- aiohttp ^3
- sqlalchemy ^2 (for DB middleware)
- asyncpg ^0 (for PostgreSQL)
- pydantic ^2
- pydantic-settings ^2
- aiohttp-pydantic ^2
- aioboto3 ^14 (for S3 middleware)
- aiobotocore (for DynamoDB middleware)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/tommmlij/some-aiohttp-middleware.git
cd some-aiohttp-middleware

# Install dependencies with Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=some_aiohttp_middleware --cov-report=html

# Run specific test file
pytest tests/test_basic_auth.py
```

### Code Quality

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint
flake8 src/

# Type check
mypy src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **PyPI**: https://pypi.org/project/some-aiohttp-middleware/
- **GitHub**: https://github.com/tommmlij/some-aiohttp-middleware
- **Issues**: https://github.com/tommmlij/some-aiohttp-middleware/issues
- **Coverage**: https://codecov.io/gh/tommmlij/some-aiohttp-middleware

## Author

**tommmlij** - [tommmlij@gmail.com](mailto:tommmlij@gmail.com)
