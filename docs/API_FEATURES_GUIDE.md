# Smart Campus Intelligence System - New Features API Documentation

## Overview
This document describes the new features added to the Smart Campus Intelligence System:
1. **Media Upload & File Management** - Upload and manage files with validation
2. **Data Export Services** - Export data to CSV, JSON, and other formats
3. **Chatbot UI Improvements** - Enhanced styling and responsiveness

---

## 🎯 Media Upload API

### Base URL
```
/media
```

### Authentication
All endpoints require a valid JWT token in the `Authorization` header:
```
Authorization: Bearer <token>
```

### Endpoints

#### 1. Upload File
**POST** `/media/upload`

Upload a file with automatic validation and storage.

**Request:**
```bash
curl -X POST http://localhost:5000/media/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "description=My project report"
```

**Form Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | File to upload (max 50MB) |
| description | String | No | Description of the file |

**Response (Success - 201):**
```json
{
  "success": true,
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "size": 2048576,
  "type": "pdf",
  "mime_type": "application/pdf"
}
```

**Response (Error - 400):**
```json
{
  "error": "File too large. Maximum size: 50.0MB"
}
```

**Allowed File Types:**
- Documents: pdf, doc, docx, txt, csv, xlsx, xls
- Images: jpg, jpeg, png, gif, webp
- Videos: mp4, avi, mov, mkv

---

#### 2. List User Files
**GET** `/media/list`

List all files uploaded by the current user.

