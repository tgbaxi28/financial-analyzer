# Document Processing & Password-Protected Files Guide

## Overview

The Financial Report Analyzer uses **IBM Granite-Docling** for unified, high-quality document processing across all supported formats. The system also provides built-in support for password-protected files, particularly encrypted PDFs.

## IBM Granite-Docling Integration

### What is Docling?

IBM Granite-Docling is a state-of-the-art document understanding library that:
- Provides consistent document extraction across multiple formats
- Extracts text, tables, and structural information with high accuracy
- Handles complex layouts and formatting
- Supports password-protected documents
- Preserves document structure and semantic relationships

### Supported File Formats

#### PDF Files
- **Regular PDFs**: Full text and table extraction
- **Password-Protected PDFs**: Encrypted PDFs with password support
- **Scanned PDFs**: OCR-capable (when enabled)
- **Complex Layouts**: Handles multi-column, mixed content documents

```bash
# Example: Upload a password-protected PDF
1. Go to Reports tab
2. Select your encrypted PDF
3. Enter password in "File Password" field
4. Click "Upload Report"
```

#### Excel Files (XLSX)
- All sheets are processed
- Preserves formulas and formatting information
- Converts to structured text for analysis
- Maintains sheet hierarchy

```python
# Result structure for Excel:
# === Sheet: Financial Summary ===
# Column1 | Column2 | Column3
# Value1  | Value2  | Value3
```

#### CSV Files
- Automatic delimiter detection (comma, semicolon, tab)
- Preserves headers and data types
- Handles quoted fields and escape sequences
- Formatted as structured tables

#### JSON Files
- Pretty-printed with indentation
- Nested structures preserved
- Array and object relationships maintained
- Schema-aware processing

#### DOCX Files
- Paragraph extraction with formatting preserved
- Embedded tables extracted
- Headers, footers, and text boxes included
- Maintains document hierarchy

### How Document Processing Works

```
┌─────────────────────┐
│  File Upload        │
│  (Select File)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Password Input     │
│  (if protected)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Docling Converter  │
│  (Extract Content)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Text & Structure   │
│  Extraction         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Chunking (1000     │
│  chars + 200 overlap)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Embedding         │
│  (LLM Provider)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  pgvector Storage  │
│  (Database)        │
└─────────────────────┘
```

## Password-Protected Files

### Why Password Protection?

Financial documents often contain sensitive information. Password protection ensures:
- **Confidentiality**: Only authorized users can access content
- **Integrity**: Encrypted PDFs can't be modified without the password
- **Compliance**: Meets regulatory requirements for data protection
- **Control**: Users can share files while maintaining security

### Supported Password Types

#### PDF Encryption
- ✅ Standard PDF 40-bit and 128-bit encryption
- ✅ AES-256 encryption (PDF 2.0)
- ❌ DRM-protected PDFs (not supported)
- ❌ Digitally signed PDFs with restrictions (not supported)

#### Other Formats
- Currently, password protection is primarily supported for PDF files
- Excel, DOCX, and other formats: Handle separately if encrypted

### Using Password-Protected Files

#### Step 1: Upload from Web Interface
```
1. Open Financial Report Analyzer (http://localhost:7860)
2. Navigate to "📄 Reports" tab
3. Select your password-protected PDF file
4. Enter the password in "File Password" field
5. Click "📤 Upload Report"
```

#### Step 2: Successful Upload
```
If successful, you'll see:
✅ Report uploaded successfully!
   Filename: financial_report_2024.pdf
   Chunks: 245
   Time: 3.42s
```

#### Step 3: Troubleshooting
```
If password fails:
🔒 File is password-protected but no password provided.
   Please enter the file password in the password field and try again.

If password is incorrect:
❌ Error: Password is incorrect. Please verify and try again.
```

### Handling Password Errors

| Error Message | Meaning | Solution |
|---|---|---|
| "File is password-protected but no password provided" | Password field was empty | Enter the correct password and retry |
| "Password is incorrect" | Wrong password entered | Verify password (case-sensitive) and retry |
| "Does not support password protection" | Format doesn't support passwords | Only PDF supports password protection currently |
| "File not found" | Upload failed before password check | Ensure file was properly selected |

### Password Security

**Important Security Notes:**

1. **Passwords are NOT stored** - They're used only during file processing
2. **In-memory only** - Passwords never touch disk or database
3. **Audit logging** - Query operations are logged, but never password details
4. **Single use** - Password is needed only at upload time
5. **HTTPS recommended** - Use HTTPS in production to protect password in transit

```
Password Processing Flow:
┌─────────────────────────────────┐
│ User enters password in UI       │
│ (HTTPS protected)               │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Password passed to Docling      │
│ (In-memory only)                │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Docling opens encrypted file    │
│ Password immediately discarded  │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Content extracted & chunked     │
│ Password cleared from memory    │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Embeddings stored (no password) │
│ in database                     │
└─────────────────────────────────┘
```

## Technical Implementation

### Document Processor Class

```python
from document_processor import DocumentProcessor

# Processing regular file
processor = DocumentProcessor(
    file_path="/uploads/report.pdf",
    file_type="pdf",
    password=None  # Regular file
)
full_text, chunks = processor.process()

# Processing password-protected file
processor = DocumentProcessor(
    file_path="/uploads/encrypted_report.pdf",
    file_type="pdf",
    password="MySecurePassword123"  # Password provided
)
full_text, chunks = processor.process()
```

### Error Handling

