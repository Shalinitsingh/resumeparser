import streamlit as st
import os
import tempfile
import json
from typing import Optional, List, Dict, Any
import PyPDF2
from docx import Document
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Resume Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e7d32;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #2e7d32;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        text-align: center;
    }
    .experience-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    .skill-tag {
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.25rem 0.5rem;
        border-radius: 1rem;
        margin: 0.25rem;
        display: inline-block;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

class ResumeParser:
    """Complete Resume Parser Class"""
    
    def __init__(self, api_key: str):
        """Initialize the parser with Gemini API key"""
        if not api_key:
            raise ValueError("API key is required")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.api_key = api_key
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini AI: {str(e)}")

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                with open(tmp_file.name, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num} ---\n" + page_text + "\n"
                    
            os.unlink(tmp_file.name)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                doc = Document(tmp_file.name)
                text = ""
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text += paragraph.text + "\n"
                    
            os.unlink(tmp_file.name)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting DOCX text: {str(e)}")

    def extract_text_from_file(self, uploaded_file) -> str:
        """Extract text based on file type"""
        file_content = uploaded_file.read()
        filename = uploaded_file.name.lower()
        
        if filename.endswith('.pdf'):
            return self.extract_text_from_pdf(file_content)
        elif filename.endswith(('.docx', '.doc')):
            return self.extract_text_from_docx(file_content)
        else:
            raise Exception("Unsupported file format. Please upload PDF or DOCX files.")

    def create_parsing_prompt(self, resume_text: str) -> str:
        """Create the prompt for resume parsing"""
        return f"""
You are an expert resume parser and HR analyst. Analyze the following resume text and extract comprehensive information. Be thorough and accurate in your extraction.

Resume Text:
{resume_text}

Extract and structure the following information as a JSON object:

1. **Personal Information:**
   - Full name
   - Email address  
   - Phone number
   - Physical address
   - LinkedIn profile URL
   - GitHub/Portfolio URLs
   - Professional websites

2. **Professional Summary:** Brief career overview/objective

3. **Work Experience:** List all jobs with:
   - Company name
   - Job title/position
   - Employment duration (start-end dates)
   - Location
   - Key responsibilities and achievements
   - Technologies/tools used

4. **Education:** All educational qualifications with:
   - Degree/certification name
   - Institution name
   - Graduation year
   - GPA/grades (if mentioned)
   - Relevant coursework

5. **Skills:** Categorize into:
   - Technical skills
   - Programming languages
   - Tools and technologies
   - Soft skills
   - Languages spoken

6. **Certifications:** All professional certifications with issuing organizations

7. **Projects:** Personal/professional projects with:
   - Project name
   - Description
   - Technologies used
   - Duration
   - Key achievements

8. **Additional Information:**
   - Awards and achievements
   - Publications
   - Volunteer work
   - Hobbies/interests

Return ONLY a valid JSON object with this exact structure:
{{
    "personal_info": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "phone number",
        "address": "full address",
        "linkedin": "linkedin URL",
        "github": "github URL",
        "portfolio": "portfolio URL"
    }},
    "summary": "Professional summary text",
    "experience": [
        {{
            "company": "Company Name",
            "position": "Job Title",
            "duration": "Start Date - End Date",
            "location": "City, State",
            "description": "Job description and achievements",
            "technologies": ["tech1", "tech2"]
        }}
    ],
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "Institution Name",
            "year": "Graduation Year",
            "gpa": "GPA if mentioned",
            "coursework": ["course1", "course2"]
        }}
    ],
    "skills": {{
        "technical": ["skill1", "skill2"],
        "programming": ["lang1", "lang2"],
        "tools": ["tool1", "tool2"],
        "soft_skills": ["skill1", "skill2"],
        "languages": ["English", "Spanish"]
    }},
    "certifications": [
        {{
            "name": "Certification Name",
            "issuer": "Issuing Organization",
            "date": "Issue Date"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Project description",
            "technologies": ["tech1", "tech2"],
            "duration": "Project duration",
            "achievements": "Key achievements"
        }}
    ],
    "additional": {{
        "awards": ["award1", "award2"],
        "publications": ["pub1", "pub2"],
        "volunteer": ["volunteer work"],
        "interests": ["interest1", "interest2"]
    }}
}}

If any field is not found, use null or empty array []. Ensure all text is properly extracted and formatted.
"""

    def parse_resume_with_ai(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text using Gemini AI"""
        try:
            prompt = self.create_parsing_prompt(resume_text)
            
            # Show progress
            with st.spinner("🤖 AI is analyzing your resume..."):
                response = self.model.generate_content(prompt)
            
            # Extract and clean response
            response_text = response.text.strip()
            
            # Clean markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                parsed_data = json.loads(response_text)
                return parsed_data
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse AI response as JSON: {str(e)}")
                st.text_area("Raw AI Response:", response_text, height=200)
                return {"error": "JSON parsing failed", "raw_response": response_text}
                
        except Exception as e:
            st.error(f"Error during AI parsing: {str(e)}")
            return {"error": str(e)}

def initialize_session_state():
    """Initialize session state variables"""
    if 'parsed_data' not in st.session_state:
        st.session_state.parsed_data = None
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = None
    if 'parser' not in st.session_state:
        st.session_state.parser = None

def create_api_key_input():
    """Create API key input section"""
    st.sidebar.markdown("### 🔑 API Configuration")
    
    # Check for API key in environment first
    env_api_key = os.getenv("GEMINI_API_KEY")
    
    if env_api_key:
        st.sidebar.success("✅ API key found in environment")
        return env_api_key
    else:
        st.sidebar.warning("⚠️ No API key found in environment")
        api_key = st.sidebar.text_input(
            "Enter your Gemini API Key:",
            type="password",
            help="Get your API key from https://makersuite.google.com/app/apikey"
        )
        
        if api_key:
            st.sidebar.success("✅ API key provided")
            return api_key
        else:
            st.sidebar.error("❌ API key required")
            st.sidebar.markdown("""
            **How to get Gemini API Key:**
            1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. Create a new API key
            3. Copy and paste it above
            """)
            return None

def display_personal_info(personal_info):
    """Display personal information section"""
    if not personal_info:
        return
    
    st.markdown('<div class="section-header">👤 Personal Information</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if personal_info.get("name"):
            st.markdown(f"**👨‍💼 Name:** {personal_info['name']}")
        if personal_info.get("email"):
            st.markdown(f"**📧 Email:** {personal_info['email']}")
    
    with col2:
        if personal_info.get("phone"):
            st.markdown(f"**📱 Phone:** {personal_info['phone']}")
        if personal_info.get("address"):
            st.markdown(f"**🏠 Address:** {personal_info['address']}")
    
    with col3:
        if personal_info.get("linkedin"):
            st.markdown(f"**💼 LinkedIn:** [Profile]({personal_info['linkedin']})")
        if personal_info.get("github"):
            st.markdown(f"**💻 GitHub:** [Profile]({personal_info['github']})")
        if personal_info.get("portfolio"):
            st.markdown(f"**🌐 Portfolio:** [Website]({personal_info['portfolio']})")

def display_summary(summary):
    """Display professional summary"""
    if summary and summary.strip():
        st.markdown('<div class="section-header">📝 Professional Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box">{summary}</div>', unsafe_allow_html=True)

def display_experience(experience_list):
    """Display work experience"""
    if not experience_list:
        return
    
    st.markdown('<div class="section-header">💼 Work Experience</div>', unsafe_allow_html=True)
    
    for i, exp in enumerate(experience_list):
        with st.expander(f"🏢 {exp.get('company', 'Unknown Company')} - {exp.get('position', 'Unknown Position')}", expanded=i==0):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if exp.get("position"):
                    st.markdown(f"**Position:** {exp['position']}")
                if exp.get("description"):
                    st.markdown(f"**Description:** {exp['description']}")
            
            with col2:
                if exp.get("duration"):
                    st.markdown(f"**Duration:** {exp['duration']}")
                if exp.get("location"):
                    st.markdown(f"**Location:** {exp['location']}")
            
            if exp.get("technologies"):
                st.markdown("**Technologies Used:**")
                tech_tags = ""
                for tech in exp['technologies']:
                    tech_tags += f'<span class="skill-tag">{tech}</span>'
                st.markdown(tech_tags, unsafe_allow_html=True)

def display_education(education_list):
    """Display education information"""
    if not education_list:
        return
    
    st.markdown('<div class="section-header">🎓 Education</div>', unsafe_allow_html=True)
    
    for edu in education_list:
        with st.expander(f"🏫 {edu.get('institution', 'Unknown Institution')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                if edu.get("degree"):
                    st.markdown(f"**Degree:** {edu['degree']}")
                if edu.get("year"):
                    st.markdown(f"**Graduation Year:** {edu['year']}")
            
            with col2:
                if edu.get("gpa"):
                    st.markdown(f"**GPA:** {edu['gpa']}")
                if edu.get("coursework"):
                    st.markdown("**Relevant Coursework:**")
                    for course in edu['coursework']:
                        st.markdown(f"• {course}")

def display_skills(skills):
    """Display skills section"""
    if not skills:
        return
    
    st.markdown('<div class="section-header">🔧 Skills</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if skills.get("technical"):
            st.markdown("**Technical Skills:**")
            tech_tags = ""
            for skill in skills['technical']:
                tech_tags += f'<span class="skill-tag">{skill}</span>'
            st.markdown(tech_tags, unsafe_allow_html=True)
        
        if skills.get("programming"):
            st.markdown("**Programming Languages:**")
            prog_tags = ""
            for lang in skills['programming']:
                prog_tags += f'<span class="skill-tag">{lang}</span>'
            st.markdown(prog_tags, unsafe_allow_html=True)
    
    with col2:
        if skills.get("tools"):
            st.markdown("**Tools & Technologies:**")
            tool_tags = ""
            for tool in skills['tools']:
                tool_tags += f'<span class="skill-tag">{tool}</span>'
            st.markdown(tool_tags, unsafe_allow_html=True)
        
        if skills.get("soft_skills"):
            st.markdown("**Soft Skills:**")
            soft_tags = ""
            for skill in skills['soft_skills']:
                soft_tags += f'<span class="skill-tag">{skill}</span>'
            st.markdown(soft_tags, unsafe_allow_html=True)

def display_projects(projects_list):
    """Display projects section"""
    if not projects_list:
        return
    
    st.markdown('<div class="section-header">🚀 Projects</div>', unsafe_allow_html=True)
    
    for project in projects_list:
        with st.expander(f"⚡ {project.get('name', 'Unknown Project')}"):
            if project.get("description"):
                st.markdown(f"**Description:** {project['description']}")
            if project.get("duration"):
                st.markdown(f"**Duration:** {project['duration']}")
            if project.get("achievements"):
                st.markdown(f"**Achievements:** {project['achievements']}")
            if project.get("technologies"):
                st.markdown("**Technologies:**")
                tech_tags = ""
                for tech in project['technologies']:
                    tech_tags += f'<span class="skill-tag">{tech}</span>'
                st.markdown(tech_tags, unsafe_allow_html=True)

def display_certifications(certifications_list):
    """Display certifications"""
    if not certifications_list:
        return
    
    st.markdown('<div class="section-header">🏆 Certifications</div>', unsafe_allow_html=True)
    
    for cert in certifications_list:
        if isinstance(cert, dict):
            st.markdown(f"• **{cert.get('name', 'Unknown')}** - {cert.get('issuer', 'Unknown Issuer')} ({cert.get('date', 'Date not specified')})")
        else:
            st.markdown(f"• {cert}")

def display_additional_info(additional):
    """Display additional information"""
    if not additional:
        return
    
    st.markdown('<div class="section-header">🌟 Additional Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if additional.get("awards"):
            st.markdown("**🏆 Awards & Achievements:**")
            for award in additional['awards']:
                st.markdown(f"• {award}")
        
        if additional.get("publications"):
            st.markdown("**📚 Publications:**")
            for pub in additional['publications']:
                st.markdown(f"• {pub}")
    
    with col2:
        if additional.get("volunteer"):
            st.markdown("**🤝 Volunteer Work:**")
            for vol in additional['volunteer']:
                st.markdown(f"• {vol}")
        
        if additional.get("interests"):
            st.markdown("**🎯 Interests:**")
            interest_tags = ""
            for interest in additional['interests']:
                interest_tags += f'<span class="skill-tag">{interest}</span>'
            st.markdown(interest_tags, unsafe_allow_html=True)

def display_parsed_results(parsed_data):
    """Display all parsed results"""
    if not parsed_data or "error" in parsed_data:
        st.error("❌ Failed to parse resume data")
        if "raw_response" in parsed_data:
            with st.expander("Show AI Response"):
                st.text(parsed_data["raw_response"])
        return
    
    # Display each section
    display_personal_info(parsed_data.get("personal_info"))
    display_summary(parsed_data.get("summary"))
    display_experience(parsed_data.get("experience"))
    display_education(parsed_data.get("education"))
    display_skills(parsed_data.get("skills"))
    display_projects(parsed_data.get("projects"))
    display_certifications(parsed_data.get("certifications"))
    display_additional_info(parsed_data.get("additional"))

def create_download_section(parsed_data, extracted_text):
    """Create download section"""
    st.markdown("---")
    st.markdown("### 📥 Download Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Download JSON", use_container_width=True):
            json_data = json.dumps(parsed_data, indent=2)
            st.download_button(
                label="📄 Download Parsed Data",
                data=json_data,
                file_name="parsed_resume.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col2:
        if st.button("📋 Download Text", use_container_width=True):
            st.download_button(
                label="📝 Download Extracted Text",
                data=extracted_text,
                file_name="extracted_text.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col3:
        if st.button("🔍 Show Raw JSON", use_container_width=True):
            st.json(parsed_data)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 AI-Powered Resume Parser</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # API Key Configuration
    api_key = create_api_key_input()
    
    if not api_key:
        st.markdown('''
        <div class="warning-box">
        <h3>⚠️ API Key Required</h3>
        <p>Please provide your Gemini API key to continue. You can:</p>
        <ol>
        <li>Add it to your .env file as GEMINI_API_KEY=your_key_here</li>
        <li>Or enter it in the sidebar</li>
        </ol>
        </div>
        ''', unsafe_allow_html=True)
        st.stop()
    
    # Initialize parser
    try:
        if not st.session_state.parser:
            st.session_state.parser = ResumeParser(api_key)
        st.sidebar.success("✅ Parser initialized successfully")
    except Exception as e:
        st.sidebar.error(f"❌ Failed to initialize parser: {str(e)}")
        st.stop()
    
    # Sidebar configuration
    st.sidebar.markdown("### ⚙️ Configuration")
    parsing_mode = st.sidebar.radio(
        "Choose input method:",
        ["📄 File Upload", "✏️ Text Input"],
        help="Upload a resume file or paste text directly"
    )
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Parse", "📊 Results", "ℹ️ Help"])
    
    with tab1:
        if parsing_mode == "📄 File Upload":
            st.markdown("### 📁 Upload Resume File")
            st.info("📋 **Supported formats:** PDF, DOC, DOCX")
            
            uploaded_file = st.file_uploader(
                "Choose your resume file",
                type=['pdf', 'doc', 'docx'],
                help="Upload your resume in PDF, DOC, or DOCX format"
            )
            
            if uploaded_file:
                # Display file info
                file_details = {
                    "Filename": uploaded_file.name,
                    "File size": f"{len(uploaded_file.getvalue())} bytes",
                    "File type": uploaded_file.type
                }
                
                col1, col2, col3 = st.columns(3)
                for i, (key, value) in enumerate(file_details.items()):
                    with [col1, col2, col3][i]:
                        st.metric(key, value)
                
                # Parse button
                if st.button("🚀 Parse Resume", type="primary", use_container_width=True):
                    try:
                        # Extract text
                        with st.spinner("📄 Extracting text from file..."):
                            extracted_text = st.session_state.parser.extract_text_from_file(uploaded_file)
                            st.session_state.extracted_text = extracted_text
                        
                        st.success("✅ Text extracted successfully!")
                        
                        # Show preview
                        with st.expander("📄 Preview Extracted Text"):
                            st.text_area(
                                "Extracted Content",
                                extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
                                height=200,
                                disabled=True
                            )
                        
                        # Parse with AI
                        with st.spinner("🤖 Parsing resume with AI..."):
                            parsed_data = st.session_state.parser.parse_resume_with_ai(extracted_text)
                            st.session_state.parsed_data = parsed_data
                        
                        if "error" not in parsed_data:
                            st.success("🎉 Resume parsed successfully!")
                            st.balloons()
                        else:
                            st.error("❌ Failed to parse resume")
                        
                    except Exception as e:
                        st.error(f"💥 Error processing file: {str(e)}")
        
        else:  # Text Input mode
            st.markdown("### ✏️ Enter Resume Text")
            
            resume_text = st.text_area(
                "Paste your resume text here:",
                height=300,
                placeholder="Copy and paste your complete resume text here...",
                help="Paste the full content of your resume for best results"
            )
            
            if st.button("🚀 Parse Text", type="primary", use_container_width=True) and resume_text.strip():
                try:
                    st.session_state.extracted_text = resume_text
                    
                    # Parse with AI
                    with st.spinner("🤖 Parsing resume with AI..."):
                        parsed_data = st.session_state.parser.parse_resume_with_ai(resume_text)
                        st.session_state.parsed_data = parsed_data
                    
                    if "error" not in parsed_data:
                        st.success("🎉 Resume parsed successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to parse resume")
                        
                except Exception as e:
                    st.error(f"💥 Error parsing text: {str(e)}")
            
            elif st.button("🚀 Parse Text", type="primary", use_container_width=True):
                st.warning("⚠️ Please enter some resume text first!")
    
    with tab2:
        if st.session_state.parsed_data:
            st.markdown("### 📊 Parsed Resume Data")
            display_parsed_results(st.session_state.parsed_data)
            
            # Download section
            if st.session_state.extracted_text:
                create_download_section(st.session_state.parsed_data, st.session_state.extracted_text)
        else:
            st.info("🔄 No data to display yet. Please upload and parse a resume first.")
    
    with tab3:
        st.markdown("""
        ### 📖 How to Use This Application
        
        **Step 1: Configure API Key**
        - Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        - Add it to your `.env` file or enter it in the sidebar
        
        **Step 2: Choose Input Method**
        - **File Upload**: Upload PDF, DOC, or DOCX files
        - **Text Input**: Paste resume text directly
        
        **Step 3: Parse Resume**
        - Click the "Parse Resume" or "Parse Text" button
        - Wait for AI processing (usually takes 10-30 seconds)
        
        **Step 4: View Results**
        - Check the "Results" tab to see structured data
        - Download JSON or text files as needed
        
        ### 🔧 Features
        - ✅ Extracts personal information
        - ✅ Parses work experience with details
        - ✅ Identifies education and certifications
        - ✅ Categorizes skills (technical, soft, languages)
        - ✅ Finds projects and achievements
        - ✅ Supports multiple file formats
        - ✅ Downloads results in JSON format
        
        ### 🚨 Troubleshooting
        - **API Error**: Check your Gemini API key
        - **File Error**: Ensure file is PDF, DOC, or DOCX
        - **Parsing Error**: Try with cleaner, well-formatted resumes
        - **Slow Processing**: Large files may take longer
        
        ### 📝 Tips for Best Results
        - Use well-formatted, standard resume layouts
        - Include clear section headings (Experience, Education, etc.)
        - Avoid heavily stylized or image-based resumes
        - Ensure text is selectable in PDF files
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
    <p>🚀 Built with ❤️ using Streamlit and Google Gemini AI</p>
    <p>🔒 Your data is processed securely and not stored</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()