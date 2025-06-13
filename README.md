# Vogelring 🦆

A comprehensive bird tracking and sighting management system for ornithologists and bird watchers. Vogelring enables researchers to track ringed birds, manage sightings, analyze migration patterns, and maintain detailed records of bird populations.

<img width="1308" alt="entrylist" src="https://github.com/user-attachments/assets/dd96a7c6-b3c9-45ba-a6bc-c33e816b36df" />
<img width="1308" alt="entry" src="https://github.com/user-attachments/assets/7a7501a6-ae95-4d1b-b405-5ffc54606c41" />
<img width="1308" alt="new" src="https://github.com/user-attachments/assets/2208b293-df06-4ab6-84e1-298cc546b293" />

## 🧑🏼‍💻 Become a User

We'd be very pleased to extend the user group of vogelring. If you wish to become a user, please contact me. 


## 🌟 Features

### Core Functionality
- **Bird Sighting Management**: Record, edit, and track bird sightings with detailed metadata
- **Ring Database**: Comprehensive database of ringed birds with identification and tracking
- **Interactive Maps**: Visualize sightings on interactive maps with location accuracy indicators
- **Advanced Search**: Powerful search functionality with partial ring reading support (wildcards)
- **Family Trees**: Track breeding relationships and family lineages between birds

### Analytics & Insights
- **Friend Analysis**: Discover which birds are frequently seen together
- **Seasonal Patterns**: Analyze seasonal migration and behavior patterns
- **Dashboard**: Real-time statistics and insights about bird populations
- **Data Quality**: Built-in data validation and quality assessment tools
- **Radius Analysis**: Find all sightings within a specified geographic radius

### Data Management
- **Import/Export**: Support for various data formats and migration tools
- **Ringing Records**: Manage detailed ringing information and metadata
- **Reporting**: Generate shareable reports with customizable time ranges
- **Version Control**: Track changes and maintain data integrity

## 🏗️ Architecture

Vogelring is built as a modern full-stack application:

### Frontend
- **Vue 3** with TypeScript for type safety
- **Vuetify 3** for Material Design components
- **Leaflet** for interactive mapping
- **ECharts** for data visualization
- **Pinia** for state management

### Backend
- **AWS Lambda** with Python for serverless computing
- **API Gateway** for REST API endpoints
- **DynamoDB** for NoSQL data storage
- **S3** for file storage and data persistence
- **CloudFront** for content delivery

### Key Technologies
- **AWS SAM** for infrastructure as code
- **Pydantic** for data validation
- **AWS Lambda Powertools** for observability
- **TypeScript** for frontend type safety

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- AWS CLI configured
- AWS SAM CLI

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vogelring
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   # Frontend
   cd frontend
   npm install
   
   # Backend
   cd ../
   rye sync
   ```

4. **Start development servers**
   ```bash
   # Frontend (runs on http://localhost:5173)
   npm run dev
   
   # Backend (local API)
   rye run local
   ```

### Deployment

1. **Deploy the API**
   ```bash
   rye run deploy
   ```

2. **Deploy the frontend**
   ```bash
   cd frontend
   npm run deploy
   ```

## 📊 Data Model

### Core Entities

- **Sightings**: Individual bird observations with location, date, and metadata
- **Birds**: Unique ringed birds with identification and tracking information
- **Ringing**: Detailed ringing records including location, date, and ringer information
- **Family Trees**: Breeding relationships and lineage tracking

### Key Features

- **Flexible Data Entry**: Support for partial readings and uncertain identifications
- **Geographic Precision**: Exact and approximate location tracking
- **Temporal Analysis**: Date-based filtering and seasonal pattern analysis
- **Relationship Mapping**: Partner and offspring relationship tracking

## 🔍 API Documentation

The API provides comprehensive endpoints for:

- **Sightings**: CRUD operations, filtering, and search
- **Birds**: Metadata retrieval and suggestions
- **Analytics**: Friend analysis, seasonal patterns, radius searches
- **Ringing**: Ringing record management
- **Family**: Family tree and relationship management

API documentation is available at `/swagger` when running the development server.

## 🗺️ Mapping Features

- **Interactive Maps**: Leaflet-based mapping with multiple base layers
- **Clustering**: Automatic marker clustering for better performance
- **Location Accuracy**: Visual indicators for exact vs. approximate locations
- **Timeline Mode**: Temporal visualization of sightings
- **Radius Analysis**: Geographic proximity analysis

## 📈 Analytics

### Dashboard
- Real-time statistics and trends
- Top birds and locations
- Streak tracking for consecutive observation days
- Rolling 12-month analysis by species

### Advanced Analytics
- **Friend Networks**: Identify birds frequently seen together
- **Seasonal Patterns**: Migration and behavior analysis
- **Data Quality**: Validation and completeness metrics
- **Geographic Distribution**: Spatial analysis tools

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
RING_API_KEY=your-api-key
VITE_API_KEY=your-api-key

# AWS Configuration
AWS_REGION=eu-central-1
BUCKET=vogelring-data
CLOUDFRONT_DOMAIN=your-domain.com
```

### Database Setup

The system uses DynamoDB for structured data and S3 for bulk storage. Migration scripts are available in the `scripts/` directory.

## 🧪 Testing

```bash
# Run backend tests
rye run test

# Run frontend tests (if configured)
cd frontend
npm test
```

## 📝 Data Import

Vogelring includes tools for importing existing bird data:

```bash
# Convert CSV data to the internal format
rye run convert

# Migrate partner relationships
python scripts/migrate_partners.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for ornithological research and bird conservation efforts
- Supports the scientific community in tracking bird populations and migration patterns
- Designed with input from field researchers

## 📞 Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Contact me: anton@antonroesler.com

---

**Vogelring** - Empowering bird research through technology 🦅
