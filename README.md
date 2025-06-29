# 🎓 Scorix MVP

A dynamic, AI-powered grading system that uses semantic analysis to automatically grade student answers with customizable rules and user authentication.

## ✨ Features

### 🔐 Authentication & Security
- **User registration and login** with secure password hashing
- **JWT-based session management** with configurable timeouts
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

### 📊 Grade Management
- **Customizable grade thresholds** (A, B, C, D, F)
- **Quick preset options** (Standard, Strict, Lenient)
- **Real-time preview** of threshold changes
- **Rule-based scoring** with sample answer bonuses

### 🎯 User Interface
- **Streamlit web interface** with responsive design
- **Intuitive navigation** with clear sections
- **Debug mode** for detailed grading analysis
- **Real-time feedback** and error handling

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

### 1. Create Account
- Register with username, email, and password
- Login to access your personal workspace

### 2. Create Questions
- Write question text and sample answer
- Add marking rules (auto-detected types):
  - `"mentions F = ma"` → Exact phrase
  - `"contains protons, electrons"` → Keyword matching
  - `"explains the relationship"` → Semantic understanding

### 3. Upload Student Answers
- Select a question
- Enter student name, roll number, and answer
- Submit for grading

### 4. Configure Grading
- Customize grade thresholds (A: 85%, B: 70%, etc.)
- Use presets or set custom values
- Preview changes before saving

### 5. Run Grading
- Execute semantic analysis on all answers
- View detailed results with matched/missed rules
- Enable debug mode for detailed analysis

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
│   ├── auth_service.py  # Authentication logic
│   └── grading_service.py # Grading orchestration
└── tests/               # Test files
```

## 🔧 Configuration

### Grading Parameters
- **Semantic weights**: Direct similarity vs concept overlap
- **Rule thresholds**: Matching sensitivity for each rule type
- **Scoring weights**: Rule-based vs sample answer influence

### Database Settings
- **MongoDB URI**: Connection string
- **Database name**: Default: "semantic_grader"
- **Collections**: users, questions, answers, grades, settings

### Security Settings
- **JWT Secret**: Session token encryption
- **Session Timeout**: Default: 1 hour
- **Password Requirements**: Min 6 characters

## 🧪 Testing

Run the test files to verify functionality:
```bash
python test_improved_grading.py
python test_final_grading.py
python test_hybrid_grading.py
```

## 🔍 Debug Mode

Enable debug mode in the "Run Grading" page to see:
- Extracted key phrases from rules
- Word-level matching details
- Semantic similarity scores
- Rule type auto-detection

## 🛡️ Security Features

- **Password hashing** with bcrypt
- **JWT token authentication**
- **User data isolation**
- **Input validation**
- **Error handling** without exposing sensitive data

## 📈 Production Considerations

### Security
- Change default JWT secret
- Use environment variables for sensitive data
- Enable HTTPS in production
- Implement rate limiting

### Performance
- Add database indexing
- Implement caching
- Use connection pooling
- Monitor resource usage

### Scalability
- Add load balancing
- Implement microservices
- Use cloud databases
- Add monitoring and logging

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

---

**Built with ❤️ using Streamlit, MongoDB, and AI-powered semantic analysis** 