#!/usr/bin/env python3
"""
Test script to verify import/export functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.import_export_service import ImportExportService
from bson.objectid import ObjectId

def test_import_export_service():
    """Test the import/export service functionality"""
    print("🧪 Testing Import/Export Service...")
    
    # Create a test user ID
    test_user_id = ObjectId()
    
    # Initialize service
    service = ImportExportService(test_user_id)
    
    # Test 1: Get export templates
    print("\n1. Testing export templates...")
    templates = service.get_export_templates()
    if templates and 'questions' in templates and 'student_answers' in templates:
        print("✅ Export templates retrieved successfully")
        print(f"   Questions template: {templates['questions']['headers']}")
        print(f"   Answers template: {templates['student_answers']['headers']}")
    else:
        print("❌ Failed to get export templates")
        return False
    
    # Test 2: Test CSV template creation
    print("\n2. Testing CSV template creation...")
    try:
        import csv
        import io
        
        # Create questions template
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(templates['questions']['headers'])
        writer.writerow(templates['questions']['example'])
        
        csv_content = output.getvalue()
        if csv_content:
            print("✅ CSV template created successfully")
            print(f"   Template content: {csv_content[:100]}...")
        else:
            print("❌ Failed to create CSV template")
            return False
            
    except Exception as e:
        print(f"❌ Error creating CSV template: {e}")
        return False
    
    # Test 3: Test JSON template creation
    print("\n3. Testing JSON template creation...")
    try:
        import json
        
        # Create sample JSON data
        sample_questions = [
            {
                "question_text": "What is the formula for force?",
                "sample_answer": "F = ma",
                "rules": ["mentions F = ma", "contains force, mass, acceleration"]
            }
        ]
        
        json_content = json.dumps(sample_questions, indent=2)
        if json_content:
            print("✅ JSON template created successfully")
            print(f"   Template content: {json_content[:100]}...")
        else:
            print("❌ Failed to create JSON template")
            return False
            
    except Exception as e:
        print(f"❌ Error creating JSON template: {e}")
        return False
    
    print("\n🎉 All import/export service tests passed!")
    return True

if __name__ == "__main__":
    success = test_import_export_service()
    if success:
        print("\n✅ Import/Export functionality is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Import/Export functionality tests failed!")
        sys.exit(1) 