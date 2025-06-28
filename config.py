import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "semantic_grader"

# Security Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Grading Configuration
GRADING_CONFIG = {
    # Scoring weights
    "semantic_weights": {
        "direct_similarity": 0.7,
        "concept_overlap": 0.3
    },
    
    # Rule matching thresholds
    "rule_thresholds": {
        "semantic": 0.2,
        "keyword_overlap": 0.8,
        "keyword_required_percentage": 0.8,
        "min_keyword_matches": 3
    },
    
    # Final scoring weights
    "final_scoring": {
        "rule_based_weight": 1.0,
        "sample_bonus_weight": 0.2,
        "sample_bonus_threshold": 0.5
    },
    
    # Default grade thresholds
    "default_grade_thresholds": {
        "A": 85,
        "B": 70,
        "C": 55,
        "D": 40,
        "F": 0
    }
}

# Rule Type Detection Patterns
RULE_DETECTION_PATTERNS = {
    "exact_phrase": [
        "formula", "equation", "mentions", "exact", "precise"
    ],
    "contains_keywords": [
        "contains", "has", "includes", "keywords", "terms", "specific"
    ],
    "semantic": [
        "explains", "describes", "shows", "demonstrates", "understands", "concept"
    ]
}

# Text Processing Configuration
TEXT_PROCESSING = {
    # Stop words to filter out
    "stop_words": {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    },
    
    # Function words to filter out
    "function_words": {
        'mentions', 'mention', 'contains', 'contain', 'includes', 'include', 'has', 'have',
        'shows', 'show', 'demonstrates', 'demonstrate', 'explains', 'explain', 'describes', 'describe',
        'student', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    },
    
    # Minimum word length for processing
    "min_word_length": 3
}

# Preset Grade Thresholds
GRADE_PRESETS = {
    "standard": {"A": 85, "B": 70, "C": 55, "D": 40, "F": 0},
    "strict": {"A": 90, "B": 80, "C": 70, "D": 60, "F": 0},
    "lenient": {"A": 80, "B": 65, "C": 50, "D": 35, "F": 0}
}
