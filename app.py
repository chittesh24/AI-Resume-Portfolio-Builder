import streamlit as st
import PyPDF2
import docx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
from collections import Counter
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import base64
import requests
import json

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

# Initialize session state
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'ats_score' not in st.session_state:
    st.session_state.ats_score = None
if 'matched_keywords' not in st.session_state:
    st.session_state.matched_keywords = []
if 'missing_keywords' not in st.session_state:
    st.session_state.missing_keywords = []
if 'optimized_resume' not in st.session_state:
    st.session_state.optimized_resume = ""
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        'name': '',
        'email': '',
        'phone': '',
        'linkedin': '',
        'github': '',
        'portfolio_url': '',
        'summary': '',
        'experience': [{'title': '', 'company': '', 'duration': '', 'description': ''}],
        'projects': [{'name': '', 'description': '', 'technologies': '', 'link': ''}],
        'education': '',
        'skills': '',
        'certificates': [{'name': '', 'link': ''}]
    }
if 'ollama_available' not in st.session_state:
    st.session_state.ollama_available = None
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = ""

# Skill categorization database
SKILL_CATEGORIES = {
    'Programming Languages': [
        'python', 'java', 'javascript', 'c', 'c++', 'c#', 'ruby', 'php', 'swift', 
        'kotlin', 'go', 'rust', 'typescript', 'r', 'matlab', 'scala', 'perl', 
        'dart', 'objective-c', 'shell', 'bash', 'powershell', 'sql', 'html', 'css'
    ],
    'Web Frameworks': [
        'react', 'angular', 'vue', 'svelte', 'django', 'flask', 'fastapi', 'spring', 
        'spring boot', 'express', 'nodejs', 'node.js', 'laravel', 'rails', 'asp.net', 
        'nextjs', 'next.js', 'nuxt', 'gatsby', 'ember'
    ],
    'Mobile Development': [
        'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic', 'cordova', 
        'swift', 'kotlin', 'java'
    ],
    'Cloud Platforms': [
        'aws', 'azure', 'gcp', 'google cloud', 'alibaba cloud', 'oracle cloud', 
        'heroku', 'digitalocean', 'linode', 'ibm cloud'
    ],
    'Cloud Services': [
        'ec2', 's3', 'lambda', 'rds', 'dynamodb', 'cloudformation', 'cloudfront', 
        'elastic beanstalk', 'ecs', 'eks', 'azure functions', 'azure devops', 
        'cloud functions', 'cloud run', 'compute engine', 'app engine'
    ],
    'DevOps & CI/CD': [
        'docker', 'kubernetes', 'jenkins', 'gitlab', 'github actions', 'circleci', 
        'travis', 'ansible', 'terraform', 'vagrant', 'puppet', 'chef', 'bamboo', 
        'teamcity', 'spinnaker', 'argocd'
    ],
    'Databases': [
        'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'oracle', 'mssql', 
        'sqlite', 'mariadb', 'dynamodb', 'elasticsearch', 'neo4j', 'couchdb', 
        'firebase', 'realm', 'cockroachdb'
    ],
    'Data Science & ML': [
        'machine learning', 'deep learning', 'artificial intelligence', 'ai', 'ml', 
        'data science', 'data analysis', 'statistics', 'nlp', 'computer vision', 
        'neural networks', 'cnn', 'rnn', 'lstm', 'transformers', 'gpt', 'bert'
    ],
    'ML Frameworks': [
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'xgboost', 
        'lightgbm', 'catboost', 'fastai', 'mxnet', 'caffe', 'theano', 'paddlepaddle'
    ],
    'Data Tools': [
        'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 'scipy', 'statsmodels', 
        'dask', 'pyspark', 'spark', 'hadoop', 'hive', 'pig', 'tableau', 'power bi', 
        'looker', 'qlik', 'jupyter', 'google colab', 'kaggle'
    ],
    'API & Integration': [
        'rest', 'restful', 'graphql', 'soap', 'grpc', 'websocket', 'api', 'microservices', 
        'api gateway', 'postman', 'swagger', 'openapi'
    ],
    'Testing': [
        'unit testing', 'integration testing', 'selenium', 'junit', 'pytest', 'jest', 
        'mocha', 'chai', 'cucumber', 'testng', 'cypress', 'puppeteer', 'karma', 'jasmine'
    ],
    'Version Control': [
        'git', 'github', 'gitlab', 'bitbucket', 'svn', 'mercurial', 'perforce'
    ],
    'Design & UI/UX': [
        'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator', 'ui', 'ux', 
        'user experience', 'user interface', 'wireframing', 'prototyping'
    ],
    'Methodologies': [
        'agile', 'scrum', 'kanban', 'devops', 'waterfall', 'lean', 'tdd', 'bdd', 
        'ci/cd', 'continuous integration', 'continuous deployment'
    ],
    'Security': [
        'cybersecurity', 'penetration testing', 'security', 'encryption', 'oauth', 
        'jwt', 'ssl', 'tls', 'https', 'authentication', 'authorization', 'firewall'
    ],
    'Big Data': [
        'hadoop', 'spark', 'kafka', 'storm', 'flink', 'hive', 'pig', 'hbase', 
        'mapreduce', 'yarn', 'zookeeper', 'airflow'
    ],
    'Blockchain': [
        'blockchain', 'ethereum', 'solidity', 'web3', 'smart contracts', 'nft', 
        'defi', 'cryptocurrency', 'bitcoin', 'hyperledger'
    ],
    'Other Tools': [
        'linux', 'unix', 'windows', 'macos', 'vim', 'vscode', 'visual studio', 
        'intellij', 'eclipse', 'pycharm', 'sublime', 'atom', 'nginx', 'apache', 
        'tomcat', 'jira', 'confluence', 'slack', 'teams', 'zoom', 'notion'
    ],
    'Finance & Accounting': [
        'finance', 'accounting', 'financial accounting', 'management accounting',
        'bookkeeping', 'auditing', 'financial statements', 'balance sheet',
        'income statement', 'cash flow', 'gaap', 'ifrs', 'cost accounting',
        'budgeting', 'forecasting'
    ],
    'Financial Analysis & Modeling': [
        'financial analysis', 'financial modeling', 'valuation',
        'discounted cash flow', 'dcf', 'npv', 'irr', 'ratio analysis',
        'scenario analysis', 'sensitivity analysis', 'forecast modeling',
        'excel modeling', 'powerpoint'
    ],
    'Banking & Investment': [
        'investment banking', 'commercial banking', 'retail banking',
        'corporate finance', 'wealth management', 'asset management',
        'portfolio management', 'equity research', 'fixed income',
        'derivatives', 'mutual funds', 'hedge funds', 'private equity',
        'venture capital'
    ],
    'Trading & Markets': [
        'trading', 'stock market', 'equities', 'bonds', 'commodities',
        'forex', 'fx', 'options', 'futures', 'technical analysis',
        'fundamental analysis', 'algo trading', 'high frequency trading'
    ],
    'Risk & Compliance': [
        'risk management', 'credit risk', 'market risk', 'operational risk',
        'liquidity risk', 'compliance', 'aml', 'kyc', 'sox',
        'internal controls', 'regulatory reporting', 'basel'
    ],
    'FinTech & Financial Systems': [
        'fintech', 'payments', 'digital payments', 'payment gateways',
        'blockchain finance', 'crypto trading', 'robo advisory',
        'open banking', 'financial APIs', 'core banking systems',
        'sap fico', 'oracle financials', 'netsuite'
    ],
    'Financial Tools & Software': [
        'excel', 'advanced excel', 'vba', 'power bi', 'tableau',
        'quickbooks', 'tally', 'sap', 'sap fico', 'oracle erp',
        'bloomberg', 'reuters', 'factset', 'morningstar'
    ]

}

