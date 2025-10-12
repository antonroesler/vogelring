# Multi-Tenant Organization Architecture Documentation

## Overview

Vogelring has been enhanced to support multiple organizations with complete data isolation using **application-level filtering**. Each organization has its own private dataset, and users belong to organizations. Data is isolated at the organization level using explicit `org_id` filtering in all database queries, providing scalable multi-tenancy with admin capabilities.

## Authentication Architecture

### Production Authentication (Cloudflare Zero Trust)

- **Provider**: Cloudflare Zero Trust
- **Headers**: `CF-Access-Authenticated-User-Email`, `CF-Access-JWT`
- **User Identification**: JWT `sub` claim + email
- **Automatic User Creation**: Users created on first login

### Development Authentication (Mock System)

- **Provider**: Mock user system
- **Environment Variables**: `DEV_USER_EMAIL`, `DEV_USER_NAME`
- **User Identification**: Email-based
- **Automatic User Creation**: Dev user created automatically

## Database Schema

### User Model

**Table**: `users`
**Location**: `backend/src/database/user_models.py`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cf_sub VARCHAR(255) UNIQUE NOT NULL,     -- Cloudflare subject ID
    email VARCHAR(255) UNIQUE NOT NULL,      -- User email
    display_name VARCHAR(100),               -- Display name
    org_id UUID REFERENCES organizations(id) NOT NULL, -- Organization membership
    is_admin BOOLEAN DEFAULT false NOT NULL, -- Admin privileges
    is_active BOOLEAN DEFAULT true,          -- Account status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,                    -- Last login time
    preferences JSONB DEFAULT '{}'::jsonb    -- User preferences
);

-- Indexes
CREATE INDEX idx_users_cf_sub ON users(cf_sub);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org_id ON users(org_id);
CREATE INDEX idx_users_is_active ON users(is_active);
```

### Organization Schema

**Table**: `organizations`
**Location**: `backend/src/database/organization_models.py`

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_organizations_is_active ON organizations(is_active);
```

### Organization Columns

All data tables include `org_id` columns for organization-based isolation:

```sql
-- Ringings table
ALTER TABLE ringings ADD COLUMN org_id UUID REFERENCES organizations(id) NOT NULL;
CREATE INDEX idx_ringings_org_id ON ringings(org_id);
CREATE INDEX idx_ringings_org_species_date ON ringings(org_id, species, date);
CREATE INDEX idx_ringings_org_place ON ringings(org_id, place);

-- Sightings table
ALTER TABLE sightings ADD COLUMN org_id UUID REFERENCES organizations(id) NOT NULL;
CREATE INDEX idx_sightings_org_id ON sightings(org_id);
CREATE INDEX idx_sightings_org_species_date ON sightings(org_id, species, date);
CREATE INDEX idx_sightings_org_ring_date ON sightings(org_id, ring, date);
CREATE INDEX idx_sightings_org_place ON sightings(org_id, place);

-- Bird relationships table
ALTER TABLE bird_relationships ADD COLUMN org_id UUID REFERENCES organizations(id) NOT NULL;
CREATE INDEX idx_bird_relationships_org_id ON bird_relationships(org_id);
CREATE INDEX idx_bird_relationships_org_type ON bird_relationships(org_id, relationship_type);
CREATE INDEX idx_bird_relationships_org_bird1 ON bird_relationships(org_id, bird1_ring);
CREATE INDEX idx_bird_relationships_org_bird2 ON bird_relationships(org_id, bird2_ring);
```

## Data Isolation Strategy

### Application-Level Filtering (Current Implementation)

**Approach**: All database queries explicitly filter by `org_id` at the application level.

**Benefits**:
- Simple and predictable
- Easy to debug and troubleshoot
- No transaction boundary issues
- Works with connection pooling
- Clear audit trail

**Implementation**:
```python
# All repository methods include org_id filtering
def get_all_sightings(self, org_id: str, limit: Optional[int] = None):
    return self.db.query(Sighting).filter(Sighting.org_id == org_id).limit(limit).all()

def create_sighting(self, org_id: str, **kwargs):
    kwargs['org_id'] = org_id
    instance = Sighting(**kwargs)
    self.db.add(instance)
    self.db.commit()
    return instance
```

