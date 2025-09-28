# Family Relationships System

## Overview

The family relationships system manages breeding partnerships, parent-child relationships, and sibling connections between birds in the Vogelring application. It provides both a comprehensive management interface and clean overview displays.

## Architecture

### Backend Components

#### Database Models

- **Location**: `backend/src/database/family_models.py`
- **Main Model**: `BirdRelationship`
- **Relationship Types**: `RelationshipType` enum
  - `BREEDING_PARTNER`: Breeding partners
  - `PARENT_OF`: Parent to child relationship
  - `CHILD_OF`: Child to parent relationship
  - `SIBLING_OF`: Sibling relationships

#### Repository Layer

- **Location**: `backend/src/database/family_repository.py`
- **Class**: `FamilyRepository`
- **Key Methods**:
  - `create_relationship()`: Create single relationship
  - `create_symmetric_relationship()`: Create bidirectional relationships
  - `get_bird_relationships()`: Get all relationships for a bird
  - `get_all_relationships()`: Get all relationships with filters
  - `update_relationship()`: Update existing relationship
  - `delete_relationship()`: Delete relationship

#### API Endpoints

- **Location**: `backend/src/api/routers/family.py`
- **Base Path**: `/family`

| Method | Endpoint                     | Description                         |
| ------ | ---------------------------- | ----------------------------------- |
| GET    | `/relationships`             | Get all relationships with filters  |
| GET    | `/relationships/{bird_ring}` | Get relationships for specific bird |
| POST   | `/relationships`             | Create new relationship             |
| PUT    | `/relationships/{id}`        | Update existing relationship        |
| DELETE | `/relationships/{id}`        | Delete relationship                 |
| POST   | `/relationships/symmetric`   | Create symmetric relationship       |
| GET    | `/partners/{bird_ring}`      | Get breeding partners               |
| GET    | `/children/{bird_ring}`      | Get children                        |
| GET    | `/parents/{bird_ring}`       | Get parents                         |
| GET    | `/siblings/{bird_ring}`      | Get siblings                        |

### Frontend Components

#### Main Views

1. **FamilyRelationsList.vue** (`/family-relations`)

   - **Purpose**: Comprehensive management interface for all relationships
   - **Features**: CRUD operations, filtering, pagination
   - **URL Parameters**: `?bird_ring=123000` for filtering

2. **BirdFamilyEditor.vue** (Used in bird details)
   - **Purpose**: Clean overview of bird's family relationships
   - **Features**: Read-only display, deduplication, navigation

#### Supporting Components

1. **FamilyRelationshipEditor.vue**

   - **Purpose**: Create/edit relationship dialog
   - **Features**: Form validation, symmetric relationship info

2. **FamilyOverviewList.vue**

   - **Purpose**: Clean list display for bird overview
   - **Features**: Clickable bird links, no edit functionality

3. **FamilyRelationshipList.vue**
   - **Purpose**: Detailed list with edit/delete actions
   - **Features**: Reference links, action buttons

## Data Flow

### Relationship Creation (Family Sightings)

When a family is created through the sighting form:

1. **Main sighting** is created
2. **Partner sighting** is created (if exists)
3. **Child sightings** are created for each child
4. **Relationships are established**:
   - Breeding partner: `bird1 ↔ bird2` (bidirectional)
   - Parent-child: `parent → child` and `child → parent`
   - Siblings: All children connected bidirectionally

```typescript
// Example: Creating family relationships
await createRelationship({
  bird1_ring: mainSighting.ring,
  bird2_ring: partnerSighting.ring,
  relationship_type: "breeding_partner",
  year: 2025,
  sighting1_id: mainSighting.id,
  sighting2_id: partnerSighting.id,
});
```

### Field Clearing Integration

The family relationship system integrates with the field clearing settings:

- **Location**: `frontend/src/utils/fieldClearingUtils.ts`
- **Function**: `createClearedSighting()`
- **Usage**: Applied after family creation to reset form fields according to user preferences

## Key Design Decisions

### 1. Symmetric Relationships

**Breeding Partners** and **Siblings** are symmetric (bidirectional):

- Stored as separate database entries in both directions
- Created using individual `createRelationship()` calls (not `createSymmetricRelationship()`)
- **Reason**: Allows proper sighting/ringing ID tracking

### 2. Reference Tracking

Relationships track their source sightings/ringings:

- `sighting1_id`, `sighting2_id`: Link to source sightings
- `ringing1_id`, `ringing2_id`: Link to source ringings
- **Priority**: Ringing references over sighting references
- **Display**: Clickable links in management interface

### 3. No Automatic Symmetric Editing

**Design Decision**: Manual editing only for symmetric relationships

- **Reason**: Prevents accidental data corruption
- **Implementation**: Users must edit each direction separately
- **UI**: Warning message about symmetric nature, no automatic update option

### 4. Deduplication in Overview

Bird detail page shows unique relationships only:

- **Logic**: One entry per `{otherBird}-{year}` combination
- **Implementation**: Map-based deduplication in computed properties
- **Benefit**: Clean overview without duplicate entries

## Component Responsibilities

### BirdFamilyEditor.vue (Bird Details)

