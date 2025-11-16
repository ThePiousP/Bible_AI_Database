"""
Test suite for Bible NER Pipeline

Test Organization:
- test_alignment.py - Greedy alignment algorithm tests
- test_label_rules.py - Label matching and priority tests
- test_step_parser.py - XML and morphology parsing tests
- test_database.py - Database operation tests
- conftest.py - Shared fixtures and test data

Run tests:
    pytest                    # Run all tests
    pytest -v                 # Verbose output
    pytest -k alignment       # Run alignment tests only
    pytest -m unit            # Run unit tests only
    pytest --cov              # Run with coverage report
"""

__version__ = "1.0.0"
