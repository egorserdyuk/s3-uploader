#!/usr/bin/env python3
"""S3 Uploader - CLI tool for managing S3 operations
Upload, download, move, and remove files from S3 servers using Boto3
"""

import argparse
import json
import logging
import os
import sys
from typing import Optional, Tuple
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
from colorama import Fore, init
from tqdm import tqdm

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("s3_uploader.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class S3Uploader:
    """Main S3 operations class"""

    def __init__(self, creds_file: str = "creds.json"):
        """Initialize S3 Uploader with credentials

        Args:
            creds_file (str): Path to credentials JSON file

        """
        self.creds_file = creds_file
        self.s3_client = None
        self.bucket_name = None
        self.connected = False

        # Load and validate credentials
        self._load_credentials()
        self._connect_to_s3()

    def _load_credentials(self) -> None:
        """Load credentials from JSON file"""
        try:
            if not os.path.exists(self.creds_file):
                logger.error(f"Credentials file not found: {self.creds_file}")
                print(f"{Fore.RED}Error: Credentials file not found: {self.creds_file}")
                print(
                    f"{Fore.YELLOW}Please create a {self.creds_file} file with your S3 credentials.",
                )
                sys.exit(1)

            with open(self.creds_file) as f:
                self.credentials = json.load(f)

            required_fields = [
                "aws_access_key_id",
                "aws_secret_access_key",
                "region_name",
            ]
            missing_fields = [
                field for field in required_fields if field not in self.credentials
            ]

            if missing_fields:
                logger.error(
                    f"Missing required fields in credentials: {missing_fields}",
                )
                print(
                    f"{Fore.RED}Error: Missing required fields in credentials: {missing_fields}",
                )
                sys.exit(1)

            logger.info("Credentials loaded successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in credentials file: {e}")
            print(f"{Fore.RED}Error: Invalid JSON in credentials file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            print(f"{Fore.RED}Error loading credentials: {e}")
            sys.exit(1)

    def _connect_to_s3(self) -> None:
        """Establish connection to S3"""
        try:
            # Create S3 client
            client_params = {
                "aws_access_key_id": self.credentials["aws_access_key_id"],
                "aws_secret_access_key": self.credentials["aws_secret_access_key"],
                "region_name": self.credentials["region_name"],
            }

            # Add endpoint URL if provided (for custom S3-compatible services)
            if "endpoint_url" in self.credentials:
                client_params["endpoint_url"] = self.credentials["endpoint_url"]

            self.s3_client = boto3.client("s3", **client_params)

            # Test connection by listing buckets
            self.s3_client.list_buckets()
            self.connected = True
            logger.info("Successfully connected to S3")
            print(f"{Fore.GREEN}✓ Connected to S3 successfully")

        except NoCredentialsError:
            logger.error("AWS credentials not found or invalid")
            print(f"{Fore.RED}Error: AWS credentials not found or invalid")
            sys.exit(1)
        except EndpointConnectionError as e:
            logger.error(f"Cannot connect to S3 endpoint: {e}")
            print(f"{Fore.RED}Error: Cannot connect to S3 endpoint: {e}")
            sys.exit(1)
        except ClientError as e:
            logger.error(f"Authentication failed: {e}")
            print(f"{Fore.RED}Error: Authentication failed: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            print(f"{Fore.RED}Error connecting to S3: {e}")
            sys.exit(1)

    def _parse_s3_path(self, s3_path: str) -> tuple[str, str]:
        """Parse S3 path into bucket and key

        Args:
            s3_path (str): S3 path in format s3://bucket/key or bucket/key

        Returns:
            Tuple[str, str]: (bucket_name, key)

        """
        if s3_path.startswith("s3://"):
            # Parse s3://bucket/key format
            parsed = urlparse(s3_path)
            bucket_name = parsed.netloc
            key = parsed.path.lstrip("/")
        else:
            # Parse bucket/key format
            parts = s3_path.split("/", 1)
            bucket_name = parts[0]
            key = parts[1] if len(parts) > 1 else ""

        if not bucket_name:
            raise ValueError("Invalid S3 path: bucket name is required")

        return bucket_name, key

    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    def upload(
        self,
        local_path: str,
        s3_path: str,
        bucket_name: str | None = None,
    ) -> None:
        """Upload file to S3

        Args:
            local_path (str): Local file path
            s3_path (str): S3 destination path
            bucket_name (str, optional): Bucket name (if not in s3_path)

        """
        try:
            # Parse S3 path
            if bucket_name:
                s3_bucket = bucket_name
                s3_key = s3_path
            else:
                s3_bucket, s3_key = self._parse_s3_path(s3_path)

            # Ensure local file exists
            if not os.path.exists(local_path):
                logger.error(f"Local file not found: {local_path}")
                print(f"{Fore.RED}Error: Local file not found: {local_path}")
                return

            # Get file size for progress bar
            file_size = self._get_file_size(local_path)

            print(f"{Fore.CYAN}Uploading {local_path} to s3://{s3_bucket}/{s3_key}")

            # Upload with progress bar
            with tqdm(
                total=file_size,
                unit="B",
                unit_scale=True,
                desc="Uploading",
            ) as pbar:
                self.s3_client.upload_file(
                    local_path,
                    s3_bucket,
                    s3_key,
                    Callback=lambda bytes_transferred: pbar.update(bytes_transferred),
                )

            logger.info(
                f"Successfully uploaded {local_path} to s3://{s3_bucket}/{s3_key}",
            )
            print(f"{Fore.GREEN}✓ Upload completed successfully")

        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            print(f"{Fore.RED}Upload failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            print(f"{Fore.RED}Unexpected error: {e}")

    def download(
        self,
        s3_path: str,
        local_path: str,
        bucket_name: str | None = None,
    ) -> None:
        """Download file from S3

        Args:
            s3_path (str): S3 source path
            local_path (str): Local destination path
            bucket_name (str, optional): Bucket name (if not in s3_path)

        """
        try:
            # Parse S3 path
            if bucket_name:
                s3_bucket = bucket_name
                s3_key = s3_path
            else:
                s3_bucket, s3_key = self._parse_s3_path(s3_path)

            # Create local directory if needed
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)

            print(f"{Fore.CYAN}Downloading s3://{s3_bucket}/{s3_key} to {local_path}")

            # Get file size for progress bar
            try:
                head_response = self.s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                file_size = head_response.get("ContentLength", 0)
            except Exception as e:
                file_size = 0
                print(f"{Fore.RED}Unexpected error: {e}")

            # Download with progress bar
            with tqdm(
                total=file_size,
                unit="B",
                unit_scale=True,
                desc="Downloading",
            ) as pbar:
                self.s3_client.download_file(
                    s3_bucket,
                    s3_key,
                    local_path,
                    Callback=lambda bytes_transferred: pbar.update(bytes_transferred),
                )

            logger.info(
                f"Successfully downloaded s3://{s3_bucket}/{s3_key} to {local_path}",
            )
            print(f"{Fore.GREEN}✓ Download completed successfully")

        except ClientError as e:
            logger.error(f"Download failed: {e}")
            print(f"{Fore.RED}Download failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            print(f"{Fore.RED}Unexpected error: {e}")

    def move(
        self,
        source_path: str,
        dest_path: str,
        source_bucket: str | None = None,
        dest_bucket: str | None = None,
    ) -> None:
        """Move file within S3 (copy then delete)

        Args:
            source_path (str): Source S3 path
            dest_path (str): Destination S3 path
            source_bucket (str, optional): Source bucket name
            dest_bucket (str, optional): Destination bucket name

        """
        try:
            # Parse source path
            if source_bucket:
                src_bucket = source_bucket
                src_key = source_path
            else:
                src_bucket, src_key = self._parse_s3_path(source_path)

            # Parse destination path
            if dest_bucket:
                dst_bucket = dest_bucket
                dst_key = dest_path
            else:
                dst_bucket, dst_key = self._parse_s3_path(dest_path)

            print(
                f"{Fore.CYAN}Moving s3://{src_bucket}/{src_key} to s3://{dst_bucket}/{dst_key}",
            )

            # Copy object
            copy_source = {"Bucket": src_bucket, "Key": src_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=dst_bucket,
                Key=dst_key,
            )

            # Delete source object
            self.s3_client.delete_object(Bucket=src_bucket, Key=src_key)

            logger.info(
                f"Successfully moved s3://{src_bucket}/{src_key} to s3://{dst_bucket}/{dst_key}",
            )
            print(f"{Fore.GREEN}✓ Move completed successfully")

        except ClientError as e:
            logger.error(f"Move failed: {e}")
            print(f"{Fore.RED}Move failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during move: {e}")
            print(f"{Fore.RED}Unexpected error: {e}")

    def remove(self, s3_path: str, bucket_name: str | None = None) -> None:
        """Remove file from S3

        Args:
            s3_path (str): S3 path to remove
            bucket_name (str, optional): Bucket name (if not in s3_path)

        """
        try:
            # Parse S3 path
            if bucket_name:
                s3_bucket = bucket_name
                s3_key = s3_path
            else:
                s3_bucket, s3_key = self._parse_s3_path(s3_path)

            print(f"{Fore.CYAN}Removing s3://{s3_bucket}/{s3_key}")

            # Delete object
            self.s3_client.delete_object(Bucket=s3_bucket, Key=s3_key)

            logger.info(f"Successfully removed s3://{s3_bucket}/{s3_key}")
            print(f"{Fore.GREEN}✓ Remove completed successfully")

        except ClientError as e:
            logger.error(f"Remove failed: {e}")
            print(f"{Fore.RED}Remove failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during remove: {e}")
            print(f"{Fore.RED}Unexpected error: {e}")

    def list_files(self, s3_path: str, bucket_name: str | None = None) -> None:
        """List files in S3 bucket/path

        Args:
            s3_path (str): S3 path to list
            bucket_name (str, optional): Bucket name (if not in s3_path)

        """
        try:
            # Parse S3 path
            if bucket_name:
                s3_bucket = bucket_name
                s3_prefix = s3_path
            else:
                s3_bucket, s3_prefix = self._parse_s3_path(s3_path)

            # Ensure prefix ends with / for directory listing
            if s3_prefix and not s3_prefix.endswith("/"):
                s3_prefix += "/"

            print(f"{Fore.CYAN}Listing files in s3://{s3_bucket}/{s3_prefix}")

            # List objects
            paginator = self.s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=s3_bucket, Prefix=s3_prefix)

            files_found = False
            total_size = 0

            for page in page_iterator:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        size = obj["Size"]
                        last_modified = obj["LastModified"]

                        # Skip the prefix itself if it's listed
                        if key == s3_prefix:
                            continue

                        files_found = True
                        total_size += size

                        # Format size
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        elif size < 1024 * 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        else:
                            size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"

                        print(
                            f"  {key:<50} {size_str:>10}  {last_modified.strftime('%Y-%m-%d %H:%M:%S')}",
                        )

            if not files_found:
                print(f"{Fore.YELLOW}No files found in s3://{s3_bucket}/{s3_prefix}")
            else:
                print(f"\n{Fore.CYAN}Total: {total_size} bytes")

            logger.info(f"Listed files in s3://{s3_bucket}/{s3_prefix}")

        except ClientError as e:
            logger.error(f"List failed: {e}")
            print(f"{Fore.RED}List failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during list: {e}")
            print(f"{Fore.RED}Unexpected error: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="S3 Uploader - CLI tool for managing S3 operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Upload a file:     s3_uploader.py upload local_file.txt s3://my-bucket/files/
  Download a file:   s3_uploader.py download s3://my-bucket/files/file.txt ./local_file.txt
  Move a file:       s3_uploader.py move s3://my-bucket/old/file.txt s3://my-bucket/new/file.txt
  Remove a file:     s3_uploader.py remove s3://my-bucket/files/file.txt
  List files:        s3_uploader.py list s3://my-bucket/files/
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload file to S3")
    upload_parser.add_argument("local_path", help="Local file path")
    upload_parser.add_argument(
        "s3_path",
        help="S3 destination path (s3://bucket/key or bucket/key)",
    )
    upload_parser.add_argument("--bucket", help="Bucket name (if not in s3_path)")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download file from S3")
    download_parser.add_argument(
        "s3_path",
        help="S3 source path (s3://bucket/key or bucket/key)",
    )
    download_parser.add_argument("local_path", help="Local destination path")
    download_parser.add_argument("--bucket", help="Bucket name (if not in s3_path)")

    # Move command
    move_parser = subparsers.add_parser("move", help="Move file within S3")
    move_parser.add_argument(
        "source_path",
        help="Source S3 path (s3://bucket/key or bucket/key)",
    )
    move_parser.add_argument(
        "dest_path",
        help="Destination S3 path (s3://bucket/key or bucket/key)",
    )
    move_parser.add_argument(
        "--source-bucket",
        help="Source bucket name (if not in source_path)",
    )
    move_parser.add_argument(
        "--dest-bucket",
        help="Destination bucket name (if not in dest_path)",
    )

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove file from S3")
    remove_parser.add_argument(
        "s3_path",
        help="S3 path to remove (s3://bucket/key or bucket/key)",
    )
    remove_parser.add_argument("--bucket", help="Bucket name (if not in s3_path)")

    # List command
    list_parser = subparsers.add_parser("list", help="List files in S3")
    list_parser.add_argument(
        "s3_path",
        help="S3 path to list (s3://bucket/path or bucket/path)",
    )
    list_parser.add_argument("--bucket", help="Bucket name (if not in s3_path)")

    # Global options
    parser.add_argument(
        "--creds",
        default="creds.json",
        help="Path to credentials file (default: creds.json)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Initialize S3 uploader
        uploader = S3Uploader(args.creds)

        # Execute command
        if args.command == "upload":
            uploader.upload(
                args.local_path,
                args.s3_path,
                getattr(args, "bucket", None),
            )
        elif args.command == "download":
            uploader.download(
                args.s3_path,
                args.local_path,
                getattr(args, "bucket", None),
            )
        elif args.command == "move":
            uploader.move(
                args.source_path,
                args.dest_path,
                getattr(args, "source_bucket", None),
                getattr(args, "dest_bucket", None),
            )
        elif args.command == "remove":
            uploader.remove(args.s3_path, getattr(args, "bucket", None))
        elif args.command == "list":
            uploader.list_files(args.s3_path, getattr(args, "bucket", None))

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"{Fore.RED}Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
