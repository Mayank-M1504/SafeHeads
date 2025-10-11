# Troubleshooting: Violation Images Not Displaying

## Issues Fixed

### 1. **Number Plate Format Validation** ✅
- Updated Gemini prompt to enforce Indian number plate format: `2 letters + 2 digits + 1-2 letters + 3-4 digits`
- Examples: `MH12AB1234`, `KA01CD567`
- Added regex validation to ensure only properly formatted plates are saved

### 2. **Image Display Debugging** ✅
- Added console logging to track image URLs
- Added visual indicator for missing images
- Enhanced debugging in ImagePipeline for Cloudinary uploads

## Debugging Steps

### Step 1: Check if Images are Being Uploaded

Run the ImagePipeline and watch for these debug messages:

```bash
python backend/Imagepipeline.py
```

Look for:
- `☁️ Uploading image to Cloudinary with public_id: violation_xxx`
- `✅ Cloudinary upload successful: https://res.cloudinary.com/...`
- `📊 Violation data prepared: MH12AB1234 - https://res.cloudinary.com/...`
- `💾 Violation data saved to database successfully`

### Step 2: Check Database Content

Test the violations API:

```bash
python backend/test_violations_api.py
```

This will:
- Test API connectivity
- Create a test violation
- Check if violations are being retrieved
- Verify image URLs are in the database

### Step 3: Check Frontend Console

Open browser developer tools (F12) and look for:
- Console logs showing image URLs when clicking the image button
- Network requests to Cloudinary URLs
- Any CORS or loading errors

### Step 4: Manual Database Check

If you have database access, check the violations table:

```sql
SELECT number_plate, image_url, image_public_id, created_at 
FROM violations 
ORDER BY created_at DESC 
LIMIT 10;
```

## Common Issues and Solutions

### Issue 1: Cloudinary Not Configured
**Symptoms**: `⚠️ Cloudinary credentials not configured`

**Solution**: 
1. Create `.env` file in `backend/` directory
2. Add your Cloudinary credentials:
```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Issue 2: Violations API Not Running
**Symptoms**: `❌ Error saving to database: Connection refused`

**Solution**:
1. Start the violations API: `python backend/violations_api.py`
2. Check if it's running on port 5001: `http://localhost:5001/api/health`

### Issue 3: Invalid Number Plates
**Symptoms**: Images saved but no violations in database

**Solution**: 
- The new validation only saves plates matching Indian format
- Check ImagePipeline logs for `❌ Invalid plate` messages
- Only properly formatted plates (e.g., `MH12AB1234`) will be saved

### Issue 4: CORS Issues
**Symptoms**: Images load in database but not in frontend

**Solution**:
- Check browser console for CORS errors
- Ensure Cloudinary allows your domain
- Check if image URLs are accessible directly

### Issue 5: Database Connection Issues
**Symptoms**: `❌ Error saving to database`

**Solution**:
1. Run database setup: `python backend/setup_database.py`
2. Check PostgreSQL is running
3. Verify `.env` file has correct `DATABASE_URL`

## Testing the Complete Flow

### 1. Start All Services
```bash
python start_all_services.py
```

### 2. Generate a Violation
1. Start video stream in frontend
2. Wait for helmet violation detection
3. Check `backend/violation/` folder for new images

### 3. Check Processing
1. Watch ImagePipeline logs for processing
2. Check if valid number plate is extracted
3. Verify Cloudinary upload success

### 4. Check Database
1. Open violations section in frontend
2. Look for new violations with image URLs
3. Click image button to test display

## Debug Commands

### Check ImagePipeline Status
```bash
python backend/Imagepipeline.py
```

### Test Violations API
```bash
python backend/test_violations_api.py
```

### Check Database Connection
```bash
python backend/setup_database.py
```

### View Recent Violations
```bash
curl http://localhost:5001/api/violations
```

## Expected Behavior

1. **Video Detection**: Main backend detects helmet violations
2. **Image Saving**: Violation images saved to `violation/` folder
3. **Image Processing**: ImagePipeline processes images with Gemini AI
4. **Number Plate Validation**: Only valid Indian format plates are processed
5. **Cloudinary Upload**: Valid images uploaded to Cloudinary
6. **Database Storage**: Violation data saved with image URLs
7. **Frontend Display**: Images displayed in violations table

## Log Messages to Watch For

### Successful Flow:
```
✅ Valid plate detected: 'MH12AB1234' (normalized: 'MH12AB1234') - Processing for database...
☁️ Uploading image to Cloudinary with public_id: violation_1234567890_40
✅ Cloudinary upload successful: https://res.cloudinary.com/...
📊 Violation data prepared: MH12AB1234 - https://res.cloudinary.com/...
📡 Sending violation data to API: http://localhost:5001/api/violations
📡 API Response: 201
✅ Violation saved to database: MH12AB1234
```

### Failed Flow:
```
❌ Invalid plate: 'ABC123' (normalized: 'ABC123') - Skipping
```
or
```
⚠️ Cloudinary credentials not configured
```
or
```
❌ Error saving to database: Connection refused
```

If you're still having issues, check the specific error messages and follow the corresponding solution above.