# Ollama Integration Functions
def check_ollama_availability():
    """Check if Ollama is running and available"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return True, [model['name'] for model in models]
        return False, []
    except:
        return False, []

def warmup_ollama(model="llama3.2:3b"):
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": "Say ready.",
                "stream": False
            },
            timeout=30
        )
    except:
        pass

if st.session_state.ollama_available and not st.session_state.get("ollama_warmed"):
    warmup_ollama(model="llama3.2:3b")
    st.session_state.ollama_warmed = True


def call_ollama(prompt, model="llama3.2:3b", temperature=0.4):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=180
        )
        if response.status_code == 200:
            return response.json().get("response", "")
        return None
    except Exception as e:
        st.error(f"Ollama API Error: {e}")
        return None


def ai_optimize_resume(resume_text, missing_keywords, model="llama3.2:3b"):
    """Use Ollama AI to intelligently optimize resume"""
    
    prompt = f"""You are a professional resume optimization expert. Your task is to enhance a resume by naturally incorporating missing keywords.

IMPORTANT RULES:
1. DO NOT invent or fabricate any experience, projects, or achievements
2. ONLY add the missing keywords to existing content where they naturally fit
3. Add keywords to the SKILLS section in a categorized format
4. If keywords can be naturally added to existing bullet points, do so
5. Keep the original structure and content intact
6. DO NOT remove any existing content
7. DO NOT add any job description content
8. Return ONLY the optimized resume text, no explanations
9. Keep the resume concise for 1-page format
10. If the role is finance-related, prioritize finance & accounting keywords over technical ones


ORIGINAL RESUME:
{resume_text}

MISSING KEYWORDS TO INCORPORATE:
{', '.join(missing_keywords[:30])}

OUTPUT REQUIREMENTS:
- Add missing keywords in a categorized SKILLS section (e.g., "Programming Languages: Python, Java")
- If keywords fit naturally in existing descriptions, integrate them
- Maintain professional tone
- Keep all original content
- Return the complete optimized resume
- Keep it concise

OPTIMIZED RESUME:"""

    result = call_ollama(prompt, model=model, temperature=0.5)
    return result if result else None

def ai_improve_bullet_points(bullet_points, job_description, model="llama3.2:3b"):
    """Use AI to improve resume bullet points to better match job description"""
    
    prompt = f"""You are a professional resume writer. Improve the following resume bullet points to better align with the job description while keeping them truthful and achievement-focused.

RULES:
1. Keep the core facts intact - DO NOT invent achievements
2. Use strong action verbs
3. Quantify where possible (if numbers already exist)
4. Add relevant keywords from the job description naturally
5. Make them more impactful and results-oriented
6. Keep each bullet point concise (1-2 lines max)
7. Return ONLY the improved bullet points, one per line, starting with "•"

JOB DESCRIPTION:
{job_description[:500]}...

ORIGINAL BULLET POINTS:
{bullet_points}

IMPROVED BULLET POINTS:"""

    result = call_ollama(prompt, model=model, temperature=0.6)
    return result if result else None

def ai_generate_professional_summary(resume_text, job_description, model="llama3.2:3b"):
    """Generate AI-powered professional summary"""
    
    prompt = f"""You are a professional resume writer. Create a compelling professional summary (2-3 sentences, max 60 words) based on the resume content and job description.

RULES:
1. Base it ONLY on actual experience from the resume
2. Highlight key skills matching the job description
3. Make it achievement-focused
4. Keep it concise (40-60 words)
5. Use third-person perspective
6. Return ONLY the summary text

RESUME CONTENT:
{resume_text[:1000]}...

JOB DESCRIPTION:
{job_description[:500]}...

PROFESSIONAL SUMMARY:"""

    result = call_ollama(prompt, model=model, temperature=0.7)
    return result if result else None

def ai_suggest_improvements(resume_text, job_description, ats_score, model="llama3.2:3b"):
    """Get AI suggestions for resume improvement"""
    
    prompt = f"""You are a professional career coach and ATS expert. Analyze this resume against the job description and provide specific, actionable improvement suggestions.

CURRENT ATS SCORE: {ats_score}%

RESUME:
{resume_text[:1500]}...

JOB DESCRIPTION:
{job_description[:800]}...

Provide 5-7 specific suggestions to improve this resume. Format as:
1. [Suggestion]
2. [Suggestion]
...

Focus on:
- Missing keywords and skills
- Weak bullet points
- Missing quantifiable achievements
- Formatting issues
- Skills gaps

