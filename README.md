# 🤖 AI Resume & Portfolio Builder

An **AI-powered Resume and Portfolio Generator** that helps students and job seekers create **ATS-optimized resumes** and **professional portfolio websites** effortlessly using **Natural Language Processing (NLP)** and **Generative AI**.

This project automates resume creation, analyzes job descriptions for ATS compatibility, improves resume quality using AI, and generates a modern HTML portfolio from resume data.

---

## 🚀 Features

### 📄 Resume Input Options
- Upload resume (PDF / DOCX)
- Build resume manually using a guided form

### 🎯 ATS Keyword Analysis
- Extracts keywords from resume and job description  
- Calculates ATS score  
- Displays matched and missing keywords  

### ⚡ AI-Powered Resume Optimization
- Rule-based keyword optimization  
- AI-based intelligent optimization using **Ollama (LLaMA models)**  
- Maintains factual accuracy (no hallucinated content)  

### 💡 AI Suggestions
- Resume improvement recommendations  
- AI-generated professional summary  
- Bullet point enhancement aligned with job descriptions  

### 🌐 Portfolio Generation
- Template-based HTML portfolio (fast & reliable)  
- AI-generated HTML portfolio with modern UI  
- Fully responsive, single-page portfolio  

### 📦 Export Options
- Download ATS-friendly 1-page resume as PDF  
- Download portfolio as HTML file  

---

## 🧠 Technologies Used

- **Frontend:** Streamlit  
- **Backend:** Python  
- **AI Models:** Ollama (LLaMA 3.x local models)  
- **NLP:** NLTK  
- **Document Processing:** PyPDF2, python-docx  
- **PDF Generation:** ReportLab  
- **Web Technologies:** HTML, CSS  

---

## 🏗️ System Architecture
```bash
User Input
    ↓
Resume / Job Description
    ↓
NLP Processing & Keyword Extraction
    ↓
ATS Score Analyzer
    ↓
AI Resume Optimization (Ollama)
    ↓
PDF Resume & HTML Portfolio Output
```
---

## 📊 Use Cases

- Students creating resumes for internships  
- Freshers applying for entry-level jobs  
- Professionals improving ATS compatibility  
- Portfolio generation for personal branding  

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/chittesh24/AI-Resume-Portfolio-Builder.git
cd AI-Resume-Portfolio-Builder
```
## 🛠️ Installation & Setup

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
3️⃣ Install & Run Ollama
```bash
ollama pull llama3.2:3b
ollama serve
```
4️⃣ Run the Application
```bash
streamlit run app.py
```
📂 Project Structure
```bash
├── app2.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── assets/                 # Images / icons (optional)
├── sample_resume/          # Sample resumes (optional)
└── README.md               # Project documentation
```
🔮 Future Enhancements
- Cover letter generation.
- LinkedIn profile optimization.
- Multi-language resume support.
- Cloud deployment (AWS / GCP).
- Recruiter dashboard & analytics.
- Resume version tracking.

📚 References
- Streamlit Documentation: https://docs.streamlit.io
- NLTK Documentation: https://www.nltk.org
- Ollama AI: https://ollama.ai
- ReportLab PDF Library: https://www.reportlab.com
- Research on Applicant Tracking Systems (ATS)

👨‍💻 Author
- **Chittesh S**
- 📧 **Email:** chittesh.work@gmail.com
- 🔗 **LinkedIn:** https://linkedin.com/in/chittesh-s
- 💻 **GitHub:** https://github.com/chittesh24
