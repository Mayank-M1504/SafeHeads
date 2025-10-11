# Safehead Violation Database Setup

This document provides instructions for setting up the PostgreSQL database and Cloudinary integration for the Safehead violation tracking system.

## Prerequisites

1. **PostgreSQL Database**: Install PostgreSQL on your system
2. **Cloudinary Account**: Sign up for a free Cloudinary account at [cloudinary.com](https://cloudinary.com)
3. **Python Environment**: Ensure you have Python 3.8+ installed

## Database Setup

### 1. Install PostgreSQL

**Windows:**
- Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
- Remember the password you set for the `postgres` user

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### 2. Create Database

Connect to PostgreSQL and create the database:

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE safehead_violations;

-- Create user (optional, you can use postgres user)
CREATE USER safehead_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE safehead_violations TO safehead_user;

-- Exit psql
\q
```

## Cloudinary Setup

### 1. Create Cloudinary Account

1. Go to [cloudinary.com](https://cloudinary.com)
2. Sign up for a free account
3. After logging in, go to your Dashboard
4. Note down your:
   - Cloud Name
   - API Key
   - API Secret

### 2. Configure Cloudinary

The system will automatically use your Cloudinary credentials from environment variables.

## Environment Configuration

### 1. Create Environment File

Copy the template and configure your environment:

```bash
# Copy the template
cp env_template.txt .env

# Edit the .env file with your actual values
```

### 2. Configure .env File

Edit the `.env` file with your actual values:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=safehead_violations
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Flask Configuration
SECRET_KEY=your-secret-key-here

# Optional: Location and Camera Information
DEFAULT_LOCATION=Traffic Intersection 1
DEFAULT_CAMERA_ID=CAM001
```

## Installation and Setup

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Run the database initialization script
python init_db.py
```

This script will:
- Create the database if it doesn't exist
- Create all necessary tables
- Test the database connection

### 3. Start the Application

```bash
# Start the Flask application
python app.py
```

The application will be available at `http://localhost:5000`

## Database Schema

### Violations Table

The `violations` table stores all helmet violation records:

| Column | Type | Description |
|--------|------|-------------|
| `number_plate` | VARCHAR(20) | Primary key - vehicle number plate |
| `violation_type` | VARCHAR(50) | Type of violation (e.g., 'no_helmet') |
| `violation_description` | TEXT | Detailed description of the violation |
| `image_url` | VARCHAR(500) | Cloudinary URL of the violation image |
| `image_public_id` | VARCHAR(200) | Cloudinary public ID for image management |
| `violation_timestamp` | DATETIME | When the violation occurred |
| `created_at` | DATETIME | When the record was created |
| `updated_at` | DATETIME | When the record was last updated |
| `confidence_score` | FLOAT | Detection confidence score |
| `vehicle_id` | VARCHAR(50) | Internal vehicle tracking ID |
| `crop_filename` | VARCHAR(200) | Original crop filename |
| `location` | VARCHAR(200) | Location where violation occurred |
| `camera_id` | VARCHAR(50) | Camera identifier |
| `status` | VARCHAR(20) | Violation status (active/resolved/dismissed) |

## API Endpoints

### Violation Management

- `GET /api/violations` - Get all violations with pagination
- `GET /api/violations/<number_plate>` - Get specific violation by number plate
- `PUT /api/violations/<number_plate>` - Update violation status
- `DELETE /api/violations/<number_plate>` - Delete violation and image
- `GET /api/violations/stats` - Get violation statistics
- `GET /api/violations/export` - Export violations to CSV

### Query Parameters

**GET /api/violations:**
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)
- `status` - Filter by status (active/resolved/dismissed)
- `number_plate` - Search by number plate

**PUT /api/violations/<number_plate>:**
```json
{
  "status": "resolved"
}
```

## Features

### Automatic Violation Detection
- Detects helmet violations in real-time
- Saves violation images to Cloudinary
- Stores violation details in PostgreSQL
- Uses number plate as primary key

### Image Management
- Automatic upload to Cloudinary
- Image optimization and transformation
- Secure image URLs
- Automatic cleanup when violations are deleted

### Data Management
- Paginated violation listing
- Status management (active/resolved/dismissed)
- Search and filtering capabilities
- CSV export functionality
- Comprehensive statistics

## Troubleshooting

### Database Connection Issues

1. **Check PostgreSQL is running:**
   ```bash
   # Windows
   services.msc
   
   # Linux/macOS
   sudo systemctl status postgresql
   ```

2. **Verify database exists:**
   ```sql
   psql -U postgres -l
   ```

3. **Check connection parameters in .env file**

### Cloudinary Issues

1. **Verify credentials in .env file**
2. **Check Cloudinary dashboard for usage limits**
3. **Ensure internet connectivity**

### Application Issues

1. **Check Python dependencies:**
   ```bash
   pip list
   ```

2. **Verify database initialization:**
   ```bash
   python init_db.py
   ```

3. **Check application logs for error messages**

## Security Considerations

1. **Environment Variables**: Never commit `.env` file to version control
2. **Database Security**: Use strong passwords and limit database access
3. **API Security**: Consider adding authentication for production use
4. **Image Security**: Cloudinary provides secure image URLs

## Production Deployment

For production deployment:

1. **Use environment variables** instead of .env file
2. **Set up proper database backups**
3. **Configure Cloudinary for production** (paid plan recommended)
4. **Add authentication and authorization**
5. **Set up monitoring and logging**
6. **Use HTTPS for all communications**

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Verify all configuration settings
4. Test database and Cloudinary connectivity separately