SUGGESTIONS:"""

    result = call_ollama(prompt, model=model, temperature=0.7)
    return result if result else None

# Helper functions
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting PDF: {str(e)}")
        return ""

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting DOCX: {str(e)}")
        return ""

def extract_keywords(text):
    if not text or text.strip() == "":
        return []

    text_lower = text.lower()

    # ---- 1. Extract multi-word skills FIRST (protected) ----
    multi_word_skills = set()
    for skills in SKILL_CATEGORIES.values():
        for skill in skills:
            if len(skill.split()) > 1 and skill in text_lower:
                multi_word_skills.add(skill)

    # ---- 2. Remove matched phrases from text ----
    clean_text = text_lower
    for phrase in multi_word_skills:
        clean_text = clean_text.replace(phrase, "")

    tokens = word_tokenize(clean_text)

    stop_words = set(stopwords.words('english'))

    technical_terms = {
        skill for skills in SKILL_CATEGORIES.values()
        for skill in skills if len(skill.split()) == 1
    }

    lemmatizer = WordNetLemmatizer()
    keywords = []

    for token in tokens:
        if token.isalpha() and len(token) > 2:
            if token in technical_terms or token not in stop_words:
                keywords.append(lemmatizer.lemmatize(token))

    return list(set(keywords).union(multi_word_skills))


def calculate_ats_score(resume_keywords, jd_keywords):
    if not jd_keywords:
        return 0, [], []
    
    resume_set = set([k.lower() for k in resume_keywords])
    jd_set = set([k.lower() for k in jd_keywords])
    
    # Exact matches
    matched = set()
    for jd_kw in jd_set:
        if jd_kw in resume_set:
            matched.add(jd_kw)
    
    # Partial matches for phrases (only if not already matched)
    partial_matched = set()
    for jd_kw in jd_set:
        if jd_kw not in matched:
            # Check if JD keyword is part of any resume keyword or vice versa
            for resume_kw in resume_set:
                if jd_kw in resume_kw or resume_kw in jd_kw:
                    # Ensure meaningful overlap (not just substrings like "a" in "java")
                    if len(jd_kw) > 2 and len(resume_kw) > 2:
                        if jd_kw in resume_kw or resume_kw in jd_kw:
                            partial_matched.add(jd_kw)
                            break
    
    all_matched = matched.union(partial_matched)
    missing = jd_set - all_matched
    
    # Calculate score
    score = (len(all_matched) / len(jd_set)) * 100 if jd_set else 0
    
    return round(score, 2), sorted(list(all_matched)), sorted(list(missing))

def categorize_skills(keywords):
    categorized = {}
    uncategorized = []
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        found = False
        
        for category, skills in SKILL_CATEGORIES.items():
            if keyword_lower in skills:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(keyword)
                found = True
                break
        
        if not found:
            uncategorized.append(keyword)
    
    return categorized, uncategorized

def optimize_resume_rule_based(resume_text, missing_keywords):
    if not missing_keywords or not resume_text:
        return resume_text
    
    optimized = resume_text
    
    # Categorize missing keywords
    categorized_skills, uncategorized = categorize_skills(missing_keywords)
    
    # Find existing SKILLS section
    skills_pattern = r'(SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|EXPERTISE)(.*?)(?=\n\n[A-Z]|\n[A-Z]{4,}|$)'
    skills_match = re.search(skills_pattern, resume_text, re.IGNORECASE | re.DOTALL)
    
    if skills_match:
        # Replace existing skills section with categorized version
        skills_section_start = skills_match.start()
        skills_section_end = skills_match.end()
        
        # Build new categorized skills section
        new_skills_lines = ["\n\n**SKILLS**"]
        
        for category, skills in categorized_skills.items():
            if skills:
                # Format: Category: skill1, skill2, skill3
                skills_str = ", ".join(skills[:10])  # Limit per category for 1-page
                new_skills_lines.append(f"{category}: {skills_str}")
        
        # Add uncategorized at the end
        if uncategorized:
            uncategorized_str = ", ".join(uncategorized[:8])
            new_skills_lines.append(f"Other: {uncategorized_str}")
        
        new_skills_section = "\n".join(new_skills_lines) + "\n"
        
        # Replace old skills section
        optimized = resume_text[:skills_section_start] + new_skills_section + resume_text[skills_section_end:]
    
    else:
        # Create new categorized skills section
        new_skills_lines = ["\n\n**SKILLS**"]
        
        for category, skills in categorized_skills.items():
            if skills:
                skills_str = ", ".join(skills[:10])
                new_skills_lines.append(f"{category}: {skills_str}")
        
        if uncategorized:
            uncategorized_str = ", ".join(uncategorized[:8])
            new_skills_lines.append(f"Other: {uncategorized_str}")
        
        new_skills_section = "\n".join(new_skills_lines) + "\n"
        optimized = resume_text + new_skills_section
    
    return optimized

def generate_resume_from_form(form_data):
    resume = []
    
    # Header with name
    if form_data['name']:
        resume.append(form_data['name'].upper())
    
    # Contact info in one line
    contact = []
    if form_data['email']:
        contact.append(form_data['email'])
    if form_data['phone']:
        contact.append(form_data['phone'])
    if form_data['linkedin']:
        contact.append(f"LinkedIn: {form_data['linkedin']}")
    if form_data['github']:
        contact.append(f"GitHub: {form_data['github']}")
    if form_data['portfolio_url']:
        contact.append(f"Portfolio: {form_data['portfolio_url']}")
    
    if contact:
        resume.append(' | '.join(contact))
    
    resume.append('')
    
    # Summary
    if form_data['summary']:
        resume.append('**PROFESSIONAL SUMMARY**')
        resume.append(form_data['summary'])
        resume.append('')
    
    # Skills (categorized if possible)
    if form_data['skills']:
        resume.append('**SKILLS**')
        skills_list = [s.strip() for s in form_data['skills'].split(',')]
        categorized, uncategorized = categorize_skills(skills_list)
        
        for category, skills in categorized.items():
            if skills:
                resume.append(f"{category}: {', '.join(skills)}")
        
        if uncategorized:
            resume.append(f"Other: {', '.join(uncategorized)}")
        
        resume.append('')
    
    # Work Experience
    if any(exp['title'] or exp['company'] for exp in form_data['experience']):
        resume.append('**WORK EXPERIENCE**')
        for exp in form_data['experience']:
            if exp['title'] or exp['company']:
                title_line = []
                if exp['title']:
                    title_line.append(exp['title'])
                if exp['company']:
                    title_line.append(exp['company'])
                if exp['duration']:
                    title_line.append(exp['duration'])
                resume.append(' | '.join(title_line))
                if exp['description']:
                    # Split description into bullet points if not already
                    desc_lines = exp['description'].strip().split('\n')
                    for line in desc_lines:
                        line = line.strip()
                        if line:
                            if not line.startswith('•') and not line.startswith('-'):
                                resume.append(f"• {line}")
                            else:
                                resume.append(line)
                resume.append('')
    
    # Projects
    if any(proj['name'] for proj in form_data['projects']):
        resume.append('**PROJECTS**')
        for proj in form_data['projects']:
            if proj['name']:
                proj_header = proj['name']
                if proj['link']:
                    proj_header += f" | Link: {proj['link']}"
                resume.append(proj_header)
                if proj['technologies']:
                    resume.append(f"Technologies: {proj['technologies']}")
                if proj['description']:
                    # Split into bullet points
                    desc_lines = proj['description'].strip().split('\n')
                    for line in desc_lines:
                        line = line.strip()
                        if line:
                            if not line.startswith('•') and not line.startswith('-'):
                                resume.append(f"• {line}")
                            else:
                                resume.append(line)
                resume.append('')
    
    # Education
    if form_data['education']:
        resume.append('**EDUCATION**')
        resume.append(form_data['education'])
        resume.append('')
    
    # Certificates
    if any(cert['name'] for cert in form_data['certificates']):
        resume.append('**CERTIFICATIONS**')
        for cert in form_data['certificates']:
            if cert['name']:
                cert_line = cert['name']
                if cert['link']:
                    cert_line += f" | {cert['link']}"
                resume.append(cert_line)
        resume.append('')
    
    return '\n'.join(resume)

def generate_pdf(resume_text, name="Resume"):
    """Generate professional 1-page PDF with bold headings"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        topMargin=0.5*inch,
        bottomMargin=0.4*inch,
        leftMargin=0.6*inch,
        rightMargin=0.6*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles for 1-page resume
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#000000',
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor='#333333',
        spaceAfter=8,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=11,
        textColor='#000000',
        spaceAfter=4,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#000000',
        spaceAfter=3,
        alignment=TA_JUSTIFY,
        leading=11
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#000000',
        spaceAfter=2,
        leftIndent=15,
        leading=10
    )
    
    story = []
    lines = resume_text.split('\n')
    
    is_first_line = True
    is_second_line = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.05*inch))
            continue
        
        # Remove markdown bold markers for processing
        line_clean = line.replace('**', '')
        
        # Escape special characters for reportlab
        line_escaped = line_clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # First line is name
        if is_first_line:
            story.append(Paragraph(line_escaped, name_style))
            is_first_line = False
            is_second_line = True
            continue
        
        # Second line is contact info
        if is_second_line:
            story.append(Paragraph(line_escaped, contact_style))
            is_second_line = False
            continue
        
        # Check if line is a heading (has ** markers or is all caps keyword)
        heading_keywords = ['PROFESSIONAL SUMMARY', 'SUMMARY', 'SKILLS', 'TECHNICAL SKILLS', 
                          'WORK EXPERIENCE', 'EXPERIENCE', 'PROJECTS', 'PROJECT EXPERIENCE',
                          'EDUCATION', 'CERTIFICATIONS', 'CERTIFICATES']
        
        if line.startswith('**') and line.endswith('**'):
            # Bold heading from markdown
            story.append(Paragraph(line_escaped, heading_style))
        elif any(line_clean.upper() == keyword for keyword in heading_keywords):
            # Keyword heading
            story.append(Paragraph(line_escaped, heading_style))
        elif line.startswith('•') or line.startswith('-'):
            # Bullet point
            story.append(Paragraph(line_escaped, bullet_style))
        else:
            # Regular text
            story.append(Paragraph(line_escaped, normal_style))
    
    try:
        doc.build(story)
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None
    
    buffer.seek(0)
    return buffer

