# 🎓 Scorix MVP

A dynamic, AI-powered grading system that uses semantic analysis to automatically grade student answers with customizable rules, user authentication, and persistent session management.

## ✨ Features

### 🔐 Authentication & Security
- **User registration and login** with secure password hashing
- **JWT-based session management** with configurable timeouts
- **Persistent sessions** that survive page reloads and browser navigation
- **Multi-layer session validation** (Session State + Query Parameters + MongoDB)
- **User-specific data isolation** - each user can only access their own data
- **Input validation and sanitization**

### 🧠 Dynamic Grading System
- **Hybrid matching algorithms**:
  - 🔍 **Exact Phrase**: Matches specific formulas, terms, or mentions
  - 🔑 **Keyword Matching**: Identifies important concepts with lemmatization
  - 🧠 **Semantic**: Uses AI embeddings for conceptual understanding
- **Auto-detection of rule types** based on natural language
- **Content-agnostic** - works with any subject or domain
- **Configurable grading thresholds** per user

### 📋 Test Management
- **Create comprehensive tests** with multiple questions
- **Upload test answers** via CSV or manual entry
- **Batch grading** for entire tests
- **Test statistics** and grade distribution analysis
- **Export/Import functionality** for data management

### 📊 Grade Management
- **Customizable grade thresholds** (A, B, C, D, F)
- **Quick preset options** (Standard, Strict, Lenient)
- **Real-time preview** of threshold changes
- **Rule-based scoring** with sample answer bonuses
- **Test-specific grading** with overall scores

### 🎯 User Interface
- **Streamlit web interface** with responsive design
- **Intuitive navigation** with clear sections
- **Debug mode** for detailed grading analysis
- **Real-time feedback** and error handling
- **Session status indicators** showing persistence and expiry

### 📤 Data Management
- **CSV import/export** for bulk operations
- **Template downloads** for easy data entry
- **Bulk operations** for data cleanup
- **Test answer management** with structured uploads

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (local or cloud)
- Internet connection (for AI model download)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd semantic_grader_mvp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MongoDB**
   - Install MongoDB locally or use MongoDB Atlas
   - Update `config.py` with your MongoDB URI if needed

5. **Configure environment** (optional)
   ```bash
   # Create .env file for production
   echo "JWT_SECRET=your-super-secret-key-here" > .env
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 📖 Usage

### 1. Create Account & Login
- Register with username, email, and password
- Login to access your personal workspace
- **Sessions persist** across page reloads and browser navigation
- **Session status** is displayed in the UI

### 2. Create Questions
- Write question text and sample answer
- Add marking rules (auto-detected types):
  - `"mentions F = ma"` → Exact phrase
  - `"contains protons, electrons"` → Keyword matching
  - `"explains the relationship"` → Semantic understanding

### 3. Test Management
- **Create Tests**: Combine multiple questions into comprehensive tests
- **Upload Test Answers**: Use CSV templates or manual entry
- **Grade Tests**: Batch process all test submissions
- **View Results**: See detailed statistics and grade distributions

### 4. Upload Student Answers
- Select a question
- Enter student name, roll number, and answer
- Submit for grading
- **CSV Import**: Bulk upload multiple answers

### 5. Configure Grading
- Customize grade thresholds (A: 85%, B: 70%, etc.)
- Use presets or set custom values
- Preview changes before saving

### 6. Run Grading
- Execute semantic analysis on all answers
- View detailed results with matched/missed rules
- Enable debug mode for detailed analysis
- **Test Grading**: Process entire tests with overall scores

### 7. Data Management
- **Export Data**: Download all data as CSV ZIP
- **Import Answers**: Bulk upload student responses
- **Templates**: Download CSV templates for easy data entry
- **Bulk Operations**: Clear data when needed

## 🏗️ Architecture

```
semantic_grader_mvp/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration and settings
├── requirements.txt      # Python dependencies
├── core/
│   ├── db.py            # Database operations
│   └── grader.py        # Grading algorithms
├── services/
│   ├── auth_service.py  # Authentication & session management
│   ├── grading_service.py # Grading orchestration
│   ├── test_grading_service.py # Test-specific grading
│   └── import_export_service.py # Data import/export
└── tests/               # Test files
```

## 🔧 Configuration

### Session Management
- **Session Timeout**: Default: 24 hours (configurable)
- **Refresh Window**: 10 minutes before expiry
- **MongoDB Cleanup**: 30 days for old sessions
- **Persistence Layers**: Session State + Query Parameters + MongoDB

### Grading Parameters
- **Semantic weights**: Direct similarity vs concept overlap
- **Rule thresholds**: Matching sensitivity for each rule type
- **Scoring weights**: Rule-based vs sample answer influence

### Database Settings
- **MongoDB URI**: Connection string
- **Database name**: Default: "semantic_grader"
- **Collections**: users, questions, answers, grades, settings, sessions, tests, test_answers, test_grades

### Security Settings
- **JWT Secret**: Session token encryption
- **Session Timeout**: Default: 24 hours
- **Password Requirements**: Min 6 characters

## 🧪 Testing

Run the test files to verify functionality:
```bash
python test_improved_grading.py
python test_final_grading.py
python test_hybrid_grading.py
python test_grading_service.py
python test_import_export.py
```

## 🔍 Debug Mode

### Session Debugging
Enable debug mode in `app.py`:
```python
DEBUG_SESSION = True  # Set to True in main() function
```

### Grading Debugging
Enable debug mode in the "Run Grading" page to see:
- Extracted key phrases from rules
- Word-level matching details
- Semantic similarity scores
- Rule type auto-detection

## 🛡️ Security Features

- **Password hashing** with bcrypt
- **JWT token authentication**
- **Multi-layer session validation**
- **Persistent session management**
- **User data isolation**
- **Input validation**
- **Error handling** without exposing sensitive data

## 📈 Production Considerations

### Security
- Change default JWT secret
- Use environment variables for sensitive data
- Enable HTTPS in production
- Implement rate limiting
- Monitor session activity

### Performance
- Add database indexing
- Implement caching
- Use connection pooling
- Monitor resource usage
- Optimize session queries

### Scalability
- Add load balancing
- Implement microservices
- Use cloud databases
- Add monitoring and logging
- Session distribution across servers

## 🔄 Session Management Flow

### Login Process
1. **User Authentication** → Credential validation
2. **Token Creation** → JWT token generation
3. **Multi-Storage** → Session State + Query Parameters + MongoDB
4. **Session Persistence** → Survives page reloads

### Session Restoration
1. **Token Retrieval** → Session State → Query Parameters (fallback)
2. **MongoDB Validation** → Server-side session verification
3. **User Data Recovery** → Restore user information
4. **Session Update** → Refresh activity timestamps

### Session Validation
1. **Token Check** → Validate existence and expiration
2. **MongoDB Verification** → Confirm server-side session
3. **Auto Refresh** → Extend session if needed
4. **Cleanup** → Remove expired sessions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the debug mode for detailed analysis
2. Review the test files for examples
3. Check MongoDB connection and data
4. Verify all dependencies are installed
5. Enable session debugging for authentication issues

---

**Built with ❤️ using Streamlit, MongoDB, and AI-powered semantic analysis** 