# S3 Uploader

A powerful command-line tool for managing files on S3-compatible storage services. Built with Python and Boto3, this tool provides an intuitive interface for uploading, downloading, moving, and removing files from S3 servers.

## Features

- **Upload**: Upload local files to S3 buckets
- **Download**: Download files from S3 to your local machine
- **Move**: Move files within S3 (copy and delete operation)
- **Remove**: Delete files from S3 buckets
- **List**: List files in S3 buckets with detailed information
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Progress tracking**: Real-time progress bars for uploads and downloads
- **Credentials management**: Secure JSON-based credential storage
- **Logging**: Comprehensive logging with file and console output
- **Colorized output**: Easy-to-read colored terminal output

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Manual Installation

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install boto3 botocore colorama tqdm
   ```
3. Create your credentials file (see below)

## Configuration

### Credentials Setup

Create a `creds.json` file in the project directory with your S3 credentials:

```json
{
  "aws_access_key_id": "YOUR_ACCESS_KEY",
  "aws_secret_access_key": "YOUR_SECRET_KEY",
  "region_name": "us-east-1",
  "endpoint_url": "https://your-s3-endpoint.com"
}
```

**Required fields:**
- `aws_access_key_id`: Your AWS/S3 access key
- `aws_secret_access_key`: Your AWS/S3 secret key
- `region_name`: AWS region (e.g., "us-east-1", "eu-west-1")

**Optional fields:**
- `endpoint_url`: Custom S3 endpoint URL (for S3-compatible services like MinIO, DigitalOcean Spaces, etc.)

### Example Credentials

For AWS S3:
```json
{
  "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
  "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "region_name": "us-east-1"
}
```

For MinIO:
```json
{
  "aws_access_key_id": "minioadmin",
  "aws_secret_access_key": "minioadmin",
  "region_name": "us-east-1",
  "endpoint_url": "http://localhost:9000"
}
```

## Usage

### Basic Commands

```bash
python s3_uploader.py [command] [options]
```

### Upload Files

Upload a local file to S3:

```bash
# Upload to specific bucket and path
python s3_uploader.py upload local_file.txt s3://my-bucket/files/

# Upload with explicit bucket name
python s3_uploader.py upload local_file.txt files/ --bucket my-bucket

# Upload multiple files
python s3_uploader.py upload image.jpg s3://my-bucket/images/
python s3_uploader.py upload document.pdf s3://my-bucket/documents/
```

### Download Files

Download files from S3 to your local machine:

```bash
# Download with full S3 path
python s3_uploader.py download s3://my-bucket/files/file.txt ./local_file.txt

# Download with explicit bucket name
python s3_uploader.py download files/file.txt ./local_file.txt --bucket my-bucket

# Download to specific directory
python s3_uploader.py download s3://my-bucket/images/photo.jpg ./downloads/photo.jpg
```

### Move Files

Move files within S3 (copy to new location, then delete original):

```bash
# Move within same bucket
python s3_uploader.py move s3://my-bucket/old/file.txt s3://my-bucket/new/file.txt

# Move between different buckets
python s3_uploader.py move s3://source-bucket/file.txt s3://dest-bucket/file.txt

# Move with explicit bucket names
python s3_uploader.py move old/file.txt new/file.txt --source-bucket source-bucket --dest-bucket dest-bucket
```

### Remove Files

Delete files from S3:

```bash
# Remove with full S3 path
python s3_uploader.py remove s3://my-bucket/files/file.txt

# Remove with explicit bucket name
python s3_uploader.py remove files/file.txt --bucket my-bucket
```

### List Files

List files in a bucket or path:

```bash
# List files in bucket
python s3_uploader.py list s3://my-bucket/

# List files in specific path
python s3_uploader.py list s3://my-bucket/files/

# List with explicit bucket name
python s3_uploader.py list files/ --bucket my-bucket
```

## Command Reference

### Global Options

- `--creds FILE`: Path to credentials file (default: creds.json)
- `--verbose, -v`: Enable verbose logging

### Command-Specific Options

#### Upload
- `local_path`: Local file to upload
- `s3_path`: S3 destination path
- `--bucket BUCKET`: Bucket name (if not in s3_path)

#### Download
- `s3_path`: S3 source path
- `local_path`: Local destination path
- `--bucket BUCKET`: Bucket name (if not in s3_path)

#### Move
- `source_path`: Source S3 path
- `dest_path`: Destination S3 path
- `--source-bucket BUCKET`: Source bucket name
- `--dest-bucket BUCKET`: Destination bucket name

#### Remove
- `s3_path`: S3 path to remove
- `--bucket BUCKET`: Bucket name (if not in s3_path)

#### List
- `s3_path`: S3 path to list
- `--bucket BUCKET`: Bucket name (if not in s3_path)

## Building Executables

Use the provided PyInstaller build script to create standalone executables:

### Build for Current Platform

```bash
python build.py
```

### Build for Specific Platform

```bash
# Build for Windows x64
python build.py --platform windows --arch x64