### Previous RLS Implementation (Deprecated)

**Issue**: Row Level Security (RLS) with `SET LOCAL` caused transaction boundary problems:
- Context lost after `commit()` operations
- Refresh operations failed
- Complex multi-operation workflows broke
- Connection pooling complications

**Migration**: Moved from RLS to explicit application-level filtering for reliability.

## Backend Implementation

### Authentication Utilities

**File**: `backend/src/utils/auth.py`

Key functions:
- `get_current_user()` - Environment-aware user provider
- `get_current_user_dev()` - Development mock user
- `get_current_user_prod()` - Production Cloudflare user

**Removed**: `get_db_with_org()` - No longer needed with application-level filtering

### Repository Pattern

**File**: `backend/src/database/repositories.py`

```python
class BaseRepository:
    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class

    def get_by_id(self, id: str, org_id: str):
        """Get record by ID within organization"""
        return self.db.query(self.model_class).filter(
            self.model_class.id == id,
            self.model_class.org_id == org_id
        ).first()

    def create(self, org_id: str, **kwargs):
        """Create new record"""
        kwargs['org_id'] = org_id
        instance = self.model_class(**kwargs)
        self.db.add(instance)
        self.db.commit()
        return instance
```

### Service Layer

**Files**: `backend/src/api/services/`

All services updated to accept and pass `org_id`:

```python
class SightingService:
    def get_sightings(self, org_id: str, limit: Optional[int] = None):
        return self.repository.get_all(org_id, limit=limit)
    
    def add_sighting(self, org_id: str, sighting_data: Dict[str, Any]):
        return self.repository.create(org_id, **sighting_data)
```

### API Endpoints

**Pattern**: All endpoints receive `current_user` and pass `current_user.org_id` to services:

```python
@router.get("/sightings")
async def get_sightings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SightingService(db)
    return service.get_sightings(current_user.org_id)
```

## Updated Services and Routers

### Completed Migrations

✅ **SightingService + Router**
- All methods accept `org_id` parameter
- All database queries filter by `org_id`
- Router passes `current_user.org_id` to all service calls

✅ **RingingService + Router**
- All methods accept `org_id` parameter
- All database queries filter by `org_id`
- Router passes `current_user.org_id` to all service calls

✅ **BirdService + Router**
- `get_bird_meta_by_ring(ring, org_id)`
- `get_bird_suggestions_by_partial_reading(partial_reading, org_id)`
- Router passes `current_user.org_id` to all service calls

✅ **SuggestionService + Router**
- All methods accept `org_id` parameter
- All database queries filter by `org_id`
- Router passes `current_user.org_id` to all service calls

✅ **AnalyticsService + Router**
- `get_all_sightings_from_ring(ring, org_id)`
- `get_friends_from_ring(ring, org_id, min_shared_sightings)`
- `get_seasonal_analysis(org_id)`
- Router passes `current_user.org_id` to all service calls

✅ **Dashboard Router**
- All database queries filter by `current_user.org_id`
- No separate service class - direct DB queries updated

✅ **FamilyRepository + Router**
- All methods accept `org_id` parameter
- All database queries filter by `org_id`
- Router passes `current_user.org_id` to all repository calls

## API Endpoints

### Authentication Endpoints

| Method | Endpoint                  | Description                                   |
| ------ | ------------------------- | --------------------------------------------- |
| GET    | `/api/auth/me`            | Get current user information                  |
| GET    | `/api/auth/status`        | Authentication status and debug info          |

### Data Endpoints (All Organization-Filtered)

| Method | Endpoint                    | Description                              |
| ------ | --------------------------- | ---------------------------------------- |
| GET    | `/api/sightings`            | Get sightings for user's organization    |
| POST   | `/api/sightings`            | Create sighting in user's organization   |
| GET    | `/api/ringings`             | Get ringings for user's organization     |
| POST   | `/api/ringing`              | Create ringing in user's organization    |
| GET    | `/api/birds/{ring}`         | Get bird data from user's organization   |
| GET    | `/api/suggestions/species`  | Get species from user's organization     |
| GET    | `/api/dashboard`            | Get dashboard for user's organization    |
| GET    | `/api/family/relationships` | Get relationships in user's organization |

