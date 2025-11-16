#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_databases.py
Validates integrity of GoodBook.db and concordance.db databases

Usage:
    python validate_databases.py
    python validate_databases.py --db data/GoodBook.db --verbose
    python validate_databases.py --fix-minor-issues

Purpose:
    - Check schema integrity
    - Verify row counts and relationships
    - Validate foreign key constraints
    - Check for missing/corrupt data
    - Verify Strong's lexicon completeness
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationResult:
    check_name: str
    status: str  # 'PASS', 'WARN', 'FAIL'
    message: str
    details: Optional[str] = None
    count: Optional[int] = None


class DatabaseValidator:
    def __init__(self, db_path: str, verbose: bool = False):
        self.db_path = Path(db_path)
        self.verbose = verbose
        self.results: List[ValidationResult] = []

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def connect(self) -> sqlite3.Connection:
        """Create database connection with foreign key checks enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def add_result(self, check: str, status: str, message: str, details: str = None, count: int = None):
        """Add validation result"""
        self.results.append(ValidationResult(check, status, message, details, count))

        # Print immediately if verbose
        if self.verbose:
            icon = {'PASS': '✓', 'WARN': '⚠', 'FAIL': '✗'}.get(status, '?')
            print(f"  {icon} {check}: {message}")
            if details:
                print(f"      {details}")

    def check_file_integrity(self) -> bool:
        """Check database file is valid SQLite"""
        try:
            with self.connect() as conn:
                conn.execute("PRAGMA integrity_check").fetchone()
            self.add_result("File Integrity", "PASS", f"Database file is valid")
            return True
        except sqlite3.DatabaseError as e:
            self.add_result("File Integrity", "FAIL", f"Database is corrupt: {e}")
            return False

    def check_schema_version(self) -> Optional[int]:
        """Check if schema_version table exists"""
        try:
            with self.connect() as conn:
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
                )
                if cur.fetchone():
                    version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
                    self.add_result("Schema Version", "PASS", f"Schema version: {version}", count=version)
                    return version
                else:
                    self.add_result("Schema Version", "WARN",
                                    "No schema_version table found (recommend adding for migrations)")
                    return None
        except sqlite3.Error as e:
            self.add_result("Schema Version", "FAIL", f"Error checking schema: {e}")
            return None

    def check_table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        """Check if table exists"""
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        return cur.fetchone() is not None

    def get_row_count(self, conn: sqlite3.Connection, table: str) -> int:
        """Get row count for table"""
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except sqlite3.Error:
            return -1


class GoodBookValidator(DatabaseValidator):
    """Validator for GoodBook.db"""

    REQUIRED_TABLES = ['books', 'chapters', 'verses', 'complete_canon']
    OPTIONAL_TABLES = ['cross_references', 'verse_footnotes', 'lexical_words']

    def validate_all(self) -> bool:
        """Run all validations"""
        print(f"\n{'='*80}")
        print(f"Validating GoodBook.db: {self.db_path}")
        print(f"{'='*80}\n")

        if not self.check_file_integrity():
            return False

        self.check_schema_version()

        with self.connect() as conn:
            self.check_required_tables(conn)
            self.check_row_counts(conn)
            self.check_foreign_keys(conn)
            self.check_books_data(conn)
            self.check_cross_references(conn)
            self.check_indexes(conn)

        return self.print_summary()

    def check_required_tables(self, conn: sqlite3.Connection):
        """Verify all required tables exist"""
        missing = []
        for table in self.REQUIRED_TABLES:
            if not self.check_table_exists(conn, table):
                missing.append(table)

        if missing:
            self.add_result("Required Tables", "FAIL",
                            f"Missing tables: {', '.join(missing)}")
        else:
            self.add_result("Required Tables", "PASS",
                            f"All {len(self.REQUIRED_TABLES)} required tables present")

        # Check optional tables
        optional_present = [t for t in self.OPTIONAL_TABLES if self.check_table_exists(conn, t)]
        if optional_present:
            self.add_result("Optional Tables", "PASS",
                            f"Found {len(optional_present)}/{len(self.OPTIONAL_TABLES)} optional tables",
                            details=', '.join(optional_present))

    def check_row_counts(self, conn: sqlite3.Connection):
        """Check row counts are reasonable"""
        counts = {
            'books': self.get_row_count(conn, 'books'),
            'chapters': self.get_row_count(conn, 'chapters'),
            'verses': self.get_row_count(conn, 'verses'),
        }

        # Expected: 66 books, ~1189 chapters, ~31102 verses
        if counts['books'] != 66:
            self.add_result("Book Count", "WARN",
                            f"Expected 66 books, found {counts['books']}", count=counts['books'])
        else:
            self.add_result("Book Count", "PASS", f"66 canonical books present", count=66)

        if counts['chapters'] < 1180 or counts['chapters'] > 1200:
            self.add_result("Chapter Count", "WARN",
                            f"Chapter count unusual: {counts['chapters']} (expected ~1189)",
                            count=counts['chapters'])
        else:
            self.add_result("Chapter Count", "PASS",
                            f"Chapter count in expected range", count=counts['chapters'])

        if counts['verses'] < 30000 or counts['verses'] > 32000:
            self.add_result("Verse Count", "WARN",
                            f"Verse count unusual: {counts['verses']} (expected ~31102)",
                            count=counts['verses'])
        else:
            self.add_result("Verse Count", "PASS",
                            f"Verse count in expected range", count=counts['verses'])

    def check_foreign_keys(self, conn: sqlite3.Connection):
        """Check foreign key integrity"""
        try:
            # Check orphaned chapters (no matching book)
            orphaned_chapters = conn.execute("""
                SELECT COUNT(*) FROM chapters c
                LEFT JOIN books b ON c.book_id = b.id
                WHERE b.id IS NULL
            """).fetchone()[0]

            if orphaned_chapters > 0:
                self.add_result("Chapter FK", "FAIL",
                                f"Found {orphaned_chapters} chapters with invalid book_id",
                                count=orphaned_chapters)
            else:
                self.add_result("Chapter FK", "PASS", "All chapters link to valid books")

            # Check orphaned verses (no matching chapter)
            orphaned_verses = conn.execute("""
                SELECT COUNT(*) FROM verses v
                LEFT JOIN chapters c ON v.chapter_id = c.id
                WHERE c.id IS NULL
            """).fetchone()[0]

            if orphaned_verses > 0:
                self.add_result("Verse FK", "FAIL",
                                f"Found {orphaned_verses} verses with invalid chapter_id",
                                count=orphaned_verses)
            else:
                self.add_result("Verse FK", "PASS", "All verses link to valid chapters")

        except sqlite3.Error as e:
            self.add_result("Foreign Keys", "FAIL", f"Error checking foreign keys: {e}")

    def check_books_data(self, conn: sqlite3.Connection):
        """Check books table data quality"""
        try:
            # Check for duplicate book names
            duplicates = conn.execute("""
                SELECT book_name, COUNT(*) as cnt FROM books
                GROUP BY book_name HAVING cnt > 1
            """).fetchall()

            if duplicates:
                dup_names = ', '.join([r[0] for r in duplicates])
                self.add_result("Duplicate Books", "FAIL",
                                f"Found duplicate book names: {dup_names}",
                                count=len(duplicates))
            else:
                self.add_result("Duplicate Books", "PASS", "No duplicate book names")

            # Check for NULL book names
            null_books = conn.execute("""
                SELECT COUNT(*) FROM books WHERE book_name IS NULL OR book_name = ''
            """).fetchone()[0]

            if null_books > 0:
                self.add_result("NULL Book Names", "FAIL",
                                f"Found {null_books} books with NULL/empty names",
                                count=null_books)
            else:
                self.add_result("NULL Book Names", "PASS", "All books have valid names")

        except sqlite3.Error as e:
            self.add_result("Books Data", "FAIL", f"Error checking books: {e}")

    def check_cross_references(self, conn: sqlite3.Connection):
        """Check cross-references table if it exists"""
        if not self.check_table_exists(conn, 'cross_references'):
            return

        try:
            total_refs = self.get_row_count(conn, 'cross_references')

            if total_refs == 0:
                self.add_result("Cross References", "WARN",
                                "cross_references table exists but is empty")
            elif total_refs > 500000:
                self.add_result("Cross References", "WARN",
                                f"Unusually high cross-reference count: {total_refs:,}",
                                count=total_refs)
            else:
                self.add_result("Cross References", "PASS",
                                f"{total_refs:,} cross-references loaded", count=total_refs)

            # Check for invalid references
            invalid_refs = conn.execute("""
                SELECT COUNT(*) FROM cross_references cr
                WHERE NOT EXISTS (SELECT 1 FROM verses v WHERE v.id = cr.source_verse_id)
                   OR NOT EXISTS (SELECT 1 FROM verses v WHERE v.id = cr.related_verse_id)
            """).fetchone()[0]

            if invalid_refs > 0:
                self.add_result("Invalid Cross-Refs", "FAIL",
                                f"Found {invalid_refs} cross-refs pointing to non-existent verses",
                                count=invalid_refs)
            else:
                self.add_result("Invalid Cross-Refs", "PASS",
                                "All cross-references point to valid verses")

        except sqlite3.Error as e:
            self.add_result("Cross References", "FAIL", f"Error checking cross-refs: {e}")

    def check_indexes(self, conn: sqlite3.Connection):
        """Check if important indexes exist"""
        try:
            indexes = conn.execute("""
                SELECT name, tbl_name FROM sqlite_master WHERE type='index'
            """).fetchall()

            index_names = {r[0] for r in indexes}

            recommended = [
                'idx_books_book_name',
                'idx_chapters_book_id_chapter_number',
            ]

            missing = [idx for idx in recommended if idx not in index_names]

            if missing:
                self.add_result("Indexes", "WARN",
                                f"Missing recommended indexes: {', '.join(missing)}",
                                details="These indexes improve query performance")
            else:
                self.add_result("Indexes", "PASS",
                                f"All recommended indexes present ({len(index_names)} total)",
                                count=len(index_names))

        except sqlite3.Error as e:
            self.add_result("Indexes", "WARN", f"Could not check indexes: {e}")

    def print_summary(self) -> bool:
        """Print validation summary and return True if all passed"""
        passed = sum(1 for r in self.results if r.status == 'PASS')
        warned = sum(1 for r in self.results if r.status == 'WARN')
        failed = sum(1 for r in self.results if r.status == 'FAIL')

        print(f"\n{'='*80}")
        print(f"Validation Summary")
        print(f"{'='*80}\n")

        print(f"  ✓ Passed: {passed}")
        print(f"  ⚠ Warnings: {warned}")
        print(f"  ✗ Failed: {failed}")
        print(f"  Total Checks: {len(self.results)}")

        if failed > 0:
            print(f"\n❌ Validation FAILED - {failed} critical issue(s) found")
            print("\nFailed Checks:")
            for r in self.results:
                if r.status == 'FAIL':
                    print(f"  • {r.check_name}: {r.message}")
            return False
        elif warned > 0:
            print(f"\n⚠️  Validation passed with {warned} warning(s)")
            print("\nWarnings:")
            for r in self.results:
                if r.status == 'WARN':
                    print(f"  • {r.check_name}: {r.message}")
            return True
        else:
            print(f"\n✅ All validations PASSED")
            return True


class ConcordanceValidator(DatabaseValidator):
    """Validator for concordance.db"""

    REQUIRED_TABLES = ['books', 'chapters', 'verses', 'tokens']
    OPTIONAL_TABLES = ['strongs_lexicon', 'footnotes', 'entity_overrides']

    def validate_all(self) -> bool:
        """Run all validations"""
        print(f"\n{'='*80}")
        print(f"Validating concordance.db: {self.db_path}")
        print(f"{'='*80}\n")

        if not self.check_file_integrity():
            return False

        self.check_schema_version()

        with self.connect() as conn:
            self.check_required_tables(conn)
            self.check_row_counts(conn)
            self.check_tokens_data(conn)
            self.check_strongs_lexicon(conn)
            self.check_alignment_quality(conn)
            self.check_indexes(conn)

        return self.print_summary()

    def check_required_tables(self, conn: sqlite3.Connection):
        """Verify all required tables exist"""
        missing = []
        for table in self.REQUIRED_TABLES:
            if not self.check_table_exists(conn, table):
                missing.append(table)

        if missing:
            self.add_result("Required Tables", "FAIL",
                            f"Missing tables: {', '.join(missing)}")
        else:
            self.add_result("Required Tables", "PASS",
                            f"All {len(self.REQUIRED_TABLES)} required tables present")

    def check_row_counts(self, conn: sqlite3.Connection):
        """Check row counts"""
        counts = {
            'verses': self.get_row_count(conn, 'verses'),
            'tokens': self.get_row_count(conn, 'tokens'),
        }

        if counts['verses'] < 30000:
            self.add_result("Verse Count", "WARN",
                            f"Low verse count: {counts['verses']:,}", count=counts['verses'])
        else:
            self.add_result("Verse Count", "PASS",
                            f"{counts['verses']:,} verses loaded", count=counts['verses'])

        if counts['tokens'] < 400000:
            self.add_result("Token Count", "WARN",
                            f"Low token count: {counts['tokens']:,} (expected 400k-600k)",
                            count=counts['tokens'])
        else:
            self.add_result("Token Count", "PASS",
                            f"{counts['tokens']:,} tokens loaded", count=counts['tokens'])

    def check_tokens_data(self, conn: sqlite3.Connection):
        """Check token data quality"""
        try:
            # Check for NULL/empty token text
            empty_tokens = conn.execute("""
                SELECT COUNT(*) FROM tokens WHERE text IS NULL OR TRIM(text) = ''
            """).fetchone()[0]

            if empty_tokens > 0:
                self.add_result("Empty Tokens", "WARN",
                                f"Found {empty_tokens:,} tokens with NULL/empty text",
                                count=empty_tokens)
            else:
                self.add_result("Empty Tokens", "PASS", "All tokens have text")

            # Check for tokens with Strong's IDs
            tokens_with_strongs = conn.execute("""
                SELECT COUNT(*) FROM tokens WHERE strong_norm IS NOT NULL
            """).fetchone()[0]

            total_tokens = self.get_row_count(conn, 'tokens')
            pct_strongs = (tokens_with_strongs / total_tokens * 100) if total_tokens > 0 else 0

            if pct_strongs < 50:
                self.add_result("Strong's Coverage", "WARN",
                                f"Only {pct_strongs:.1f}% of tokens have Strong's IDs",
                                count=tokens_with_strongs)
            else:
                self.add_result("Strong's Coverage", "PASS",
                                f"{pct_strongs:.1f}% of tokens have Strong's IDs",
                                count=tokens_with_strongs)

        except sqlite3.Error as e:
            self.add_result("Token Data", "FAIL", f"Error checking tokens: {e}")

    def check_strongs_lexicon(self, conn: sqlite3.Connection):
        """Check Strong's lexicon completeness"""
        if not self.check_table_exists(conn, 'strongs_lexicon'):
            self.add_result("Strong's Lexicon", "WARN",
                            "strongs_lexicon table not found (recommend creating)")
            return

        try:
            total_entries = self.get_row_count(conn, 'strongs_lexicon')

            # Expected: ~5600 Hebrew (H1-H8674) + ~5500 Greek (G1-G5624) ≈ 11k entries
            if total_entries < 8000:
                self.add_result("Strong's Lexicon", "WARN",
                                f"Incomplete lexicon: {total_entries:,} entries (expected ~11k)",
                                count=total_entries)
            else:
                self.add_result("Strong's Lexicon", "PASS",
                                f"{total_entries:,} Strong's entries loaded", count=total_entries)

            # Check for entries with definitions
            entries_with_defs = conn.execute("""
                SELECT COUNT(*) FROM strongs_lexicon
                WHERE definition IS NOT NULL AND TRIM(definition) != ''
            """).fetchone()[0]

            pct_defs = (entries_with_defs / total_entries * 100) if total_entries > 0 else 0

            if pct_defs < 90:
                self.add_result("Lexicon Definitions", "WARN",
                                f"Only {pct_defs:.1f}% of entries have definitions",
                                count=entries_with_defs)
            else:
                self.add_result("Lexicon Definitions", "PASS",
                                f"{pct_defs:.1f}% of entries have definitions")

        except sqlite3.Error as e:
            self.add_result("Strong's Lexicon", "FAIL", f"Error checking lexicon: {e}")

    def check_alignment_quality(self, conn: sqlite3.Connection):
        """Check token-to-text alignment quality"""
        try:
            # Check if text_start/text_end columns exist
            cols = [r[1] for r in conn.execute("PRAGMA table_info(tokens)").fetchall()]

            if 'text_start' not in cols or 'text_end' not in cols:
                self.add_result("Alignment Columns", "WARN",
                                "text_start/text_end columns not found (old schema?)")
                return

            # Check for tokens with NULL offsets
            null_offsets = conn.execute("""
                SELECT COUNT(*) FROM tokens
                WHERE (text_start IS NULL OR text_end IS NULL)
                  AND text IS NOT NULL AND TRIM(text) != ''
            """).fetchone()[0]

            total_tokens = self.get_row_count(conn, 'tokens')
            pct_aligned = ((total_tokens - null_offsets) / total_tokens * 100) if total_tokens > 0 else 0

            if pct_aligned < 95:
                self.add_result("Alignment Quality", "WARN",
                                f"Only {pct_aligned:.1f}% of tokens have valid offsets",
                                details=f"{null_offsets:,} tokens missing offsets")
            else:
                self.add_result("Alignment Quality", "PASS",
                                f"{pct_aligned:.2f}% of tokens aligned successfully",
                                count=total_tokens - null_offsets)

        except sqlite3.Error as e:
            self.add_result("Alignment Quality", "WARN", f"Could not check alignment: {e}")

    def check_indexes(self, conn: sqlite3.Connection):
        """Check if important indexes exist"""
        try:
            indexes = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='index'
            """).fetchall()

            index_names = {r[0] for r in indexes}

            recommended = [
                'ix_tokens_verse',
                'ix_tokens_strong',
                'ix_tokens_verse_textspan',
            ]

            missing = [idx for idx in recommended if idx not in index_names]

            if missing:
                self.add_result("Indexes", "WARN",
                                f"Missing recommended indexes: {', '.join(missing)}",
                                details="Run REFACTORING_PLAN.md section 6 to add indexes")
            else:
                self.add_result("Indexes", "PASS",
                                f"All recommended indexes present", count=len(index_names))

        except sqlite3.Error as e:
            self.add_result("Indexes", "WARN", f"Could not check indexes: {e}")

    def print_summary(self) -> bool:
        """Print validation summary"""
        return GoodBookValidator.print_summary(self)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Validate Bible NER pipeline databases')
    parser.add_argument('--goodbook', type=str, default='data/GoodBook.db',
                        help='Path to GoodBook.db (default: data/GoodBook.db)')
    parser.add_argument('--concordance', type=str, default='data/concordance.db',
                        help='Path to concordance.db (default: data/concordance.db)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed validation output')
    parser.add_argument('--skip-goodbook', action='store_true',
                        help='Skip GoodBook.db validation')
    parser.add_argument('--skip-concordance', action='store_true',
                        help='Skip concordance.db validation')

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"Bible NER Pipeline - Database Validation")
    print(f"{'='*80}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    all_passed = True

    # Validate GoodBook.db
    if not args.skip_goodbook:
        if Path(args.goodbook).exists():
            validator = GoodBookValidator(args.goodbook, verbose=args.verbose)
            passed = validator.validate_all()
            all_passed = all_passed and passed
        else:
            print(f"\n⚠️  Skipping GoodBook.db - file not found: {args.goodbook}\n")

    # Validate concordance.db
    if not args.skip_concordance:
        if Path(args.concordance).exists():
            validator = ConcordanceValidator(args.concordance, verbose=args.verbose)
            passed = validator.validate_all()
            all_passed = all_passed and passed
        else:
            print(f"\n⚠️  Skipping concordance.db - file not found: {args.concordance}\n")

    # Final summary
    print(f"\n{'='*80}")
    if all_passed:
        print(f"✅ All database validations PASSED")
        print(f"\n✓ Databases are ready for refactoring")
        print(f"{'='*80}\n")
        return 0
    else:
        print(f"❌ Database validation FAILED")
        print(f"\n✗ Fix issues before proceeding with refactoring")
        print(f"{'='*80}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
