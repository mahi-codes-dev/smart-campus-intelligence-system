# Deployment & Testing Guide - New Features

## Pre-Deployment Checklist

### 1. Environment Setup
```bash
# Create uploads directory
mkdir -p uploads
chmod 755 uploads

# Install dependencies
pip install -r requirements.txt

# Verify Python version (3.8+)
python --version
```

### 2. Database Setup
```bash
# Run migrations
python -c "from services.migration_service import run_migrations; run_migrations()"

# Verify media tables created
psql $DATABASE_URL -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'media' OR table_name LIKE 'data_exports';"
```

### 3. Configuration
Update `.env` file with these settings:
```env
# File Upload Settings
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
UPLOAD_FOLDER=./uploads
ALLOWED_EXTENSIONS=pdf,doc,docx,txt,csv,xlsx,jpg,jpeg,png,gif,webp,mp4,avi,mov,mkv
```

---

## Testing Procedures

### Local Testing Setup
```bash
# Start development server
python app.py

# Server should be running on http://localhost:5000
```

### Test Case 1: File Upload
**Test**: Upload a valid PDF file
```bash
curl -X POST http://localhost:5000/media/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_document.pdf" \
  -F "description=Test Document"
```

**Expected Response**:
```json
{
  "success": true,
  "file_id": "uuid-string",
  "filename": "test_document.pdf",
  "size": 12345,
  "type": "pdf",
  "mime_type": "application/pdf"
}
```

### Test Case 2: File Type Validation
**Test**: Try uploading an invalid file type
```bash
curl -X POST http://localhost:5000/media/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@script.exe"
```

**Expected Response** (400):
```json
{
  "error": "File type not allowed. Allowed: csv, doc, docx, ..."
}
```

### Test Case 3: File Size Validation
**Test**: Create a file larger than 50MB
```bash
# Create large test file
dd if=/dev/zero of=largefile.bin bs=1M count=51

curl -X POST http://localhost:5000/media/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@largefile.bin"
```

**Expected Response** (400):
```json
{
  "error": "File too large. Maximum size: 50.0MB"
}
```

### Test Case 4: List Files
**Test**: List uploaded files
```bash
curl -X GET "http://localhost:5000/media/list?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "success": true,
  "files": [
    {
      "id": 1,
      "file_id": "uuid-string",
      "filename": "test_document.pdf",
      "type": "pdf",
      "size": 12345,
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "count": 1,
  "limit": 10,
  "offset": 0
}
```

### Test Case 5: Download File
**Test**: Download an uploaded file
```bash
curl -X GET "http://localhost:5000/media/<file_id>" \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded_file.pdf
```

**Expected**: File is downloaded successfully

### Test Case 6: Export to CSV
**Test**: Export marks to CSV
```bash
curl -X GET "http://localhost:5000/export/my-data/csv" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -o marks.csv
```

**Expected**: CSV file with proper format

### Test Case 7: Export to JSON
**Test**: Export data to JSON
```bash
curl -X GET "http://localhost:5000/export/my-data/json" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -o student_data.json
```

**Expected**: JSON file with nested structure

### Test Case 8: Performance Report
**Test**: Generate performance report
```bash
curl -X GET "http://localhost:5000/export/performance-report" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -o report.txt
```

**Expected**: Text file with formatted report

### Test Case 9: Delete File
**Test**: Delete an uploaded file
```bash
curl -X DELETE "http://localhost:5000/media/<file_id>" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response**:
```json
{
  "success": true
}
```

### Test Case 10: Chatbot UI on Mobile
**Test**: Open chatbot on mobile (< 480px width)
1. Open browser dev tools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select mobile device
4. Verify chatbot widget appears correctly
5. Verify no overflow or overlapping elements

---

## Performance Testing

### Load Testing File Uploads
```python
import requests
import concurrent.futures
import time

def upload_file(token):
    url = "http://localhost:5000/media/upload"
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": open("test_document.pdf", "rb")}
    
    start = time.time()
    response = requests.post(url, headers=headers, files=files)
    elapsed = time.time() - start
    
    return response.status_code, elapsed

# Run 20 concurrent uploads
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(upload_file, token) for _ in range(20)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success = sum(1 for status, _ in results if status == 201)
    avg_time = sum(t for _, t in results) / len(results)
    
    print(f"Success: {success}/20")
    print(f"Average Time: {avg_time:.2f}s")
```

### Export Performance
```python
import requests
import time