### Admin Endpoints

| Method | Endpoint                               | Description                              |
| ------ | -------------------------------------- | ---------------------------------------- |
| GET    | `/api/admin/organizations`             | List all organizations (admin only)      |
| POST   | `/api/admin/organizations`             | Create new organization (admin only)     |
| GET    | `/api/admin/organizations/{id}`        | Get organization details (admin only)    |
| PUT    | `/api/admin/organizations/{id}`        | Update organization (admin only)         |
| DELETE | `/api/admin/organizations/{id}`        | Delete organization (admin only)         |
| GET    | `/api/admin/organizations/{id}/users`  | List organization users (admin only)     |
| POST   | `/api/admin/users/assign-organization` | Assign user to organization (admin only) |
| GET    | `/api/admin/users`                     | List all users (admin only)              |

## Frontend Implementation

### Authentication Store

**File**: `frontend/src/stores/auth.ts`

```typescript
interface User {
  id: string;
  email: string;
  display_name?: string;
  org_id: string;
  organization_name?: string;
  is_admin: boolean;
  is_active: boolean;
}

const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    isAuthenticated: false,
    user: null,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchCurrentUser() {
      /* ... */
    },
    async initialize() {
      /* ... */
    },
  },
});
```

### User Interface

**File**: `frontend/src/App.vue`

- **User Menu**: Dropdown in header showing user info and organization
- **Organization Display**: Shows user's organization name
- **Admin Features**: Admin-only UI elements for organization management
- **Error Handling**: Shows authentication errors
- **Responsive**: Works on mobile devices

## Development Environment

### Docker Configuration

**File**: `docker-compose.yml`

```yaml
api:
  environment:
    DEVELOPMENT_MODE: "true"
    DEV_USER_EMAIL: ${DEV_USER_EMAIL:-dev@vogelring.local}
    DEV_USER_NAME: ${DEV_USER_NAME:-Local Developer}
```

### Environment Variables

```bash
# Development Authentication
DEVELOPMENT_MODE=true
DEV_USER_EMAIL=dev@vogelring.local
DEV_USER_NAME=Local Developer

# Database
DB_PASSWORD=defaultpassword
LOG_LEVEL=DEBUG
```

## Database Migrations

### Migration Files

**Current Migration**: `005_organization_structure_no_rls.sql`
- Creates organizations and users tables
- Adds org_id columns to all data tables
- Migrates existing data to default organization
- Creates all necessary indexes
- **No RLS policies** - uses application-level filtering

**Revert Migration**: `010_revert_rls.sql`
- Removes any existing RLS policies
- Disables RLS on all tables
- Removes triggers and functions
- Clean removal of all RLS components

### Migration Strategy

1. **Apply organization structure** (production-ready)
2. **Migrate existing data** to default organization
3. **Update application code** to use org_id filtering
4. **Remove RLS components** if previously implemented

## Security Considerations

### Data Isolation Security

- **Application-Level Filtering**: All queries explicitly filter by `org_id`
- **Parameter Validation**: `org_id` validated against user's organization
- **Index Security**: Organization-specific indexes prevent performance-based data leakage
- **Audit Trail**: All operations logged with organization context

### Authentication Security

- **JWT Validation**: Cloudflare JWT tokens validated
- **User Context**: User's organization membership enforced at application level
- **Error Handling**: Authentication errors logged but not exposed to users

## Performance Considerations

### Database Performance

- **Composite Indexes**: Organization-specific indexes on all filtered columns
  - `idx_sightings_org_species_date`
  - `idx_ringings_org_place`
  - `idx_bird_relationships_org_type`
- **Query Optimization**: All queries use organization indexes
- **Connection Pooling**: Standard connection pooling without session variables

### Application Performance

- **Service Layer**: Efficient org_id parameter passing
- **Repository Pattern**: Consistent filtering across all data access
- **Frontend Caching**: User and organization data cached in frontend stores

## Testing Strategy

### Development Testing

```bash
# Test different organizations by switching users
DEV_USER_EMAIL=alice@org1.com docker-compose up
DEV_USER_EMAIL=bob@org2.com docker-compose up

# Verify organization isolation
curl http://localhost/api/auth/me
curl http://localhost/api/sightings
```