def parse_resume_for_portfolio(resume_text):
    """Parse resume text to extract structured data for portfolio"""
    data = {
        'name': '',
        'email': '',
        'phone': '',
        'linkedin': '',
        'github': '',
        'portfolio': '',
        'summary': '',
        'projects': [],
        'skills': [],
        'experience': []
    }
    
    lines = resume_text.split('\n')
    
    # Extract name (first non-empty line)
    for line in lines:
        if line.strip():
            data['name'] = line.strip().replace('**', '')
            break
    
    # Extract contact info (second line with |)
    for line in lines[1:3]:
        if '|' in line:
            parts = line.split('|')
            for part in parts:
                part = part.strip()
                if '@' in part:
                    data['email'] = part
                elif 'linkedin' in part.lower():
                    data['linkedin'] = part.replace('LinkedIn:', '').strip()
                elif 'github' in part.lower():
                    data['github'] = part.replace('GitHub:', '').strip()
                elif 'portfolio' in part.lower():
                    data['portfolio'] = part.replace('Portfolio:', '').strip()
                elif any(char.isdigit() for char in part):
                    data['phone'] = part
    
    # Extract summary
    summary_match = re.search(
    r'\*\*(PROFESSIONAL SUMMARY|SUMMARY|PROFILE)\*\*\n(.*?)(?=\n\*\*|\n[A-Z]{4,}|$)',
    resume_text, re.IGNORECASE | re.DOTALL
    )

    if summary_match:
        data['summary'] = summary_match.group(1).strip()
    
    # Extract skills
    skills_match = re.search(r'\*\*SKILLS\*\*\n(.*?)(?=\n\*\*|\n[A-Z]{4,}|$)', resume_text, re.DOTALL)
    if skills_match:
        skills_text = skills_match.group(1).strip()
        # Parse categorized skills
        for line in skills_text.split('\n'):
            if ':' in line:
                category_skills = line.split(':', 1)[1].strip()
                data['skills'].extend([s.strip() for s in category_skills.split(',')])

    if not data['skills']:
        skill_lines = re.findall(r'•\s*(.+)', resume_text)
        data['skills'] = list(set(skill_lines[:30]))

    
    # Extract projects
    projects_match = re.search(
    r'\*\*(PROJECTS|PROJECT EXPERIENCE|ACADEMIC PROJECTS)\*\*',
    resume_text, re.IGNORECASE
)

    if projects_match:
        projects_text = projects_match.group(1).strip()
        project_blocks = re.split(r'\n(?=[A-Z]|\w)', projects_text)
        
        current_project = None
        for line in projects_text.split('\n'):
            line = line.strip()
            if not line:
                if current_project:
                    data['projects'].append(current_project)
                    current_project = None
                continue
            
            # Check if new project (doesn't start with • or Technologies:)
            if not line.startswith('•') and not line.startswith('Technologies:') and not line.startswith('-'):
                if current_project:
                    data['projects'].append(current_project)
                
                # Extract project name and link
                if '|' in line and 'Link:' in line:
                    parts = line.split('|')
                    proj_name = parts[0].strip()
                    proj_link = parts[1].replace('Link:', '').strip() if len(parts) > 1 else ''
                    current_project = {'name': proj_name, 'link': proj_link, 'technologies': '', 'description': ''}
                else:
                    current_project = {'name': line, 'link': '', 'technologies': '', 'description': ''}
            elif current_project:
                if line.startswith('Technologies:'):
                    current_project['technologies'] = line.replace('Technologies:', '').strip()
                elif line.startswith('•') or line.startswith('-'):
                    desc_line = line.lstrip('•-').strip()
                    if current_project['description']:
                        current_project['description'] += ' ' + desc_line
                    else:
                        current_project['description'] = desc_line
        
        if current_project:
            data['projects'].append(current_project)
    
    # Extract experience
    exp_match = re.search(
    r'\*\*(WORK EXPERIENCE|EXPERIENCE|PROFESSIONAL EXPERIENCE|INTERNSHIPS)\*\*',
    resume_text, re.IGNORECASE
)

    if exp_match:
        exp_text = exp_match.group(1).strip()
        
        current_exp = None
        for line in exp_text.split('\n'):
            line = line.strip()
            if not line:
                if current_exp:
                    data['experience'].append(current_exp)
                    current_exp = None
                continue
            
            # Check if new experience (has | separator)
            if '|' in line and not line.startswith('•') and not line.startswith('-'):
                if current_exp:
                    data['experience'].append(current_exp)
                
                parts = line.split('|')
                current_exp = {
                    'title': parts[0].strip() if len(parts) > 0 else '',
                    'company': parts[1].strip() if len(parts) > 1 else '',
                    'duration': parts[2].strip() if len(parts) > 2 else '',
                    'description': ''
                }
            elif current_exp and (line.startswith('•') or line.startswith('-')):
                desc_line = line.lstrip('•-').strip()
                if current_exp['description']:
                    current_exp['description'] += '\n• ' + desc_line
                else:
                    current_exp['description'] = '• ' + desc_line
        
        if current_exp:
            data['experience'].append(current_exp)
    
    return data

def generate_html_portfolio_ai(resume_text, job_description="", model="llama3.2:3b"):
    """
    Generate a complete HTML portfolio using AI (no templates, no parsing)
    """

    prompt = f"""
You are a senior UI/UX engineer and portfolio designer.

TASK:
Generate a visually attractive, modern, SINGLE-PAGE HTML portfolio website
based ONLY on the resume content provided.

ABSOLUTE RULES:
1. DO NOT invent experience, skills, metrics, or projects
2. Use ONLY information present in the resume
3. OMIT any section not present
4. Output ONLY valid HTML with embedded CSS
5. NO markdown
6. NO explanations
7. NO placeholder text
8. Mobile responsive
9. Clean, professional, recruiter-grade design

MANDATORY VISUAL DESIGN REQUIREMENTS (VERY IMPORTANT):
- Use a modern color palette (blue / indigo / slate)
- Use gradient backgrounds (header or section)
- Use card-based layout for Projects and Experience
- Use clear section separation
- Use shadows, rounded corners, spacing
- Use typography hierarchy (large headings, readable body)
- Skills MUST be displayed as colored tags or pills
- Page must NOT look plain or text-heavy

LAYOUT GUIDELINES:
- Centered max-width container
- Hero header section with name + role + contact info
- About / Summary section with soft background
- Experience as vertical cards or timeline
- Projects as grid cards
- Skills as colorful badges
- Footer with subtle dark background

TECHNICAL REQUIREMENTS:
- Embed all CSS inside <style>
- Use modern CSS (flexbox / grid)
- No external libraries
- Use accessible contrast
- Keep HTML clean and readable

RESUME CONTENT:
{resume_text}

OUTPUT:
Return ONLY the full HTML document starting with <!DOCTYPE html>.
"""

    html = call_ollama(prompt, model=model, temperature=0.55)

    # ---- SAFETY CHECKS ----
    if not html:
        return None

    lower_html = html.lower()
    banned_terms = ["lorem", "placeholder", "sample project", "dummy", "your name"]

    if any(term in lower_html for term in banned_terms):
        return None

    html_start = lower_html.find("<!doctype html")
    if html_start == -1:
        html_start = lower_html.find("<html")
    if html_start != -1:
        html = html[html_start:]
    else:
        return None

    return html



