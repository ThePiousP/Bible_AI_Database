#!/usr/bin/env python3
"""
Bible AI Database & NER Pipeline
Setup configuration for package distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        for line in f:
            # Remove inline comments
            line = line.split('#')[0].strip()
            # Skip empty lines
            if not line:
                continue
            requirements.append(line)

# Development requirements
dev_requirements_file = Path(__file__).parent / 'requirements-test.txt'
dev_requirements = []
if dev_requirements_file.exists():
    with open(dev_requirements_file, 'r') as f:
        for line in f:
            # Remove inline comments
            line = line.split('#')[0].strip()
            # Skip empty lines
            if not line:
                continue
            # Skip pip-specific directives (like -r requirements.txt)
            if line.startswith('-'):
                continue
            dev_requirements.append(line)

# AI training requirements
ai_requirements = [
    'sentence-transformers>=2.2.0',
    'numpy>=1.24.0',
    'tqdm>=4.66.0',
]

setup(
    name='bible-ai-database',
    version='1.0.0',
    author='ThePiousP',
    author_email='',
    description='Complete Bible NLP pipeline with NER, embeddings, and RAG',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ThePiousP/Bible_AI_Database',
    project_urls={
        'Bug Tracker': 'https://github.com/ThePiousP/Bible_AI_Database/issues',
        'Documentation': 'https://github.com/ThePiousP/Bible_AI_Database/blob/master/README.md',
        'Source Code': 'https://github.com/ThePiousP/Bible_AI_Database',
    },

    # Package discovery
    packages=find_packages(exclude=['tests', 'tests.*', '.archived', 'Folders']),

    # Python version requirement
    python_requires='>=3.8',

    # Dependencies
    install_requires=requirements,

    # Optional dependencies
    extras_require={
        'dev': dev_requirements if dev_requirements else [],
        'ai': ai_requirements if ai_requirements else [],
        'all': (dev_requirements if dev_requirements else []) + (ai_requirements if ai_requirements else []),
    },

    # Entry points for CLI commands
    entry_points={
        'console_scripts': [
            'bible-menu=code.menu_master:main',
            'bible-scraper=code.bible_scraper:main',
            'bible-silver-export=code.silver_export:main',
            'bible-train-ner=code.train_baseline_spacy:main',
            'bible-embeddings=code.ai_training.create_embeddings:main',
            'bible-rag=code.ai_training.rag_system:main',
            'bible-chat=code.ai_training.chat_interface:main',
        ],
    },

    # Package data
    package_data={
        'bible_ai_database': [
            'config.yaml',
            'label_rules.yml',
            'gazetteers/*.txt',
        ],
    },

    # Include package data
    include_package_data=True,

    # Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],

    # Keywords
    keywords='bible nlp ner entity-recognition embeddings rag ai machine-learning',

    # Zip safe
    zip_safe=False,
)