### API Testing

```bash
# Check authentication and organization
curl http://localhost/api/auth/me

# Test organization-specific data
curl http://localhost/api/sightings
curl http://localhost/api/ringings
curl http://localhost/api/family/relationships
```

## Troubleshooting

### Common Issues

**User not showing correct organization:**
- Check `/api/auth/me` endpoint response
- Verify user's `org_id` in database
- Ensure organization exists and is active

**Data not filtered by organization:**
- Verify all repository methods accept `org_id`
- Check that services pass `current_user.org_id`
- Ensure database queries include `org_id` filter

**Performance issues:**
- Check that composite indexes exist
- Verify queries use organization indexes
- Monitor query execution plans

### Debug Commands

```bash
# Check user and organization data
docker-compose exec postgres psql -U vogelring -d vogelring -c "
SELECT u.email, u.display_name, o.name as org_name 
FROM users u 
JOIN organizations o ON u.org_id = o.id;
"

# Check data distribution by organization
docker-compose exec postgres psql -U vogelring -d vogelring -c "
SELECT o.name, 
       COUNT(s.id) as sightings, 
       COUNT(r.id) as ringings 
FROM organizations o 
LEFT JOIN sightings s ON o.id = s.org_id 
LEFT JOIN ringings r ON o.id = r.org_id 
GROUP BY o.id, o.name;
"

# Check indexes
docker-compose exec postgres psql -U vogelring -d vogelring -c "\d+ sightings"
```

## Migration from RLS to Application-Level Filtering

### Why the Change?

**RLS Issues Encountered**:
- Transaction boundary problems with `SET LOCAL`
- Context lost after `commit()` operations
- `refresh()` operations failing
- Complex multi-operation workflows breaking
- Connection pooling complications

**Application-Level Benefits**:
- Predictable and reliable
- Easy to debug and troubleshoot
- No transaction boundary issues
- Works seamlessly with connection pooling
- Clear and explicit data access patterns

### Migration Steps Completed

1. ✅ **Updated BaseRepository** - Added `org_id` parameters to all methods
2. ✅ **Updated All Services** - Modified to accept and pass `org_id`
3. ✅ **Updated All Routers** - Changed to use `get_db` and pass `current_user.org_id`
4. ✅ **Removed RLS Dependencies** - Eliminated `get_db_with_org` and RLS context
5. ✅ **Created Clean Migration** - Single migration without RLS components
6. ✅ **Updated Documentation** - Reflected new architecture

## Future Enhancements

### Planned Features

- **Enhanced Admin Interface**: Web-based organization management
- **User Invitation System**: Invite users to organizations
- **Data Export/Import**: Organization-specific data management
- **Audit Logging**: Detailed organization activity tracking
- **API Rate Limiting**: Organization-based rate limiting

### Scalability Considerations

- **Database Sharding**: Horizontal scaling by organization
- **Caching Strategy**: Organization-specific caching layers
- **CDN Integration**: Organization-branded asset delivery
- **Monitoring**: Organization-specific performance metrics

---

**Last Updated**: October 11, 2025
**Status**: Application-Level Multi-Tenancy Complete
**Architecture**: Organization-based isolation with explicit `org_id` filtering

## Summary

The organization-based multi-tenancy implementation is now complete with **application-level filtering**:

✅ **Organization Model**: Complete organization management with metadata
✅ **User-Organization Relationship**: Users belong to organizations with admin privileges  
✅ **Data Isolation**: All data tables use `org_id` with explicit filtering
✅ **Application-Level Security**: All queries filter by `org_id` at application level
✅ **All Services Updated**: Every service and router uses organization filtering
✅ **Admin System**: Comprehensive admin endpoints for organization management
✅ **Frontend Integration**: Organization info and admin features in UI
✅ **Development Environment**: Easy testing with mock organizations
✅ **Clean Migration**: Single migration script without RLS complexity
✅ **Performance Optimized**: Composite indexes for efficient organization queries

The system provides reliable multi-tenancy where:
- Each organization has completely isolated data
- Users belong to one organization  
- Data access is filtered by `org_id` at the application level
- Security is enforced through explicit query filtering
- Performance is optimized with organization-specific indexes
- No complex RLS or session variable dependencies
