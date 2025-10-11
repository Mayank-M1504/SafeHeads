# Database Setup Guide

## Quick Fix for Current Error

The error you're seeing is because the database credentials are not properly configured. Here's how to fix it:

### Step 1: Create a .env file

Create a `.env` file in the `backend/` directory with your PostgreSQL credentials:

```bash
# Database Configuration
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/safehead_violations

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key

# Violations API Configuration
VIOLATIONS_API_URL=http://localhost:5001
VIOLATIONS_API_PORT=5001

# Flask Configuration
SECRET_KEY=your-secret-key-here
```

### Step 2: Replace the placeholders

Replace these placeholders with your actual credentials:
- `your_username` - Your PostgreSQL username (usually `postgres`)
- `your_password` - Your PostgreSQL password
- `your_cloud_name` - Your Cloudinary cloud name
- `your_api_key` - Your Cloudinary API key
- `your_api_secret` - Your Cloudinary API secret
- `your_gemini_api_key` - Your Gemini AI API key

### Step 3: Test the database connection

Run the database setup script:

```bash
python backend/setup_database.py
```

This will:
- Test your PostgreSQL connection
- Create the `safehead_violations` database if it doesn't exist
- Verify everything is working

### Step 4: Start the services

Once the database is set up, you can start the services:

```bash
# Option 1: Start all services
python start_all_services.py

# Option 2: Start individually
python backend/violations_api.py  # Terminal 1
python backend/app.py            # Terminal 2
python backend/Imagepipeline.py  # Terminal 3
cd frontend && npm run dev       # Terminal 4
```

## Common Issues and Solutions

### 1. PostgreSQL not running
**Error**: `connection to server at "localhost" (::1), port 5432 failed`

**Solution**: Start PostgreSQL service
- Windows: Start PostgreSQL service from Services
- Linux/Mac: `sudo service postgresql start`

### 2. Wrong credentials
**Error**: `password authentication failed for user "username"`

**Solution**: Check your username and password in the .env file

### 3. Database doesn't exist
**Error**: `database "safehead_violations" does not exist`

**Solution**: The setup script will create it automatically, or create it manually:
```sql
CREATE DATABASE safehead_violations;
```

### 4. Permission issues
**Error**: `permission denied for database`

**Solution**: Make sure your user has permission to create databases:
```sql
ALTER USER your_username CREATEDB;
```

## Example .env file

Here's a complete example (replace with your actual values):

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:mypassword123@localhost:5432/safehead_violations

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=my-cloud-name
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=abcdefghijklmnopqrstuvwxyz

# Gemini AI Configuration
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Violations API Configuration
VIOLATIONS_API_URL=http://localhost:5001
VIOLATIONS_API_PORT=5001

# Flask Configuration
SECRET_KEY=my-super-secret-key-12345

# Optional: Location and Camera Information
DEFAULT_LOCATION=Traffic Intersection 1
DEFAULT_CAMERA_ID=CAM001
```

## Testing the Setup

After creating the .env file, test each component:

1. **Test Database**: `python backend/setup_database.py`
2. **Test Violations API**: `python backend/violations_api.py`
3. **Test Main Backend**: `python backend/app.py`
4. **Test Image Pipeline**: `python backend/Imagepipeline.py`

If all tests pass, you can run the full system with `python start_all_services.py`.