# Build for macOS ARM64
python build.py --platform darwin --arch arm64

# Build for Linux x86
python build.py --platform linux --arch x86
```

### Build for All Platforms

```bash
python build.py --all
```

### Build Options

- `--platform PLATFORM`: Target platform (windows, darwin, linux)
- `--arch ARCH`: Target architecture (x86, x64, arm64, armv7l)
- `--output DIR`: Output directory (default: dist)
- `--all`: Build for all supported platforms
- `--clean`: Clean output directory before building

### Generated Executables

The build script creates platform-specific executables in the `dist/` directory:

```
dist/
├── windows/
│   ├── x64/s3-uploader-win64.exe
│   ├── x86/s3-uploader-win32.exe
│   └── arm64/s3-uploader-winarm64.exe
├── darwin/
│   ├── x64/s3-uploader-macos64
│   └── arm64/s3-uploader-macosarm64
├── linux/
│   ├── x64/s3-uploader-linux64
│   ├── x86/s3-uploader-linux32
│   ├── arm64/s3-uploader-linuxarm64
│   └── armv7l/s3-uploader-linuxarmv7
├── install.sh
└── README.md
```

## Examples

### Complete Workflow

1. **Upload a file:**
   ```bash
   python s3_uploader.py upload report.pdf s3://company-docs/quarterly/
   ```

2. **List files in the bucket:**
   ```bash
   python s3_uploader.py list s3://company-docs/quarterly/
   ```

3. **Download the file:**
   ```bash
   python s3_uploader.py download s3://company-docs/quarterly/report.pdf ./downloads/report.pdf
   ```

4. **Move to archive:**
   ```bash
   python s3_uploader.py move s3://company-docs/quarterly/report.pdf s3://company-docs/archive/2023/
   ```

5. **Remove from archive:**
   ```bash
   python s3_uploader.py remove s3://company-docs/archive/2023/report.pdf
   ```

### Using with MinIO

```bash
# Upload to MinIO
python s3_uploader.py upload test.txt s3://test-bucket/minio-test/

# Download from MinIO
python s3_uploader.py download s3://test-bucket/minio-test/test.txt ./local-test.txt
```

## Error Handling

The tool provides comprehensive error handling and logging:

- **Connection errors**: Failed to connect to S3 endpoint
- **Authentication errors**: Invalid credentials
- **File not found**: Local file doesn't exist or S3 object not found
- **Permission errors**: Insufficient permissions for operations
- **Network errors**: Timeout or connection issues during transfer

All errors are logged to both console and `s3_uploader.log` file.

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**
   - Ensure `creds.json` exists in the project directory
   - Check file permissions

2. **"Authentication failed"**
   - Verify your access key and secret key
   - Check if credentials have necessary S3 permissions

3. **"Cannot connect to S3 endpoint"**
   - Check internet connection
   - Verify endpoint URL is correct
   - Check if custom endpoint requires special configuration

4. **"File not found"**
   - For uploads: Check local file path exists
   - For downloads: Verify S3 object exists and path is correct

### Verbose Logging

Enable verbose logging for detailed debugging:

```bash
python s3_uploader.py --verbose upload file.txt s3://bucket/
```

## Security Notes

- Store credentials securely and never commit `creds.json` to version control
- Use environment variables or AWS IAM roles for production deployments
- Consider using AWS Secrets Manager or similar services for credential management
- Regularly rotate access keys and monitor usage

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or feature requests:

1. Check the troubleshooting section above
2. Review the logs in `s3_uploader.log`
3. Create an issue on GitHub with detailed information

## Dependencies

- **boto3**: AWS SDK for Python
- **botocore**: Low-level AWS SDK components
- **colorama**: Cross-platform colored terminal text
- **tqdm**: Progress bars for loops
- **argparse**: Command-line argument parsing (built-in)

## Version History

- **1.0.0**: Initial release with basic upload, download, move, remove, and list operations