def test_export():
    token = "your_token_here"
    endpoints = [
        "/export/my-data/csv",
        "/export/my-data/json",
        "/export/performance-report"
    ]
    
    for endpoint in endpoints:
        url = f"http://localhost:5000{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        start = time.time()
        response = requests.get(url, headers=headers)
        elapsed = time.time() - start
        
        print(f"{endpoint}: {elapsed:.2f}s, Size: {len(response.content)} bytes")

test_export()
```

---

## Browser Compatibility Testing

### Chatbot Widget
| Browser | Desktop | Mobile | Dark Mode | Notes |
|---------|---------|--------|-----------|-------|
| Chrome | ✅ | ✅ | ✅ | Fully supported |
| Firefox | ✅ | ✅ | ✅ | Fully supported |
| Safari | ✅ | ✅ | ✅ | Fully supported |
| Edge | ✅ | ✅ | ✅ | Fully supported |

### File Upload
| Feature | Status | Notes |
|---------|--------|-------|
| Drag & Drop | ✅ | Supported via HTML5 |
| Progress Bar | ✅ | Can be added with XMLHttpRequest |
| Multiple Files | ⚠️ | Requires frontend enhancement |
| Cancel Upload | ⚠️ | Requires AbortController |

---

## Monitoring & Logging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitor File Storage
```bash
# Check disk usage
du -sh ./uploads

# List largest files
find ./uploads -type f -exec du -h {} + | sort -rh | head -10

# Count total files
find ./uploads -type f | wc -l
```

### Database Monitoring
```sql
-- Check media table size
SELECT pg_size_pretty(pg_total_relation_size('media'));

-- Count uploads per user
SELECT student_id, COUNT(*) as file_count, 
       SUM(file_size) as total_size
FROM media
GROUP BY student_id
ORDER BY total_size DESC;

-- Check old exports (cleanup candidates)
SELECT * FROM data_exports
WHERE created_at < NOW() - INTERVAL '30 days';
```

---

## Cleanup & Maintenance

### Remove Old Exports (30+ days)
```python
from datetime import datetime, timedelta
from database import get_db_connection

def cleanup_old_exports(days=30):
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Get old exports
            cur.execute("""
                SELECT id, file_path FROM data_exports
                WHERE created_at < %s
            """, (cutoff_date,))
            
            old_exports = cur.fetchall()
            
            # Delete files
            for export_id, file_path in old_exports:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete database records
            cur.execute("""
                DELETE FROM data_exports
                WHERE created_at < %s
            """, (cutoff_date,))
        
        conn.commit()

cleanup_old_exports()
```

### Disk Space Management
```bash
# Set up automated cleanup (cron)
0 2 * * * find /path/to/uploads -type f -mtime +90 -delete

# Or use Python scheduler
from schedule import every, run_pending
import time

def cleanup_task():
    cleanup_old_exports(days=90)

every().day.at("02:00").do(cleanup_task)

while True:
    run_pending()
    time.sleep(1)
```

---

## Common Issues & Solutions

### Issue: "Upload directory not writable"
**Solution**:
```bash
chmod -R 755 uploads
chmod -R u+w uploads
```

### Issue: "Out of disk space"
**Solution**:
```bash
# Check disk usage
df -h

# Remove old files
find uploads -type f -mtime +60 -delete

# Configure cleanup script
```

### Issue: "Database connection timeout during migration"
**Solution**:
```bash
# Increase timeout
export DATABASE_CONNECT_TIMEOUT=30

# Run migration with retry
python -c "
from services.migration_service import run_migrations
import time
for attempt in range(5):
    try:
        run_migrations()
        break
    except Exception as e:
        print(f'Attempt {attempt+1} failed: {e}')
        time.sleep(5)
"
```

### Issue: "File upload causes 413 error"
**Solution**: Check Flask MAX_CONTENT_LENGTH
```python
# Should be 50MB or larger
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
```

---

## Post-Deployment Verification

### Checklist
- [ ] All migrations completed successfully
- [ ] Upload directory created and writable
- [ ] File upload working for all allowed types
- [ ] Exports generating correctly
- [ ] Chatbot UI displays properly on all devices
- [ ] Authentication required for all endpoints
- [ ] Error handling working as expected
- [ ] Database indexes created
- [ ] File storage monitored
- [ ] Cleanup jobs scheduled

### Sign-Off
- [ ] Tested by Developer
- [ ] Tested by QA
- [ ] Approved by Product Manager
- [ ] Ready for Production

---

**Deployment Date**: _____________
**Deployed By**: _________________
**Verified By**: _________________
**Production URL**: ______________