**Request:**
```bash
curl -X GET "http://localhost:5000/media/list?limit=20&offset=0" \
  -H "Authorization: Bearer <token>"
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | Integer | 50 | Number of files to return (max 100) |
| offset | Integer | 0 | Pagination offset |

**Response (200):**
```json
{
  "success": true,
  "files": [
    {
      "id": 1,
      "file_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "report.pdf",
      "type": "pdf",
      "size": 1024576,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1,
  "limit": 20,
  "offset": 0
}
```

---

#### 3. Download File
**GET** `/media/<file_id>`

Download a file by its ID.

**Request:**
```bash
curl -X GET "http://localhost:5000/media/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>" \
  -o downloaded_file.pdf
```

**Response (200):**
- File is returned as attachment with correct MIME type

**Response (404):**
```json
{
  "error": "File not found or access denied"
}
```

---

#### 4. Delete File
**DELETE** `/media/<file_id>`

Delete a file from storage and database.

**Request:**
```bash
curl -X DELETE "http://localhost:5000/media/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

**Response (200):**
```json
{
  "success": true
}
```

---

#### 5. Toggle File Public/Private
**PUT** `/media/<file_id>/public`

Make a file public or private.

**Request:**
```bash
curl -X PUT "http://localhost:5000/media/550e8400-e29b-41d4-a716-446655440000/public" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"is_public": true}'
```

**Request Body:**
```json
{
  "is_public": true
}
```

**Response (200):**
```json
{
  "success": true
}
```

---

## 📊 Data Export API

### Base URL
```
/export
```

### Endpoints

#### 1. Export Student Marks to CSV
**GET** `/export/my-data/csv`

Export your marks to CSV format.

**Request:**
```bash
curl -X GET "http://localhost:5000/export/my-data/csv" \
  -H "Authorization: Bearer <token>" \
  -o marks_export.csv
```

**Response (200):**
- CSV file with columns: ID, Name, Email, Department, CGPA, Attendance, Mock Score, Skills Count, Status

---

#### 2. Export Student Data to JSON
**GET** `/export/my-data/json`

Export your complete data including marks, skills, and profile.

**Request:**
```bash
curl -X GET "http://localhost:5000/export/my-data/json" \
  -H "Authorization: Bearer <token>" \
  -o student_data.json
```

**Response (200):**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "department": "Computer Science",
  "cgpa": 3.8,
  "status": "Active",
  "marks": [
    {
      "subject": "Mathematics",
      "marks": 95,
      "percentage": 95.0,
      "grade": "A+",
      "date": "2024-01-10"
    }
  ],
  "skills": [
    {
      "skill": "Python",
      "level": "Advanced",
      "added_date": "2023-12-01"
    }
  ]
}
```

---

#### 3. Export Performance Report
**GET** `/export/performance-report`

Generate a comprehensive performance report in text format.

**Request:**
```bash
curl -X GET "http://localhost:5000/export/performance-report" \
  -H "Authorization: Bearer <token>" \
  -o performance_report.txt
```

**Response (200):**
```
SMART CAMPUS INTELLIGENCE SYSTEM
Performance Report
Generated: 2024-01-15 10:30:00

============================================================

STUDENT INFORMATION
============================================================
Name: John Doe
Student ID: 1
Email: john@example.com
Department: Computer Science

ACADEMIC METRICS
============================================================
CGPA: 3.8
Average Marks: 92%
Attendance: 88%
Mock Score: 85

[Full report continues...]
```

---

#### 4. Export Attendance to CSV (Faculty/Admin)
**GET** `/export/attendance/csv`

Export class attendance data (Faculty/Admin only).

**Request:**
```bash
curl -X GET "http://localhost:5000/export/attendance/csv" \
  -H "Authorization: Bearer <token>" \
  -o attendance_export.csv
```

**Response (200):**
- CSV file with columns: Student ID, Student Name, Subject, Total Classes, Present, Absent, Attendance %, Status

**Response (403):**
```json
{
  "error": "Access denied"
}
```

---

## 🎨 Chatbot UI Improvements

### Fixed Issues
✅ **Better Positioning** - Widget now uses fixed positioning with proper z-index management
✅ **Responsive Design** - Improved layout for mobile, tablet, and desktop screens
✅ **Dark Mode Support** - Full dark mode compatibility with CSS variables
✅ **Accessibility** - Added focus visible states and keyboard navigation
✅ **Animation Performance** - Optimized animations with prefers-reduced-motion support

### CSS Variables Used
```css
--primary: #4f46e5 (Primary brand color)
--bg-card: #fff (Card background)
--bg-sidebar: #0f172a (Dark sidebar)
--border-color: #e2e8f0 (Border color)
--text-primary: #0f172a (Primary text)
--text-muted: #94a3b8 (Muted text)
```

### Mobile Breakpoints
- **Mobile** (< 480px): Optimized for small screens
- **Tablet** (480px - 768px): Improved tablet layout
- **Desktop** (> 768px): Full-width layout

---

## 🗄️ Database Schema

### Media Table
```sql
CREATE TABLE media (
    id SERIAL PRIMARY KEY,
    file_id UUID UNIQUE NOT NULL,
    student_id INTEGER REFERENCES students(id),
    faculty_id INTEGER REFERENCES faculty(id),
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    mime_type VARCHAR(100),
    upload_path TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Exports Table
```sql
CREATE TABLE data_exports (
    id SERIAL PRIMARY KEY,
    export_id UUID UNIQUE NOT NULL,
    student_id INTEGER REFERENCES students(id),
    export_type VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    record_count INTEGER,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔒 Security Features

### File Upload Security
- **File Type Validation**: Only whitelisted extensions allowed
- **File Size Limits**: Maximum 50MB per file
- **MIME Type Detection**: Verify actual file type
- **Secure Filename**: Sanitize filenames using `secure_filename()`
- **Access Control**: Users can only access their own files

### Data Export Security
- **Role-Based Access**: Only authorized users can export specific data
- **User Isolation**: Students only export their own data
- **Audit Logging**: Track all export operations

---

## 📈 Performance Considerations

### Database Indexes
```sql
CREATE INDEX idx_media_file_id ON media(file_id);
CREATE INDEX idx_media_student_id ON media(student_id);
CREATE INDEX idx_media_created_at ON media(created_at DESC);
```

### Best Practices
- Use pagination for listing large numbers of files
- Limit export operations to reasonable record counts
- Consider compressing large files before export
- Implement caching for frequently accessed exports

---

## 🚀 Deployment Checklist

- [ ] Install new dependencies: `pip install -r requirements.txt`
- [ ] Run database migrations: `python -c "from services.migration_service import run_migrations; run_migrations()"`
- [ ] Create uploads directory: `mkdir uploads`
- [ ] Test file upload functionality
- [ ] Verify export endpoints work
- [ ] Test chatbot UI on mobile devices
- [ ] Monitor file storage usage
- [ ] Set up automated cleanup for old exports
- [ ] Configure CDN for file serving (optional)

---

## 📝 Example Usage

### Upload a file
```python
import requests

url = "http://localhost:5000/media/upload"
headers = {"Authorization": "Bearer <token>"}
files = {"file": open("document.pdf", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

### Export marks to CSV
```python
import requests

url = "http://localhost:5000/export/my-data/csv"
headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)
with open("marks.csv", "wb") as f:
    f.write(response.content)
```

### List user files
```python
import requests

url = "http://localhost:5000/media/list?limit=10"
headers = {"Authorization": "Bearer <token>"}

response = requests.get(url, headers=headers)
files = response.json()["files"]
for file in files:
    print(f"{file['filename']} - {file['size']} bytes")
```

---

## 🐛 Troubleshooting

### File Upload Issues
**Problem**: "File too large" error
- **Solution**: Ensure file size is < 50MB

**Problem**: "File type not allowed"
- **Solution**: Check file extension against allowed list

**Problem**: "Permission denied" on download
- **Solution**: Verify you own the file or it's public

### Export Issues
**Problem**: Export returns 403 "Access denied"
- **Solution**: Check user role (some exports require Faculty/Admin)

**Problem**: Export file is empty
- **Solution**: Ensure there's data to export

---

## 📞 Support & Contributing

For issues or improvements, please:
1. Check existing documentation
2. Review error messages carefully
3. Enable debug logging for troubleshooting
4. Document any custom extensions

---

**Version**: 1.0
**Last Updated**: January 2024
**Maintained By**: Smart Campus Development Team