```python
try:
    processor = DocumentProcessor(file_path, file_type, password)
    full_text, chunks = processor.process()
except ValueError as ve:
    # Handle password-related errors
    if "password" in str(ve).lower():
        print(f"🔒 {ve}")
    else:
        print(f"❌ {ve}")
except Exception as e:
    # Handle other processing errors
    print(f"❌ Processing failed: {e}")
```

### Chunk Structure

Each chunk contains:
```python
{
    "text": "chunk_content_text...",
    "chunk_index": 0,
    "page_number": 1,
    "section_type": "page_1"
}
```

## Configuration

### Environment Variables

```bash
# In .env file

# Document Processing
CHUNK_SIZE=1000              # Characters per chunk
CHUNK_OVERLAP=200            # Overlap between chunks
MIN_TEXT_LENGTH=500          # Minimum processable text

# File Upload
MAX_FILE_SIZE_MB=100         # Maximum file size
UPLOAD_DIR=./uploads         # Where files are temporarily stored

# Processing
DOCLING_LANGUAGE_HINTS=en    # Language optimization
```

## Performance Metrics

### Processing Speed (Typical)

| Format | Size | Time | Chunks |
|--------|------|------|--------|
| PDF (20 pages) | 5 MB | 2-4 sec | 150-200 |
| Excel (5 sheets) | 2 MB | 1-2 sec | 80-120 |
| CSV (10K rows) | 3 MB | 1-2 sec | 100-150 |
| JSON (nested) | 1 MB | <1 sec | 50-80 |
| DOCX (50 pages) | 4 MB | 2-3 sec | 120-180 |

### Embedding Generation

After chunking, embeddings are generated:

| Provider | Model | Time per Chunk | Batch Size |
|----------|-------|---|---|
| Azure OpenAI | text-embedding-3-small | 15-20 ms | 20 |
| Google Gemini | embedding-001 | 20-25 ms | 10 |
| AWS Bedrock | Titan | 10-15 ms | 25 |

## Troubleshooting

### File Won't Upload

**Problem**: "Error processing document: ..."

**Solutions**:
1. Check file is not corrupted: Try opening in native application
2. Verify file format: Use correct file extension
3. Check file size: Must be under MAX_FILE_SIZE_MB
4. Review logs: `docker-compose logs app`

### Password Not Working

**Problem**: "Password is incorrect"

**Solutions**:
1. Verify password is case-sensitive
2. Try copying password from secure location
3. Ensure file is actually password-protected
4. Try opening PDF locally to verify password works

### Docling Import Error

**Problem**: "ImportError: No module named 'docling'"

**Solutions**:
1. Ensure requirements.txt is installed: `pip install -r requirements.txt`
2. Restart container: `docker-compose restart app`
3. Rebuild container: `docker-compose build --no-cache app`

### Out of Memory During Processing

**Problem**: Large file causes memory error

**Solutions**:
1. Increase container memory: Edit docker-compose.yml
   ```yaml
   services:
     app:
       mem_limit: 2g  # Increase from 1g
   ```
2. Reduce MAX_FILE_SIZE_MB in .env
3. Split large documents into smaller files

## Best Practices

### For Users

1. **Use passwords for sensitive documents**
   - Financial statements with proprietary data
   - Documents with merger/acquisition information
   - Competitive analysis reports

2. **Remember passwords**
   - Passwords are not stored
   - You'll need to provide them again if re-uploading

3. **Organize by sensitivity**
   - Use separate systems for highly sensitive data
   - Apply document classification labels

4. **Monitor access**
   - Check audit logs regularly
   - Review who accesses which reports

### For Administrators

1. **Monitor disk space**
   - Documents are temporarily stored during processing
   - Implement cleanup policies for old uploads

2. **Enable HTTPS**
   - Protects passwords in transit
   - Use SSL certificates in production

3. **Regular backups**
   - Back up PostgreSQL database regularly
   - Test restore procedures

4. **Log rotation**
   - Implement log rotation to prevent disk filling
   - Archive logs for compliance

## Advanced Usage

### Batch Processing Password-Protected Files

```python
import os
from document_processor import DocumentProcessor
from pathlib import Path

# Directory of password-protected PDFs
secure_docs = "/path/to/secure/documents"
passwords = {
    "report1.pdf": "password1",
    "report2.pdf": "password2",
    "report3.pdf": "password3"
}

results = []
for filename, password in passwords.items():
    file_path = os.path.join(secure_docs, filename)
    
    try:
        processor = DocumentProcessor(
            file_path=file_path,
            file_type="pdf",
            password=password
        )
        full_text, chunks = processor.process()
        
        results.append({
            "filename": filename,
            "status": "success",
            "chunks": len(chunks)
        })
    except Exception as e:
        results.append({
            "filename": filename,
            "status": "failed",
            "error": str(e)
        })

# Summary
print(f"Processed {len(results)} files")
for result in results:
    status_icon = "✅" if result["status"] == "success" else "❌"
    print(f"{status_icon} {result['filename']}: {result.get('chunks', result.get('error'))}")
```

## Summary

The Financial Report Analyzer now provides:

✅ **Unified Document Processing** - All formats handled consistently via Docling
✅ **Password Support** - Encrypted PDFs can be uploaded and processed securely
✅ **Runtime Credentials** - Passwords never stored, only used during processing
✅ **Quality Extraction** - Tables, text, and structure preserved accurately
✅ **Performance** - Fast processing with reasonable memory footprint
✅ **Security** - No password logging, in-memory only, HTTPS ready

For questions or issues, refer to the troubleshooting section or check logs:
```bash
docker-compose logs -f app
```
