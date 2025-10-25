# Fix Violations API - Images Not Showing

## Problem
The violations API is throwing an error: `'no_helmet_count' is an invalid keyword argument for Violation`

This prevents violations from being saved to the database, so no images appear in the frontend.

## Root Cause
The database table is missing the `no_helmet_count` column that was recently added to the model.

## Solution

### Option 1: Simple Fix (Recommended)
Run the database fix script:

```bash
cd backend
python fix_database.py
```

This will automatically add the missing column to your database.

### Option 2: Manual Migration
If Option 1 doesn't work, run the migration script:

```bash
cd backend
python migrate_add_no_helmet_count.py
```

### Option 3: Recreate Database (Nuclear Option)
If both above fail, you can recreate the database:

```bash
cd backend
python init_db.py
```

**⚠️ Warning:** This will delete all existing violation data!

## Verification Steps

1. **Check Database Connection**
   ```bash
   # Make sure your .env file has correct credentials
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=safehead_violations
   DB_USER=postgres
   DB_PASSWORD=your_password
   ```

2. **Test Violations API**
   ```bash
   # Start the violations API
   python violations_api.py
   ```
   
   You should see:
   ```
   ✅ Database tables created successfully
   🚀 Starting Violations API on port 5001
   ```

3. **Test in Browser**
   Open: http://localhost:5001/api/violations
   
   You should see a JSON response (empty if no violations yet).

4. **Start Image Pipeline**
   ```bash
   python start_image_pipeline.py
   ```
   
   Wait for violations to be detected and processed.

5. **Check Frontend**
   Open your React app and check the Violations section.
   Images should now appear with Cloudinary URLs.

## Changes Made

### 1. violations_api.py
- ✅ Added `no_helmet_count` field to Violation model (line 47)
- ✅ Added `no_helmet_count` to `to_dict()` method (line 65)

### 2. Imagepipeline.py
- ✅ Fixed directory paths to use absolute paths
- ✅ Removed image enhancement logic
- ✅ Now processes original images directly

### 3. app.py
- ✅ Unified violation storage to single directory
- ✅ Added 50px padding to vehicle crops
- ✅ Maintains no_helmet_count in filename and image

## Common Issues

### Issue: Database Connection Error
**Solution:** Check your PostgreSQL is running and credentials in .env are correct

### Issue: Images still not showing
**Solutions:**
1. Check browser console for CORS errors
2. Verify Cloudinary credentials in .env
3. Make sure violations API is running on port 5001
4. Clear browser cache

### Issue: Cloudinary upload fails
**Solution:** Add to .env:
```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## Testing Checklist

- [ ] Database migration ran successfully
- [ ] Violations API starts without errors
- [ ] Image pipeline starts without errors
- [ ] Browser can access http://localhost:5001/api/violations
- [ ] Frontend shows violation images
- [ ] Images have Cloudinary URLs (not local paths)
- [ ] No_helmet_count appears in API responses

## Next Steps After Fix

1. **Restart all services:**
   ```bash
   # Terminal 1: Violations API
   python backend/violations_api.py
   
   # Terminal 2: Image Pipeline
   python backend/start_image_pipeline.py
   
   # Terminal 3: Main App
   python backend/app.py
   
   # Terminal 4: Frontend
   cd frontend
   npm run dev
   ```

2. **Test the complete flow:**
   - Start video stream
   - Wait for violations to be detected
   - Check violations appear in frontend
   - Verify images load from Cloudinary

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/violations` | GET | Get all violations |
| `/api/violations` | POST | Create new violation |
| `/api/violations/<plate>` | GET | Get specific violation |
| `/api/violations/<plate>` | PUT | Update violation |
| `/api/violations/<plate>` | DELETE | Delete violation |
| `/api/violations/stats` | GET | Get statistics |
| `/api/violations/export` | GET | Export to CSV |

## Support

If you're still having issues:
1. Check terminal logs for detailed error messages
2. Verify all environment variables are set
3. Ensure all Python dependencies are installed: `pip install -r requirements.txt`
4. Make sure PostgreSQL service is running