def generate_html_portfolio(resume_text):
    """Generate HTML portfolio from optimized resume"""
    
    # Parse resume to extract data
    data = parse_resume_for_portfolio(resume_text)
    
    name = data.get('name', 'Your Name')
    email = data.get('email', '')
    phone = data.get('phone', '')
    linkedin = data.get('linkedin', '')
    github = data.get('github', '')
    portfolio = data.get('portfolio', '')
    summary = data.get('summary', 'Passionate professional dedicated to excellence and innovation.')
    projects = data.get('projects', [])
    skills = data.get('skills', [])
    experience = data.get('experience', [])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Portfolio</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .contact-info {{
            margin-top: 20px;
            font-size: 1em;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .contact-info a {{
            color: white;
            text-decoration: none;
            transition: opacity 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .contact-info a:hover {{
            opacity: 0.7;
        }}
        
        .contact-info span {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        section {{
            padding: 60px 40px;
        }}
        
        section:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        h2 {{
            font-size: 2.5em;
            margin-bottom: 30px;
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .about-content {{
            font-size: 1.1em;
            line-height: 1.8;
            color: #555;
        }}
        
        .experience-timeline {{
            margin-top: 30px;
        }}
        
        .experience-item {{
            background: white;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }}
        
        .experience-item h3 {{
            color: #667eea;
            font-size: 1.4em;
            margin-bottom: 5px;
        }}
        
        .experience-item .company {{
            color: #764ba2;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .experience-item .duration {{
            color: #888;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        
        .experience-item .description {{
            color: #666;
            line-height: 1.6;
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}
        
        .project-card {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }}
        
        .project-card h3 {{
            color: #667eea;
            font-size: 1.5em;
            margin-bottom: 15px;
        }}
        
        .project-link {{
            display: inline-block;
            color: #764ba2;
            text-decoration: none;
            font-weight: bold;
            margin-bottom: 10px;
            transition: color 0.3s;
        }}
        
        .project-link:hover {{
            color: #667eea;
        }}
        
        .project-tech {{
            color: #764ba2;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 0.9em;
        }}
        
        .project-description {{
            color: #666;
            line-height: 1.6;
        }}
        
        .skills-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 30px;
        }}
        
        .skill-tag {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 1em;
            font-weight: 500;
            transition: transform 0.3s;
        }}
        
        .skill-tag:hover {{
            transform: scale(1.05);
        }}
        
        footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 30px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            header h1 {{
                font-size: 2em;
            }}
            
            section {{
                padding: 40px 20px;
            }}
            
            h2 {{
                font-size: 2em;
            }}
            
            .projects-grid {{
                grid-template-columns: 1fr;
            }}
            
            .contact-info {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{name}</h1>
            <p>Professional Portfolio</p>
            <div class="contact-info">
"""
    
    if email:
        html += f'                <a href="mailto:{email}">📧 {email}</a>\n'
    if phone:
        html += f'                <span>📱 {phone}</span>\n'
    if linkedin:
        html += f'                <a href="{linkedin}" target="_blank">💼 LinkedIn</a>\n'
    if github:
        html += f'                <a href="{github}" target="_blank">💻 GitHub</a>\n'
    if portfolio:
        html += f'                <a href="{portfolio}" target="_blank">🌐 Portfolio</a>\n'
    
    html += """            </div>
        </header>
        
        <section id="about">
            <h2>About Me</h2>
            <div class="about-content">
"""
    
    html += f'                <p>{summary}</p>\n'
    
    html += """            </div>
        </section>
"""
    
    # Add experience section if available
    if experience:
        html += """        
        <section id="experience">
            <h2>Work Experience</h2>
            <div class="experience-timeline">
"""
        for exp in experience:
            html += f"""                <div class="experience-item">
                    <h3>{exp.get('title', 'Position')}</h3>
                    <div class="company">{exp.get('company', 'Company')}</div>
                    <div class="duration">{exp.get('duration', '')}</div>
                    <div class="description">{exp.get('description', '').replace(chr(10), '<br>')}</div>
                </div>
"""
        html += """            </div>
        </section>
"""
    
    # Add projects section
    html += """        
        <section id="projects">
            <h2>Projects</h2>
            <div class="projects-grid">
"""
    
    if projects and len(projects) > 0:
        for project in projects:
            if project.get('name'):
                html += f"""                <div class="project-card">
                    <h3>{project.get('name', 'Project')}</h3>
"""
                if project.get('link'):
                    html += f'                    <a href="{project.get("link")}" class="project-link" target="_blank">🔗 View Project</a><br>\n'
                
                if project.get('technologies'):
                    html += f'                    <div class="project-tech">Technologies: {project.get("technologies")}</div>\n'
                
                html += f"""                    <div class="project-description">
                        {project.get('description', 'Project description not available.')}
                    </div>
                </div>
"""
    else:
        html += """                <div class="project-card">
                    <h3>Sample Project</h3>
                    <div class="project-tech">Technologies: Various</div>
                    <div class="project-description">
                        Add your projects to showcase your work and achievements.
                    </div>
                </div>
"""
    
    html += """            </div>
        </section>
        
        <section id="skills">
            <h2>Skills</h2>
            <div class="skills-container">
"""
    
    if skills and len(skills) > 0:
        for skill in skills[:40]:  # Limit to 40 skills for clean display
            if skill.strip():
                html += f'                <div class="skill-tag">{skill.strip()}</div>\n'
    else:
        html += '                <div class="skill-tag">Problem Solving</div>\n'
        html += '                <div class="skill-tag">Team Collaboration</div>\n'
        html += '                <div class="skill-tag">Communication</div>\n'
    
    html += f"""            </div>
        </section>
        
        <footer>
            <p>&copy; 2024 {name}. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>"""
    
    return html



# Streamlit UI
st.set_page_config(page_title="AI Resume & Portfolio Builder", page_icon="📄", layout="wide")

st.title("🤖 AI-Powered Resume & Portfolio Builder")
st.markdown("*Powered by Ollama Local AI*")
st.markdown("---")

# Check Ollama availability
if st.session_state.ollama_available is None:
    with st.spinner("Checking Ollama availability..."):
        available, models = check_ollama_availability()
        st.session_state.ollama_available = available
        st.session_state.available_models = models if models else ["llama3.2:3b"]

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Resume Input", "🎯 ATS Analysis", "⚡ AI Optimization", "💡 AI Suggestions", "📦 Export"])

# Tab 1: Resume Input
with tab1:
    st.header("Resume Input")
    
    input_mode = st.radio("Choose input method:", ["Upload Resume", "Manual Resume Builder"], horizontal=True)
    
    if input_mode == "Upload Resume":
        st.subheader("Upload Your Resume")
        uploaded_file = st.file_uploader("Upload PDF or DOCX", type=['pdf', 'docx'])
        
        if uploaded_file:
            with st.spinner("Extracting text from resume..."):
                if uploaded_file.type == "application/pdf":
                    extracted_text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    extracted_text = extract_text_from_docx(uploaded_file)
                else:
                    st.error("Unsupported file format")
                    extracted_text = ""
                
                if extracted_text:
                    st.success("Resume extracted successfully!")
                    st.session_state.resume_text = st.text_area(
                        "Extracted Resume Text (editable):",
                        value=extracted_text,
                        height=400
                    )
    
    else:  # Manual Resume Builder
        st.subheader("Build Your Resume")
        
        st.info("📌 Tips: Keep entries concise for 1-page format. Use bullet points for descriptions.")
        
        # Personal Info
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.form_data['name'] = st.text_input("Full Name *", value=st.session_state.form_data['name'])
            st.session_state.form_data['email'] = st.text_input("Email *", value=st.session_state.form_data['email'])
            st.session_state.form_data['phone'] = st.text_input("Phone", value=st.session_state.form_data['phone'])
        
        with col2:
            st.session_state.form_data['linkedin'] = st.text_input("LinkedIn URL", value=st.session_state.form_data['linkedin'], placeholder="https://linkedin.com/in/yourprofile")
            st.session_state.form_data['github'] = st.text_input("GitHub URL", value=st.session_state.form_data['github'], placeholder="https://github.com/yourusername")
            st.session_state.form_data['portfolio_url'] = st.text_input("Portfolio URL", value=st.session_state.form_data['portfolio_url'], placeholder="https://yourportfolio.com")
        
        # Professional Summary
        st.subheader("Professional Summary")
        st.session_state.form_data['summary'] = st.text_area(
            "2-3 sentences highlighting your expertise (max 60 words)",
            value=st.session_state.form_data['summary'],
            height=100,
            help="Or use AI to generate one in the AI Suggestions tab!",
            max_chars=400
        )
        
        # Skills
        st.subheader("Skills")
        st.session_state.form_data['skills'] = st.text_area(
            "Enter skills separated by commas",
            value=st.session_state.form_data['skills'],
            height=80,
            placeholder="Python, Java, React, AWS, Docker, Machine Learning"
        )
        
        # Work Experience
        st.subheader("Work Experience")
        num_experiences = st.number_input("Number of experiences", min_value=0, max_value=5, value=len(st.session_state.form_data['experience']))
        
        if num_experiences != len(st.session_state.form_data['experience']):
            if num_experiences > len(st.session_state.form_data['experience']):
                for _ in range(num_experiences - len(st.session_state.form_data['experience'])):
                    st.session_state.form_data['experience'].append({'title': '', 'company': '', 'duration': '', 'description': ''})
            else:
                st.session_state.form_data['experience'] = st.session_state.form_data['experience'][:num_experiences]
        
        for i in range(num_experiences):
            with st.expander(f"Experience {i+1}", expanded=(i==0)):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.session_state.form_data['experience'][i]['title'] = st.text_input(
                        f"Job Title",
                        value=st.session_state.form_data['experience'][i]['title'],
                        key=f"exp_title_{i}"
                    )
                with col2:
                    st.session_state.form_data['experience'][i]['company'] = st.text_input(
                        f"Company",
                        value=st.session_state.form_data['experience'][i]['company'],
                        key=f"exp_company_{i}"
                    )
                with col3:
                    st.session_state.form_data['experience'][i]['duration'] = st.text_input(
                        f"Duration",
                        value=st.session_state.form_data['experience'][i]['duration'],
                        key=f"exp_duration_{i}",
                        placeholder="Jan 2022 - Present"
                    )
                st.session_state.form_data['experience'][i]['description'] = st.text_area(
                    f"Description (use bullet points, one per line)",
                    value=st.session_state.form_data['experience'][i]['description'],
                    key=f"exp_desc_{i}",
                    height=100,
                    placeholder="• Achieved X by doing Y\n• Improved Z by N%\n• Led team of N people"
                )
        
        # Projects
        st.subheader("Projects")
        num_projects = st.number_input("Number of projects", min_value=0, max_value=6, value=len(st.session_state.form_data['projects']))
        
        if num_projects != len(st.session_state.form_data['projects']):
            if num_projects > len(st.session_state.form_data['projects']):
                for _ in range(num_projects - len(st.session_state.form_data['projects'])):
                    st.session_state.form_data['projects'].append({'name': '', 'description': '', 'technologies': '', 'link': ''})
            else:
                st.session_state.form_data['projects'] = st.session_state.form_data['projects'][:num_projects]
        
        for i in range(num_projects):
            with st.expander(f"Project {i+1}", expanded=(i==0)):
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.form_data['projects'][i]['name'] = st.text_input(
                        f"Project Name",
                        value=st.session_state.form_data['projects'][i]['name'],
                        key=f"proj_name_{i}"
                    )
                with col2:
                    st.session_state.form_data['projects'][i]['link'] = st.text_input(
                        f"Project Link (GitHub/Demo)",
                        value=st.session_state.form_data['projects'][i]['link'],
                        key=f"proj_link_{i}",
                        placeholder="https://github.com/user/project"
                    )
                
                st.session_state.form_data['projects'][i]['technologies'] = st.text_input(
                    f"Technologies Used",
                    value=st.session_state.form_data['projects'][i]['technologies'],
                    key=f"proj_tech_{i}",
                    placeholder="React, Node.js, MongoDB"
                )
                
                st.session_state.form_data['projects'][i]['description'] = st.text_area(
                    f"Description (2-3 bullet points)",
                    value=st.session_state.form_data['projects'][i]['description'],
                    key=f"proj_desc_{i}",
                    height=80,
                    placeholder="• Brief description of what the project does\n• Key features or achievements"
                )
        
        # Education
        st.subheader("Education")
        st.session_state.form_data['education'] = st.text_area(
            "Education Details",
            value=st.session_state.form_data['education'],
            height=80,
            placeholder="Bachelor of Science in Computer Science\nUniversity Name | 2018-2022 | GPA: 3.8/4.0"
        )
        
        # Certifications
        st.subheader("Certifications")
        num_certs = st.number_input("Number of certifications", min_value=0, max_value=6, value=len(st.session_state.form_data['certificates']))
        
        if num_certs != len(st.session_state.form_data['certificates']):
            if num_certs > len(st.session_state.form_data['certificates']):
                for _ in range(num_certs - len(st.session_state.form_data['certificates'])):
                    st.session_state.form_data['certificates'].append({'name': '', 'link': ''})
            else:
                st.session_state.form_data['certificates'] = st.session_state.form_data['certificates'][:num_certs]
        
        for i in range(num_certs):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.session_state.form_data['certificates'][i]['name'] = st.text_input(
                    f"Certification {i+1}",
                    value=st.session_state.form_data['certificates'][i]['name'],
                    key=f"cert_name_{i}",
                    placeholder="AWS Certified Solutions Architect"
                )
            with col2:
                st.session_state.form_data['certificates'][i]['link'] = st.text_input(
                    f"Certificate Link",
                    value=st.session_state.form_data['certificates'][i]['link'],
                    key=f"cert_link_{i}",
                    placeholder="Credential URL"
                )
        
        st.markdown("---")
        
        if st.button("🎨 Generate Resume Text", type="primary", use_container_width=True):
            if not st.session_state.form_data['name']:
                st.error("Please enter your name")
            elif not st.session_state.form_data['email']:
                st.error("Please enter your email")
            else:
                with st.spinner("Generating resume..."):
                    generated_resume = generate_resume_from_form(st.session_state.form_data)
                    st.session_state.resume_text = generated_resume
                    st.success("✅ Resume generated successfully!")
                    st.rerun()
        
        if st.session_state.resume_text:
            st.markdown("---")
            st.subheader("📄 Live Preview")
            st.text_area("Generated Resume", value=st.session_state.resume_text, height=400, key="preview_resume", disabled=True)

# Tab 2: ATS Analysis
with tab2:
    st.header("ATS Keyword Analyzer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Resume")
        if st.session_state.resume_text:
            st.text_area("Current Resume", value=st.session_state.resume_text, height=300, disabled=True, key="ats_resume")
        else:
            st.warning("⚠️ Please input your resume in the Resume Input tab first.")
    
    with col2:
        st.subheader("Job Description")
        st.session_state.job_description = st.text_area(
            "Paste Job Description Here",
            value=st.session_state.job_description,
            height=300,
            placeholder="Paste the job description you want to match your resume against..."
        )
    
    if st.button("🎯 Analyze ATS Score", type="primary", use_container_width=True):
        if not st.session_state.resume_text:
            st.error("❌ Please provide a resume first.")
        elif not st.session_state.job_description:
            st.error("❌ Please provide a job description.")
        else:
            with st.spinner("Analyzing ATS score..."):
                resume_keywords = extract_keywords(st.session_state.resume_text)
                jd_keywords = extract_keywords(st.session_state.job_description)
                
                score, matched, missing = calculate_ats_score(resume_keywords, jd_keywords)
                
                st.session_state.ats_score = score
                st.session_state.matched_keywords = matched
                st.session_state.missing_keywords = missing
                
                st.success("✅ Analysis complete!")
                st.rerun()
    
    if st.session_state.ats_score is not None:
        st.markdown("---")
        st.subheader("📊 ATS Analysis Results")
        
        # Score display with color coding
        col1, col2, col3 = st.columns(3)
        
        with col1:
            score_color = "🟢" if st.session_state.ats_score >= 80 else "🟡" if st.session_state.ats_score >= 60 else "🔴"
            st.metric("ATS Score", f"{st.session_state.ats_score}%")
            st.markdown(f"<h1 style='text-align: center;'>{score_color}</h1>", unsafe_allow_html=True)
        
        with col2:
            st.metric("Matched Keywords", len(st.session_state.matched_keywords))
        
        with col3:
            st.metric("Missing Keywords", len(st.session_state.missing_keywords))
        
        # Matched keywords
        if st.session_state.matched_keywords:
            st.subheader("✅ Matched Keywords")
            matched_html = " ".join([f'<span style="background-color: #d4edda; color: #155724; padding: 5px 10px; margin: 5px; border-radius: 5px; display: inline-block;">{kw}</span>' for kw in st.session_state.matched_keywords[:50]])
            st.markdown(matched_html, unsafe_allow_html=True)
        
        # Missing keywords
        if st.session_state.missing_keywords:
            st.subheader("❌ Missing Keywords")
            missing_html = " ".join([f'<span style="background-color: #f8d7da; color: #721c24; padding: 5px 10px; margin: 5px; border-radius: 5px; display: inline-block;">{kw}</span>' for kw in st.session_state.missing_keywords[:50]])
            st.markdown(missing_html, unsafe_allow_html=True)

# Tab 3: AI Optimization
with tab3:
    st.header("⚡ AI-Powered Resume Optimization")
    
    # Ollama Status
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.ollama_available:
            st.success("🟢 Ollama is running and available")
        else:
            st.error("🔴 Ollama is not running. Please start Ollama to use AI features.")
            st.info("Install Ollama from https://ollama.ai and run: `ollama pull llama3.2:3b`")
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.ollama_available = None
            st.rerun()
    
    if not st.session_state.resume_text:
        st.warning("⚠️ Please provide a resume in the Resume Input tab first.")
    elif not st.session_state.job_description:
        st.warning("⚠️ Please provide a job description and run ATS analysis first.")
    elif st.session_state.ats_score is None:
        st.warning("⚠️ Please run ATS analysis first in the ATS Analysis tab.")
    else:
        # Model selection
        if st.session_state.ollama_available and st.session_state.available_models:
            selected_model = st.selectbox(
                "🤖 Select AI Model",
                st.session_state.available_models,
                help="Choose the Ollama model for optimization"
            )
        else:
            selected_model = "llama3.2:3b"
        
        st.info(f"💡 AI will intelligently optimize your resume by adding missing keywords naturally without hallucinating content. Using model: **{selected_model}**")
        
        # Optimization options
        col1, col2 = st.columns(2)
        with col1:
            optimization_type = st.radio(
                "Optimization Type",
                ["Rule-Based (Fast)", "AI-Powered (Smart)"],
                help="Rule-based adds keywords to skills section. AI-powered integrates keywords naturally throughout resume."
            )
        
        with col2:
            if optimization_type == "AI-Powered (Smart)" and not st.session_state.ollama_available:
                st.warning("⚠️ AI optimization requires Ollama to be running")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Original Resume")
            st.text_area("Current", value=st.session_state.resume_text, height=400, disabled=True, key="opt_original")
        
        with col2:
            st.subheader("✨ Optimized Resume")
            if st.session_state.optimized_resume:
                st.text_area("Optimized", value=st.session_state.optimized_resume, height=400, key="opt_result")
            else:
                st.text_area("Optimized", value="Click 'Optimize Resume' to generate...", height=400, disabled=True, key="opt_placeholder")
        
        if st.button("🚀 Optimize Resume", type="primary", use_container_width=True):
            if optimization_type == "Rule-Based (Fast)":
                with st.spinner("Optimizing resume with categorized skills..."):
                    optimized = optimize_resume_rule_based(
                        st.session_state.resume_text,
                        st.session_state.missing_keywords
                    )
                    
                    if len(optimized) >= len(st.session_state.resume_text) * 0.8:
                        st.session_state.optimized_resume = optimized
                        st.success("✅ Resume optimized successfully with categorized skills!")
                        st.rerun()
                    else:
                        st.error("❌ Optimization failed: result too short. Using original resume.")
                        st.session_state.optimized_resume = st.session_state.resume_text
            
            else:  # AI-Powered
                if not st.session_state.ollama_available:
                    st.error("❌ Please start Ollama first to use AI optimization")
                else:
                    with st.spinner(f"🤖 AI is analyzing and optimizing your resume using {selected_model}... This may take 30-60 seconds..."):
                        optimized = ai_optimize_resume(
                            st.session_state.resume_text,
                            st.session_state.missing_keywords,
                            model=selected_model
                        )
                        
                        if optimized and len(optimized) >= len(st.session_state.resume_text) * 0.7:
                            st.session_state.optimized_resume = optimized
                            st.success("✅ AI optimization complete! Resume enhanced with natural keyword integration.")
                            st.rerun()
                        else:
                            st.warning("⚠️ AI optimization produced unexpected results. Falling back to rule-based optimization.")
                            optimized = optimize_resume_rule_based(
                                st.session_state.resume_text,
                                st.session_state.missing_keywords
                            )
                            st.session_state.optimized_resume = optimized
                            st.rerun()
        
        if st.session_state.optimized_resume:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Use Optimized Resume", type="primary", use_container_width=True):
                    st.session_state.resume_text = st.session_state.optimized_resume
                    st.success("✅ Optimized resume is now your active resume!")
                    st.rerun()
            with col2:
                if st.button("🔄 Reset to Original", use_container_width=True):
                    st.session_state.optimized_resume = ""
                    st.info("Reset complete. Original resume preserved.")
                    st.rerun()

# Tab 4: AI Suggestions
with tab4:
    st.header("💡 AI-Powered Resume Suggestions")
    
    if not st.session_state.ollama_available:
        st.error("🔴 Ollama is not running. Please start Ollama to use AI features.")
        st.info("Install Ollama from https://ollama.ai and run: `ollama pull llama3.2:3b`")
    else:
        st.success("🟢 AI Suggestions Available")
    
    if not st.session_state.resume_text:
        st.warning("⚠️ Please provide a resume first.")
    elif not st.session_state.job_description:
        st.warning("⚠️ Please provide a job description first.")
    else:
        # Model selection
        if st.session_state.available_models:
            selected_model = st.selectbox(
                "🤖 Select AI Model",
                st.session_state.available_models,
                help="Choose the Ollama model for suggestions",
                key="suggestions_model"
            )
        else:
            selected_model = "llama3.2:3b"
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Get AI Improvement Suggestions", type="primary", disabled=not st.session_state.ollama_available, use_container_width=True):
                with st.spinner(f"🤖 AI is analyzing your resume using {selected_model}..."):
                    suggestions = ai_suggest_improvements(
                        st.session_state.resume_text,
                        st.session_state.job_description,
                        st.session_state.ats_score if st.session_state.ats_score else 0,
                        model=selected_model
                    )
                    
                    if suggestions:
                        st.session_state.ai_suggestions = suggestions
                        st.success("✅ AI analysis complete!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to generate suggestions. Please try again.")
        
        with col2:
            if st.button("✍️ Generate AI Professional Summary", type="primary", disabled=not st.session_state.ollama_available, use_container_width=True):
                with st.spinner(f"🤖 AI is creating a professional summary using {selected_model}..."):
                    summary = ai_generate_professional_summary(
                        st.session_state.resume_text,
                        st.session_state.job_description,
                        model=selected_model
                    )
                    
                    if summary:
                        st.session_state.form_data['summary'] = summary
                        st.success("✅ Professional summary generated! Check Resume Input tab to use it.")
                        st.info(f"**Generated Summary:**\n\n{summary}")
                    else:
                        st.error("❌ Failed to generate summary. Please try again.")
        
        if st.session_state.ai_suggestions:
            st.markdown("---")
            st.subheader("📋 AI Recommendations")
            st.markdown(st.session_state.ai_suggestions)
        
        # Bullet point improvement
        st.markdown("---")
        st.subheader("🎯 Improve Bullet Points with AI")
        st.info("💡 Paste your bullet points below and AI will make them more impactful and achievement-focused")
        
        bullet_input = st.text_area(
            "Paste bullet points (one per line)",
            height=150,
            placeholder="• Developed web applications\n• Managed team projects\n• Improved system performance"
        )
        
        if st.button("✨ Improve Bullet Points", disabled=not st.session_state.ollama_available or not bullet_input, use_container_width=True):
            with st.spinner(f"🤖 AI is improving your bullet points using {selected_model}..."):
                improved = ai_improve_bullet_points(
                    bullet_input,
                    st.session_state.job_description,
                    model=selected_model
                )
                
                if improved:
                    st.success("✅ Bullet points improved!")
                    st.markdown("**✨ Improved Version:**")
                    st.markdown(improved)
                    
                    if st.button("📋 Copy to Clipboard"):
                        st.code(improved, language=None)
                else:
                    st.error("❌ Failed to improve bullet points. Please try again.")

# Tab 5: Export
with tab5:
    st.header("📦 Export Options")
    
    if not st.session_state.resume_text:
        st.warning("⚠️ Please provide a resume in the Resume Input tab first.")
    else:
        # Choose which resume to export
        resume_to_export = st.radio(
            "Select resume version to export:",
            ["Original Resume", "Optimized Resume (if available)"],
            horizontal=True
        )
        
        if resume_to_export == "Optimized Resume (if available)" and st.session_state.optimized_resume:
            final_resume = st.session_state.optimized_resume
            st.success("✅ Using optimized resume for export")
        else:
            final_resume = st.session_state.resume_text
            if resume_to_export == "Optimized Resume (if available)" and not st.session_state.optimized_resume:
                st.info("ℹ️ No optimized resume available. Using original resume.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Export as PDF")
            st.write("Download your resume as a professional 1-page ATS-friendly PDF with **bold headings**.")
            
            if st.button("🎨 Generate PDF", type="primary", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    pdf_buffer = generate_pdf(final_resume, st.session_state.form_data.get('name', 'Resume'))
                    
                    if pdf_buffer:
                        pdf_buffer.seek(0)
                        st.success("✅ PDF generated successfully!")
                        st.download_button(
                            label="📥 Download PDF Resume",
                            data=pdf_buffer,
                            file_name=f"{st.session_state.form_data.get('name', 'resume').replace(' ', '_')}_resume.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ Failed to generate PDF. Please check your resume format.")
        
        with col2:
            st.subheader("🌐 Generate HTML Portfolio")
            st.write("Create a modern, responsive portfolio website with your **optimized resume data**.")
            
            portfolio_mode = st.radio(
                "Portfolio Generation Mode",
                ["AI-Generated (Smart)", "Template-Based (Fast)"],
                horizontal=True,
                help="AI-generated creates a unique portfolio using AI. Template-based is faster and deterministic."
            )


            if st.button("🎨 Generate Portfolio", type="primary", use_container_width=True):
                with st.spinner("Generating portfolio from optimized resume..."):
                    # Use optimized resume if available for portfolio
                    portfolio_source = st.session_state.optimized_resume if st.session_state.optimized_resume else st.session_state.resume_text
                    if portfolio_mode == "AI-Generated (Smart)":
                        html_content = generate_html_portfolio_ai(
                        resume_text=portfolio_source,
                        job_description=st.session_state.job_description,
                        model=selected_model
                    )
                    else:
                        html_content = generate_html_portfolio(portfolio_source)

                    if not html_content:
                        st.error("❌ Portfolio generation failed.")
                    else:
                        st.download_button(
                            label="📥 Download HTML Portfolio",
                            data=html_content.encode("utf-8"),
                            file_name="portfolio.html",
                            mime="text/html",
                            use_container_width=True
                        )
                    st.info("💡 Download the HTML file and open it in any browser to see your portfolio!")
        
        st.markdown("---")
        st.subheader("📄 Preview Current Resume")
        st.text_area("Resume Content", value=final_resume, height=400, disabled=True, key="export_preview")
        
        # Word count check for 1-page guideline
        word_count = len(final_resume.split())
        if word_count > 600:
            st.warning(f"⚠️ Your resume has {word_count} words. Consider reducing to 400-600 words for a clean 1-page format.")
        elif word_count > 400:
            st.success(f"✅ Your resume has {word_count} words. Good length for 1-page format!")
        else:
            st.info(f"ℹ️ Your resume has {word_count} words. You have room to add more details!")

# Sidebar
with st.sidebar:
    st.header("📊 Dashboard")
    
    # Ollama Status
    st.subheader("🤖 AI Status")
    if st.session_state.ollama_available:
        st.success("✅ Ollama: Online")
        if st.session_state.available_models:
            st.write(f"**Models Available:** {len(st.session_state.available_models)}")
            with st.expander("📋 View Models"):
                for model in st.session_state.available_models:
                    st.write(f"• {model}")
    else:
        st.error("❌ Ollama: Offline")
        if st.button("🔄 Retry Connection", use_container_width=True):
            st.session_state.ollama_available = None
            st.rerun()
    
    st.markdown("---")
    
    # ATS Score
    if st.session_state.ats_score is not None:
        st.metric("📊 Current ATS Score", f"{st.session_state.ats_score}%")
        
        if st.session_state.ats_score >= 80:
            st.success("🟢 Excellent match!")
        elif st.session_state.ats_score >= 60:
            st.warning("🟡 Good match, room for improvement")
        else:
            st.error("🔴 Needs optimization")
    
    st.markdown("---")
    st.subheader("📈 Quick Stats")
    
    if st.session_state.resume_text:
        word_count = len(st.session_state.resume_text.split())
        st.write(f"📝 Resume Words: **{word_count}**")
        
        if word_count > 600:
            st.caption("🔴 Too long for 1 page")
        elif word_count > 400:
            st.caption("🟢 Perfect for 1 page")
        else:
            st.caption("🟡 Room for more content")
    
    if st.session_state.job_description:
        jd_word_count = len(st.session_state.job_description.split())
        st.write(f"📋 JD Words: **{jd_word_count}**")
    
    if st.session_state.matched_keywords:
        st.write(f"✅ Matched: **{len(st.session_state.matched_keywords)}**")
    
    if st.session_state.missing_keywords:
        st.write(f"❌ Missing: **{len(st.session_state.missing_keywords)}**")
    
    st.markdown("---")
    st.subheader("💡 Pro Tips")
    st.write("""
    • **Keep resume 1 page** (400-600 words)
    • **Bold all headings** (auto-done in PDF)
    • **Add project & certificate links**
    • **Use action verbs** in descriptions
    • **Quantify achievements** (%, numbers)
    • **ATS score > 70%** is competitive
    • **Use AI suggestions** for better results
    • **Portfolio auto-generated** from optimized resume
    """)
    
    st.markdown("---")
    st.subheader("🔧 Ollama Setup")
    with st.expander("📖 Quick Setup Guide"):
        st.write("""
        **1. Install Ollama:**
        Visit https://ollama.ai
        
        **2. Pull recommended models:**
```bash
        ollama pull llama3.2:3b
```
        
        **3. Start Ollama:**
```bash
        ollama serve
```
        
        **4. Refresh this page**
        """)
    
    st.markdown("---")
    if st.button("🗑️ Reset All Data", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit & Ollama")
    st.caption("v2.0 - AI-Powered Resume Builder")