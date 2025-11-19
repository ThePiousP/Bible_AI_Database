#!/usr/bin/env python3
"""
Integration Tests - End-to-End Workflows
Tests complete pipelines from database → NER → AI training
"""

import pytest
import sqlite3
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.config_unified import get_config, get_path


class TestDatabaseIntegration:
    """Test database connectivity and data integrity."""

    def test_database_exists(self):
        """Test that GoodBook.db exists and is accessible."""
        db_path = get_path('database', 'goodbook', 'path')
        assert db_path.exists(), f"Database not found at {db_path}"

    def test_database_schema(self):
        """Test database has expected tables."""
        db_path = get_path('database', 'goodbook', 'path')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        # Required tables
        required_tables = {
            'books', 'chapters', 'verses',
            'lexical_words', 'morphology',
            'cross_references'
        }

        for table in required_tables:
            assert table in tables, f"Required table '{table}' not found"

        conn.close()

    def test_verse_count(self):
        """Test database has expected number of verses."""
        db_path = get_path('database', 'goodbook', 'path')
        config = get_config()
        expected_verses = config.get('database', 'goodbook', 'expected_verses')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM verses")
        actual_count = cursor.fetchone()[0]
        conn.close()

        assert actual_count == expected_verses, \
            f"Expected {expected_verses} verses, found {actual_count}"

    def test_book_count(self):
        """Test database has expected number of books."""
        db_path = get_path('database', 'goodbook', 'path')
        config = get_config()
        expected_books = config.get('database', 'goodbook', 'expected_books')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        actual_count = cursor.fetchone()[0]
        conn.close()

        assert actual_count == expected_books, \
            f"Expected {expected_books} books, found {actual_count}"

    def test_verse_data_integrity(self):
        """Test verses have valid data."""
        db_path = get_path('database', 'goodbook', 'path')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check for verses with missing text
        cursor.execute("SELECT COUNT(*) FROM verses WHERE text IS NULL OR text = ''")
        empty_verses = cursor.fetchone()[0]

        assert empty_verses == 0, f"Found {empty_verses} verses with empty text"

        conn.close()


class TestConfigIntegration:
    """Test configuration system integration."""

    def test_config_loads(self):
        """Test unified config loads successfully."""
        config = get_config()
        assert config is not None
        assert config.get('project', 'name') is not None

    def test_required_paths_exist(self):
        """Test all required paths from config exist or can be created."""
        config = get_config()

        # These should exist
        db_path = config.get_database_path()
        assert db_path.exists(), f"Database path doesn't exist: {db_path}"

        # These directories should be creatable
        required_dirs = [
            config.get_path('paths', 'output_dir'),
            config.get_path('paths', 'log_dir'),
            config.get_path('paths', 'cache_dir'),
        ]

        for dir_path in required_dirs:
            if dir_path and not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
            assert dir_path.exists(), f"Cannot create directory: {dir_path}"

    def test_profile_loading(self):
        """Test configuration profiles load correctly."""
        profiles = ['default', 'gospels_holdout', 'ot_only']

        for profile_name in profiles:
            config = get_config(profile=profile_name, reload=True)
            assert config is not None
            assert config.profile == profile_name


