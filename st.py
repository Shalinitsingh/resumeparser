import streamlit as st
import requests
import json
from io import BytesIO
import time

# Page configuration
st.set_page_config(
    page_title="Resume Parser",
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
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e7d32;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
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
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_health():
    """Check if the FastAPI backend is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_file_to_api(file):
    """Upload file to FastAPI backend"""
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{API_BASE_URL}/upload-resume", files=files, timeout=60)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error uploading file: {str(e)}")
        return None

def parse_text_with_api(text):
    """Parse text using FastAPI backend"""
    try:
        response = requests.post(f"{API_BASE_URL}/parse-text", 
                               json={"text": text}, 
                               timeout=60)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error parsing text: {str(e)}")
        return None

def display_parsed_data(data):
    """Display parsed resume data in a structured format"""
    if not data or "parsed_data" not in data:
        st.error("No parsed data available")
        return
    
    parsed = data["parsed_data"]
    
    # Personal Information
    st.markdown('<div class="section-header">👤 Personal Information</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if parsed.get("name"):
            st.write(f"**Name:** {parsed['name']}")
        if parsed.get("email"):
            st.write(f"**Email:** {parsed['email']}")
        if parsed.get("phone"):
            st.write(f"**Phone:** {parsed['phone']}")
    
    with col2:
        if parsed.get("address"):
            st.write(f"**Address:** {parsed['address']}")
        if parsed.get("linkedin"):
            st.write(f"**LinkedIn:** {parsed['linkedin']}")
        if parsed.get("github"):
            st.write(f"**GitHub:** {parsed['github']}")
    
    # Professional Summary
    if parsed.get("summary"):
        st.markdown('<div class="section-header">📝 Professional Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box">{parsed["summary"]}</div>', unsafe_allow_html=True)
    
    # Work Experience
    if parsed.get("experience"):
        st.markdown('<div class="section-header">💼 Work Experience</div>', unsafe_allow_html=True)
        for i, exp in enumerate(parsed["experience"], 1):
            with st.expander(f"Experience {i}: {exp.get('company', 'Unknown Company')}"):
                if exp.get("position"):
                    st.write(f"**Position:** {exp['position']}")
                if exp.get("duration"):
                    st.write(f"**Duration:** {exp['duration']}")
                if exp.get("description"):
                    st.write(f"**Description:** {exp['description']}")
    
    # Education
    if parsed.get("education"):
        st.markdown('<div class="section-header">🎓 Education</div>', unsafe_allow_html=True)
        for i, edu in enumerate(parsed["education"], 1):
            with st.expander(f"Education {i}: {edu.get('institution', 'Unknown Institution')}"):
                if edu.get("degree"):
                    st.write(f"**Degree:** {edu['degree']}")
                if edu.get("year"):
                    st.write(f"**Year:** {edu['year']}")
                if edu.get("gpa"):
                    st.write(f"**GPA:** {edu['gpa']}")
    
    # Skills
    if parsed.get("skills"):
        st.markdown('<div class="section-header">🔧 Skills</div>', unsafe_allow_html=True)
        skills_text = ", ".join(parsed["skills"]) if isinstance(parsed["skills"], list) else str(parsed["skills"])
        st.markdown(f'<div class="info-box">{skills_text}</div>', unsafe_allow_html=True)
    
    # Certifications
    if parsed.get("certifications"):
        st.markdown('<div class="section-header">🏆 Certifications</div>', unsafe_allow_html=True)
        for cert in parsed["certifications"]:
            st.write(f"• {cert}")
    
    # Projects
    if parsed.get("projects"):
        st.markdown('<div class="section-header">🚀 Projects</div>', unsafe_allow_html=True)
        for i, project in enumerate(parsed["projects"], 1):
            with st.expander(f"Project {i}: {project.get('name', 'Unknown Project')}"):
                if project.get("description"):
                    st.write(f"**Description:** {project['description']}")
                if project.get("technologies"):
                    tech_text = ", ".join(project["technologies"]) if isinstance(project["technologies"], list) else str(project["technologies"])
                    st.write(f"**Technologies:** {tech_text}")

def display_raw_json(data):
    """Display raw JSON data"""
    st.json(data)

def main():
    # Header
    st.markdown('<div class="main-header">📄 AI-Powered Resume Parser</div>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.markdown('''
        <div class="error-box">
        ❌ <strong>Backend API is not running!</strong><br>
        Please start the FastAPI server by running: <code>uvicorn main:app --reload</code>
        </div>
        ''', unsafe_allow_html=True)
        st.stop()
    else:
        st.markdown('''
        <div class="success-box">
        ✅ <strong>Backend API is running successfully!</strong>
        </div>
        ''', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    st.sidebar.info("Make sure you have set your GEMINI_API_KEY in the .env file")
    
    parsing_mode = st.sidebar.radio(
        "Choose parsing mode:",
        ["📄 File Upload", "✏️ Text Input"]
    )
    
    display_mode = st.sidebar.radio(
        "Display format:",
        ["🎯 Structured View", "📋 Raw JSON"]
    )
    
    # Main content area
    if parsing_mode == "📄 File Upload":
        st.markdown("### Upload Resume File")
        st.info("Supported formats: PDF, DOC, DOCX")
        
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'doc', 'docx'],
            help="Upload your resume in PDF or DOC format"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**File size:** {len(uploaded_file.getvalue())} bytes")
            
            if st.button("🚀 Parse Resume", type="primary"):
                with st.spinner("Parsing resume... This may take a few seconds."):
                    result = upload_file_to_api(uploaded_file)
                    
                    if result:
                        st.success("✅ Resume parsed successfully!")
                        
                        # Store result in session state
                        st.session_state.parsing_result = result
                        
                        # Show extracted text preview
                        if "extracted_text" in result:
                            with st.expander("📄 Extracted Text Preview"):
                                st.text_area("Text Content", result["extracted_text"], height=150, disabled=True)
                        
                        # Display results based on selected mode
                        if display_mode == "🎯 Structured View":
                            display_parsed_data(result)
                        else:
                            display_raw_json(result)
                    else:
                        st.error("❌ Failed to parse resume. Please try again.")
    
    else:  # Text Input mode
        st.markdown("### Enter Resume Text")
        
        resume_text = st.text_area(
            "Paste your resume text here:",
            height=300,
            placeholder="Copy and paste your resume text here..."
        )
        
        if st.button("🚀 Parse Text", type="primary") and resume_text:
            with st.spinner("Parsing resume text... This may take a few seconds."):
                result = parse_text_with_api(resume_text)
                
                if result:
                    st.success("✅ Resume text parsed successfully!")
                    
                    # Store result in session state
                    st.session_state.parsing_result = resultuvicorn main:app --reload --host 0.0.0.0 --port 8000
                    
                    # Display results based on selected mode
                    if display_mode == "🎯 Structured View":
                        display_parsed_data(result)
                    else:
                        display_raw_json(result)
                else:
                    st.error("❌ Failed to parse resume text. Please try again.")
    
    # Download results feature
    if hasattr(st.session_state, 'parsing_result') and st.session_state.parsing_result:
        st.markdown("---")
        st.markdown("### 📥 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Download as JSON"):
                json_data = json.dumps(st.session_state.parsing_result, indent=2)
                st.download_button(
                    label="📄 Download JSON File",
                    data=json_data,
                    file_name="parsed_resume.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📋 Copy to Clipboard"):
                json_data = json.dumps(st.session_state.parsing_result, indent=2)
                st.code(json_data, language="json")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
    <p>Built with ❤️ using Streamlit, FastAPI, and Google Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()