- **Purpose**: Clean family overview
- **Features**:
  - ✅ Tabbed interface (Partners, Children, Parents, Siblings)
  - ✅ Unique relationship display
  - ✅ Clickable bird links
  - ✅ Prominent "Show All" button
  - ❌ No editing capabilities
  - ❌ No sighting/ringing links

### FamilyRelationsList.vue (Management Interface)

- **Purpose**: Comprehensive relationship management
- **Features**:
  - ✅ Full CRUD operations
  - ✅ Advanced filtering
  - ✅ Reference links to sightings/ringings
  - ✅ Bird ring filter indicator
  - ✅ Pagination and sorting

## API Integration

### Frontend API Functions

- **Location**: `frontend/src/api/index.ts`
- **Functions**:
  - `getAllRelationships()`: Get all with filters
  - `getBirdRelationships()`: Get for specific bird
  - `createRelationship()`: Create new
  - `updateRelationship()`: Update existing
  - `deleteRelationship()`: Delete
  - `createSymmetricRelationship()`: Create bidirectional

### Type Definitions

- **Location**: `frontend/src/types/index.ts`
- **Interfaces**: Relationship types and family tree structures

## Navigation & Routing

### Routes

- `/family-relations`: Main management interface
- `/family-relations?bird_ring=123000`: Filtered view for specific bird
- `/birds/{ring}`: Bird details with family overview

### Navigation Flow

1. **Bird Details** → Clean overview → "Alle Beziehungen anzeigen" → Management interface
2. **Management Interface** → Filter by bird → Back to overview
3. **Cross-references**: Sighting/ringing links from management interface

## Development Guidelines

### Adding New Relationship Types

1. **Backend**: Add to `RelationshipType` enum in `family_models.py`
2. **API**: Add to API enum in `family.py`
3. **Frontend**: Add to `relationshipTypeOptions` in components
4. **UI**: Add appropriate icon and color in display functions

### Modifying Display Logic

- **Overview Display**: Modify `FamilyOverviewList.vue`
- **Management Display**: Modify `FamilyRelationshipList.vue`
- **Deduplication**: Update computed properties in `BirdFamilyEditor.vue`

### Extending Filtering

- **Backend**: Add parameters to `get_all_relationships()` in repository
- **API**: Add query parameters to GET `/relationships` endpoint
- **Frontend**: Add filter controls to `FamilyRelationsList.vue`

## Common Issues & Solutions

### 1. Duplicate Relationships

**Problem**: Multiple entries for same bird-year combination
**Solution**: Map-based deduplication using `{otherBird}-{year}` key

### 2. Symmetric Relationship Consistency

**Problem**: Breeding partners/siblings getting out of sync
**Solution**: Manual editing approach, clear warnings to users

### 3. Reference Link Failures

**Problem**: Broken links to sightings/ringings
**Solution**: Null checks and fallback displays in templates

### 4. Performance with Large Datasets

**Problem**: Slow loading with many relationships
**Solution**: Pagination, filtering, and computed property optimization

## Testing Considerations

### Test Cases

1. **Relationship Creation**: Verify symmetric relationships created correctly
2. **Deduplication**: Ensure unique display works with duplicate data
3. **Navigation**: Test all cross-reference links work correctly
4. **Filtering**: Verify URL parameter filtering functions properly
5. **Field Clearing**: Ensure family creation respects user settings

### Edge Cases

- Birds with no relationships
- Relationships with missing sighting/ringing references
- Invalid bird rings in relationships
- Year boundary conditions

## Performance Optimizations

### Current Optimizations

- **Computed Properties**: Reactive deduplication
- **Map-based Logic**: Efficient duplicate removal
- **Lazy Loading**: Components load data on mount
- **Pagination**: Limited results in management interface

### Future Considerations

- **Caching**: Consider caching frequently accessed relationships
- **Virtual Scrolling**: For very large relationship lists
- **Batch Operations**: For bulk relationship management

## Security Considerations

### Data Validation

- **Backend**: Pydantic models validate all inputs
- **Frontend**: Form validation prevents invalid submissions
- **Database**: Foreign key constraints ensure data integrity

### Access Control

- **Current**: No specific access controls (handled by Cloudflare Zero Trust)
- **Future**: Consider role-based relationship editing permissions

## Maintenance

### Regular Tasks

- **Monitor**: Relationship data consistency
- **Cleanup**: Orphaned relationships (birds that no longer exist)
- **Optimize**: Query performance as data grows

### Code Quality

- **DRY Principle**: Shared utilities for field clearing and validation
- **Type Safety**: Full TypeScript coverage
- **Error Handling**: Comprehensive error handling with user feedback
- **Clean Architecture**: Clear separation between overview and management interfaces

## Migration Notes

### From Old System

- **Removed**: Old `FamilyTree.vue` component with "Familienmitglied hinzufügen"
- **Replaced**: With comprehensive management system
- **Improved**: Field clearing consistency between individual and family sightings

### Breaking Changes

- **Confidence Field**: Hidden from UI (still in backend)
- **Source Field**: Not used for user input (auto-generated)
- **Symmetric Editing**: Removed automatic symmetric updates (manual only)

---

_Last Updated: September 2025_
_For questions or issues, refer to the main project documentation or contact the development team._