class TestGazetteerIntegration:
    """Test gazetteer files and entity data."""

    def test_gazetteers_directory_exists(self):
        """Test gazetteers directory exists."""
        gaz_dir = get_path('paths', 'gazetteers_dir')
        assert gaz_dir.exists(), f"Gazetteers directory not found: {gaz_dir}"

    def test_gazetteer_files_exist(self):
        """Test key gazetteer files exist."""
        gaz_dir = get_path('paths', 'gazetteers_dir')

        # Key entity types
        required_gazetteers = [
            'DEITY.txt',
            'PERSON.txt',
            'LOCATION.txt',
            'DIVINE_TITLE.txt',
        ]

        for gaz_file in required_gazetteers:
            gaz_path = gaz_dir / gaz_file
            assert gaz_path.exists(), f"Missing gazetteer: {gaz_file}"

    def test_gazetteer_format(self):
        """Test gazetteers have valid format (one entry per line)."""
        gaz_dir = get_path('paths', 'gazetteers_dir')
        deity_gaz = gaz_dir / 'DEITY.txt'

        if deity_gaz.exists():
            with open(deity_gaz, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Should have at least some entries
            assert len(lines) > 0, "DEITY gazetteer is empty"

            # Lines should not be excessively long (reasonable entity names)
            for i, line in enumerate(lines[:10]):  # Check first 10
                assert len(line.strip()) < 200, \
                    f"Line {i+1} is unusually long: {len(line)} chars"


class TestCacheIntegration:
    """Test STEP Bible cache integration."""

    def test_cache_directory_exists(self):
        """Test cache directory exists."""
        cache_dir = get_path('paths', 'cache_dir')
        assert cache_dir.exists(), f"Cache directory not found: {cache_dir}"

    def test_step_cache_files_exist(self):
        """Test STEP Bible cache files exist."""
        cache_dir = get_path('paths', 'cache_dir')

        # Should have book directories
        book_dirs = list(cache_dir.glob('*/'))
        assert len(book_dirs) > 0, "No cached book directories found"

        # Should have JSON files
        json_files = list(cache_dir.glob('*/*.json'))
        assert len(json_files) > 0, "No cached JSON files found"


class TestPipelineIntegration:
    """Test complete pipeline workflows."""

    def test_database_to_verse_retrieval(self):
        """Test retrieving verses from database."""
        db_path = get_path('database', 'goodbook', 'path')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Retrieve Genesis 1:1
        cursor.execute("""
            SELECT v.text, b.book_name, c.chapter_number, v.verse_number
            FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE b.book_name = 'Genesis'
            AND c.chapter_number = 1
            AND v.verse_number = 1
        """)

        result = cursor.fetchone()
        conn.close()

        assert result is not None, "Genesis 1:1 not found"
        assert 'beginning' in result[0].lower(), \
            "Genesis 1:1 doesn't contain expected text"

    def test_config_to_database_path(self):
        """Test workflow: config → database path → connection."""
        # Load config
        config = get_config()

        # Get database path
        db_path = config.get_database_path()
        assert db_path.exists()

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM verses")
        count = cursor.fetchone()[0]
        conn.close()

        assert count > 30000, "Database has too few verses"


class TestAITrainingPrerequisites:
    """Test prerequisites for AI training pipeline."""

    def test_embeddings_can_be_created(self):
        """Test embeddings creation prerequisites."""
        # Check database exists
        db_path = get_path('database', 'goodbook', 'path')
        assert db_path.exists()

        # Check AI training config exists
        config = get_config()
        ai_config = config.get_ai_training_config()
        assert ai_config is not None
        assert 'embeddings' in ai_config

    def test_rag_prerequisites(self):
        """Test RAG system prerequisites."""
        config = get_config()
        ai_config = config.get_ai_training_config()

        assert 'rag' in ai_config
        assert ai_config['rag']['top_k'] > 0


@pytest.mark.slow
class TestEndToEndWorkflow:
    """
    End-to-end integration tests (marked as slow).
    Run with: pytest -v -m slow
    """

    def test_complete_verse_retrieval_workflow(self):
        """Test complete workflow from config to verse retrieval."""
        # 1. Load config
        config = get_config()

        # 2. Get database path
        db_path = config.get_database_path()

        # 3. Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 4. Retrieve all books
        cursor.execute("SELECT book_name FROM books ORDER BY id")
        books = [row[0] for row in cursor.fetchall()]

        # 5. Verify expected books
        assert 'Genesis' in books
        assert 'Revelation' in books
        assert len(books) == 66

        # 6. Get sample verses from each testament
        cursor.execute("""
            SELECT v.text FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE b.book_name = 'Genesis' LIMIT 1
        """)
        ot_verse = cursor.fetchone()[0]

        cursor.execute("""
            SELECT v.text FROM verses v
            JOIN chapters c ON v.chapter_id = c.id
            JOIN books b ON c.book_id = b.id
            WHERE b.book_name = 'John' LIMIT 1
        """)
        nt_verse = cursor.fetchone()[0]

        conn.close()

        # 7. Verify verses have content
        assert len(ot_verse) > 0
        assert len(nt_verse) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v'])
