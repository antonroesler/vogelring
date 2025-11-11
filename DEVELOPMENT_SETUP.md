# Development Setup for Organization-Based Multi-Tenant Vogelring

## Quick Start

1. **Clone and start the development environment:**

```bash
git clone https://github.com/antonroesler/vogelring.git
cd vogelring
docker-compose up --build
```

2. **Run the organization migration:**

```bash
python run_migration.py
```

3. **Access the application:**

- Frontend: http://localhost
- API: http://localhost/api
- API Documentation: http://localhost/swagger

## Organization-Based Authentication

In development mode, authentication is automatically handled with a mock organization system:

### Default Development Setup

- **User Email**: `dev@vogelring.local`
- **User Name**: `Local Developer`
- **Organization**: `Development Organization` (auto-created)
- **Admin Status**: `false` (use setup_admin.py to enable)
- **Mode**: Automatic login (no Cloudflare Zero Trust required)

### Customizing Development User

Create a `.env` file in the project root:

```bash
# Development Authentication
DEVELOPMENT_MODE=true
DEV_USER_EMAIL=your-email@example.com
DEV_USER_NAME=Your Name

# Database Configuration
DB_PASSWORD=defaultpassword
LOG_LEVEL=DEBUG
```

### Multiple Development Organizations

To test with different organizations, change the environment variables and restart:

```bash
# Organization A
DEV_USER_EMAIL=alice@orgA.com DEV_USER_NAME="Alice Developer" docker-compose up

# Organization B
DEV_USER_EMAIL=bob@orgB.com DEV_USER_NAME="Bob Developer" docker-compose up
```

Each different email domain will create a separate organization automatically.

## Authentication Endpoints

### Check Current User

```bash
curl http://localhost/api/auth/me
```

### Authentication Status (Debug)

```bash
curl http://localhost/api/auth/status
```

## Production vs Development

| Feature            | Development           | Production            |
| ------------------ | --------------------- | --------------------- |
| Authentication     | Mock user system      | Cloudflare Zero Trust |
| User Creation      | Automatic             | From CF headers       |
| Headers Required   | None                  | `CF-Access-*` headers |
| Multi-user Testing | Environment variables | Real users            |

## Frontend User Display

The frontend now displays the current user in the header:

- **User Menu**: Click the user icon in the top-right
- **User Info**: Shows display name and email
- **Error Handling**: Shows authentication errors if any

## Database Schema

The multi-user implementation adds:

- **`users` table**: User profiles and authentication info
- **`user_id` columns**: Added to `ringings`, `sightings`, `bird_relationships`
- **Row Level Security**: PostgreSQL RLS policies for data isolation

## Development Workflow

1. **Start Development**: `docker-compose up --build`
2. **Check User**: Visit http://localhost and see user in header
3. **API Testing**: Use `/api/auth/me` to verify authentication
4. **Switch Users**: Change `DEV_USER_EMAIL` and restart
5. **Data Isolation**: Each user sees only their own data

## Troubleshooting

### User Not Showing in Header

- Check browser console for API errors
- Verify `/api/auth/me` returns user data
- Ensure `DEVELOPMENT_MODE=true` in environment

### Authentication Errors

- Check API logs: `docker-compose logs api`
- Verify database connection
- Ensure user table exists

### Database Issues

- Reset database: `docker-compose down -v && docker-compose up --build`
- Check PostgreSQL logs: `docker-compose logs postgres`

## Next Steps

Once multi-user is fully implemented:

1. **Add user_id to all tables**
2. **Implement Row Level Security**
3. **Update all repositories to filter by user**
4. **Test data isolation**
5. **Deploy to production with Cloudflare Zero Trust**
