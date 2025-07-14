"""
Security tests for path traversal vulnerability fix.

This module tests the security improvements made to file upload and deletion
operations to prevent path traversal attacks.
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, MagicMock
from fastapi import HTTPException
from fastapi.responses import JSONResponse

# Import the functions we're testing
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.server.server_utils import (
    secure_filename, 
    validate_file_path, 
    handle_file_upload, 
    handle_file_deletion
)


class TestSecureFilename:
    """Test the secure_filename function against various attack vectors."""
    
    def test_basic_filename(self):
        """Test that normal filenames pass through unchanged."""
        assert secure_filename("document.pdf") == "document.pdf"
        assert secure_filename("report_2024.docx") == "report_2024.docx"
    
    def test_path_traversal_attacks(self):
        """Test that path traversal attempts are blocked."""
        with pytest.raises(ValueError):
            secure_filename("../../../etc/passwd")
        
        with pytest.raises(ValueError):
            secure_filename("..\\..\\windows\\system32\\config\\SAM")
        
        # Multiple traversal attempts
        assert secure_filename("....//....//etc/passwd") == "etcpasswd"
    
    def test_null_byte_injection(self):
        """Test that null byte injection is prevented."""
        # Null bytes should be removed
        result = secure_filename("test\x00.txt")
        assert "\x00" not in result
        assert result == "test.txt"
    
    def test_control_characters(self):
        """Test that control characters are removed."""
        # Test various control characters
        result = secure_filename("test\x01\x02\x03file.txt")
        assert result == "testfile.txt"
    
    def test_unicode_normalization(self):
        """Test that unicode attacks are prevented."""
        # Test unicode normalization
        filename = "test\u202e\u202dfile.txt"  # Right-to-left override
        result = secure_filename(filename)
        # Should be normalized and safe
        assert len(result) > 0
    
    def test_drive_letters_windows(self):
        """Test that Windows drive letters are removed."""
        assert secure_filename("C:sensitive.txt") == "sensitive.txt"
        assert secure_filename("D:important.doc") == "important.doc"
    
    def test_reserved_names_windows(self):
        """Test that Windows reserved names are blocked."""
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'LPT1']
        
        for name in reserved_names:
            with pytest.raises(ValueError, match="reserved name"):
                secure_filename(f"{name}.txt")
            
            with pytest.raises(ValueError, match="reserved name"):
                secure_filename(name.lower())
    
    def test_empty_filename(self):
        """Test that empty filenames are rejected."""
        with pytest.raises(ValueError, match="empty"):
            secure_filename("")
        
        with pytest.raises(ValueError, match="empty"):
            secure_filename("   ")  # Only spaces
        
        with pytest.raises(ValueError, match="empty"):
            secure_filename("...")  # Only dots
    
    def test_filename_length_limit(self):
        """Test that overly long filenames are rejected."""
        # Create a filename longer than 255 bytes
        long_filename = "a" * 300 + ".txt"
        with pytest.raises(ValueError, match="too long"):
            secure_filename(long_filename)
    
    def test_leading_dots_spaces(self):
        """Test that leading dots and spaces are removed."""
        assert secure_filename("...file.txt") == "file.txt"
        assert secure_filename("   file.txt") == "file.txt"
        assert secure_filename(". . .file.txt") == "file.txt"


class TestValidateFilePath:
    """Test the validate_file_path function."""
    
    def test_valid_path(self):
        """Test that valid paths within base directory are accepted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            result = validate_file_path(file_path, temp_dir)
            assert result == os.path.abspath(file_path)
    
    def test_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Try to escape the directory
            malicious_path = os.path.join(temp_dir, "..", "..", "etc", "passwd")
            
            with pytest.raises(ValueError, match="outside allowed directory"):
                validate_file_path(malicious_path, temp_dir)
    
    def test_symlink_traversal_blocked(self):
        """Test that symlink-based traversal is blocked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a symlink pointing outside the directory
            outside_file = "/tmp/test_target.txt"
            symlink_path = os.path.join(temp_dir, "malicious_link")
            
            try:
                os.symlink(outside_file, symlink_path)
                target_path = os.path.join(temp_dir, "malicious_link", "nested")
                
                with pytest.raises(ValueError, match="outside allowed directory"):
                    validate_file_path(target_path, temp_dir)
            except OSError:
                # Skip if symlinks aren't supported (e.g., Windows without admin)
                pytest.skip("Symlinks not supported in this environment")


class TestHandleFileUpload:
    """Test the secure file upload functionality."""
    
    @pytest.fixture
    def mock_file(self):
        """Create a mock file object for testing."""
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.file = Mock()
        return mock_file
    
    @pytest.fixture
    def temp_doc_path(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_normal_file_upload(self, mock_file, temp_doc_path):
        """Test that normal file uploads work correctly."""
        # NOTE: Not fully tested with DocumentLoader due to automated environment limits
        # Manual testing recommended for: DocumentLoader integration
        
        # Mock the DocumentLoader to avoid dependency issues
        import backend.server.server_utils
        original_loader = backend.server.server_utils.DocumentLoader
        
        class MockDocumentLoader:
            def __init__(self, path):
                self.path = path
            async def load(self):
                pass
        
        backend.server.server_utils.DocumentLoader = MockDocumentLoader
        
        try:
            result = await handle_file_upload(mock_file, temp_doc_path)
            
            assert result["filename"] == "test.txt"
            assert temp_doc_path in result["path"]
            assert os.path.exists(result["path"])
        finally:
            # Restore original loader
            backend.server.server_utils.DocumentLoader = original_loader
    
    @pytest.mark.asyncio
    async def test_malicious_filename_upload(self, temp_doc_path):
        """Test that malicious filenames are rejected."""
        mock_file = Mock()
        mock_file.filename = "../../../etc/passwd"
        mock_file.file = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await handle_file_upload(mock_file, temp_doc_path)
        
        assert exc_info.value.status_code == 400
        assert "Invalid file" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_empty_filename_upload(self, temp_doc_path):
        """Test that empty filenames are rejected."""
        mock_file = Mock()
        mock_file.filename = ""
        mock_file.file = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await handle_file_upload(mock_file, temp_doc_path)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_file_conflict_handling(self, mock_file, temp_doc_path):
        """Test that file conflicts are handled by creating unique names."""
        # Create an existing file
        existing_path = os.path.join(temp_doc_path, "test.txt")
        os.makedirs(temp_doc_path, exist_ok=True)
        with open(existing_path, "w") as f:
            f.write("existing content")
        
        # Mock DocumentLoader
        import backend.server.server_utils
        original_loader = backend.server.server_utils.DocumentLoader
        
        class MockDocumentLoader:
            def __init__(self, path):
                pass
            async def load(self):
                pass
        
        backend.server.server_utils.DocumentLoader = MockDocumentLoader
        
        try:
            result = await handle_file_upload(mock_file, temp_doc_path)
            
            # Should create a unique filename
            assert result["filename"] == "test_1.txt"
            assert os.path.exists(result["path"])
        finally:
            backend.server.server_utils.DocumentLoader = original_loader


class TestHandleFileDeletion:
    """Test the secure file deletion functionality."""
    
    @pytest.fixture
    def temp_doc_path(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_normal_file_deletion(self, temp_doc_path):
        """Test that normal file deletion works correctly."""
        # Create a test file
        test_file = os.path.join(temp_doc_path, "test.txt")
        os.makedirs(temp_doc_path, exist_ok=True)
        with open(test_file, "w") as f:
            f.write("test content")
        
        result = await handle_file_deletion("test.txt", temp_doc_path)
        
        assert isinstance(result, JSONResponse)
        assert not os.path.exists(test_file)
    
    @pytest.mark.asyncio
    async def test_malicious_filename_deletion(self, temp_doc_path):
        """Test that malicious filenames are rejected for deletion."""
        result = await handle_file_deletion("../../../etc/passwd", temp_doc_path)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400
    
    @pytest.mark.asyncio
    async def test_nonexistent_file_deletion(self, temp_doc_path):
        """Test deletion of non-existent files."""
        result = await handle_file_deletion("nonexistent.txt", temp_doc_path)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 404
    
    @pytest.mark.asyncio
    async def test_directory_deletion_blocked(self, temp_doc_path):
        """Test that directory deletion is blocked."""
        # Create a subdirectory
        subdir = os.path.join(temp_doc_path, "subdir")
        os.makedirs(subdir, exist_ok=True)
        
        result = await handle_file_deletion("subdir", temp_doc_path)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400
        assert "not a file" in str(result.body.decode())


class TestSecurityIntegration:
    """Integration tests for the complete security fix."""
    
    def test_attack_vectors_blocked(self):
        """Test that common attack vectors are blocked."""
        attack_vectors = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\SAM",
            "test\x00.txt",
            "CON.txt",
            "PRN",
            "C:sensitive.txt",
            "....//....//sensitive",
            "\u202e\u202dmalicious.txt"  # Unicode RLO attack
        ]
        
        for attack in attack_vectors:
            try:
                result = secure_filename(attack)
                # If it doesn't raise an exception, ensure it's safe
                assert ".." not in result
                assert "/" not in result
                assert "\\" not in result
                assert "\x00" not in result
                assert not result.startswith(".")
            except ValueError:
                # This is expected for malicious inputs
                pass
    
    def test_legitimate_files_allowed(self):
        """Test that legitimate files are still allowed."""
        legitimate_files = [
            "document.pdf",
            "report_2024.docx",
            "data.csv",
            "image.jpg",
            "script.py",
            "config.json",
            "README.md",
            "file-with-dashes.txt",
            "file_with_underscores.txt"
        ]
        
        for filename in legitimate_files:
            result = secure_filename(filename)
            assert result == filename  # Should pass through unchanged


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"]) 