import streamlit as st
import openai
import os
import re
from typing import List, Dict
import json

# Configure OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Configure Streamlit for iframe embedding
st.set_page_config(
    page_title="Nova: AI Writing Coach",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for iframe embedding and accessibility
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e6da4 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .feedback-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
    .question-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #1976d2;
    }
    .citation-alert {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #ffc107;
    }
    .strength-highlight {
        background: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    /* Accessibility improvements */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    /* Ensure good contrast for screen readers */
    .stSelectbox label, .stTextArea label {
        font-weight: 600;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

def detect_citations(text: str) -> Dict:
    """Basic citation detection and analysis"""
    # Look for common citation patterns
    apa_pattern = r'\([A-Za-z]+(?:,\s*[A-Za-z]+)*,\s*\d{4}\)'
    mla_pattern = r'\([A-Za-z]+\s+\d+\)'
    url_pattern = r'https?://[^\s]+'
    
    apa_citations = re.findall(apa_pattern, text)
    mla_citations = re.findall(mla_pattern, text)
    urls = re.findall(url_pattern, text)
    
    # Simple heuristics for citation quality
    has_recent_sources = any('202' in citation for citation in apa_citations)
    citation_density = (len(apa_citations) + len(mla_citations)) / max(len(text.split()), 1) * 1000
    
    return {
        "apa_count": len(apa_citations),
        "mla_count": len(mla_citations),
        "url_count": len(urls),
        "has_recent_sources": has_recent_sources,
        "citation_density": citation_density,
        "total_citations": len(apa_citations) + len(mla_citations)
    }

def generate_socratic_questions(text: str, focus_area: str) -> str:
    """Generate Socratic questions based on the text and focus area"""
    
    system_prompt = f"""You are Nova, an AI writing coach that uses Socratic questioning to guide students to insights about their own writing. 

Your role is to ask 3-4 thoughtful questions that help the student discover areas for improvement in their writing, specifically focusing on {focus_area}.

Guidelines:
- Ask questions that lead students to self-discovery rather than giving direct answers
- Use "What if..." "How might..." "Why do you think..." question starters
- Make questions specific to their actual text
- Focus on helping them think critically about their choices
- Keep questions accessible but intellectually engaging
- End with one question that pushes them to consider their audience/purpose

Return your response as a JSON object with this structure:
{{
    "questions": [
        {{"question": "Your question here", "purpose": "Brief explanation of what this question helps them discover"}},
        // 2-3 more questions
    ],
    "reflection_prompt": "A final broader question about their writing goals"
}}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the student's writing:\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return json.dumps({
            "questions": [
                {"question": "What is the main argument you're trying to make in this piece?", "purpose": "Helps identify thesis clarity"},
                {"question": "Who is your intended audience and how does that shape your word choices?", "purpose": "Develops audience awareness"},
                {"question": "What evidence best supports your strongest point?", "purpose": "Encourages critical evaluation of support"}
            ],
            "reflection_prompt": "How well does this piece achieve what you set out to accomplish?"
        })

def analyze_citations_with_ai(text: str, citation_data: Dict) -> str:
    """AI analysis of citation quality and integration"""
    
    system_prompt = """You are Nova, an AI writing coach specializing in research and citation analysis. Analyze the student's use of sources and citations.

Focus on:
- Integration of sources into arguments (not just citation format)
- Variety and credibility of sources
- How well sources support the argument
- Opportunities for stronger evidence

Provide specific, actionable feedback in a supportive tone. If you see citation attempts, acknowledge the effort while suggesting improvements.

Keep response under 200 words and be encouraging but honest."""

    citation_context = f"""
    Citation Analysis:
    - Total citations found: {citation_data['total_citations']}
    - APA style citations: {citation_data['apa_count']}
    - MLA style citations: {citation_data['mla_count']}
    - URLs found: {citation_data['url_count']}
    - Recent sources detected: {citation_data['has_recent_sources']}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{citation_context}\n\nStudent's text:\n{text}"}
            ],
            temperature=0.6,
            max_tokens=300
        )
        
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return "I notice you're working on incorporating sources into your writing. Consider how each source specifically supports your main argument and whether you're explaining the connection clearly for your readers."

# Main App Interface
st.markdown('<div class="main-header"><h1>✍️ Nova: AI Writing Coach</h1><p>Discover insights about your writing through guided reflection</p></div>', unsafe_allow_html=True)

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

# Input Section
col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_area(
        "📝 Paste your draft below:",
        height=200,
        help="Paste your thesis, paragraph, or essay draft for analysis",
        placeholder="Enter your writing here..."
    )

with col2:
    st.markdown("### 🎯 Focus Area")
    focus = st.selectbox(
        "What aspect would you like to explore?",
        [
            "Argument Development",
            "Evidence & Citations", 
            "Clarity & Organization",
            "Audience Awareness",
            "Critical Thinking"
        ],
        help="Choose the area you'd like to focus on for guided questions"
    )
    
    writing_type = st.selectbox(
        "Type of writing:",
        [
            "Academic Essay",
            "Research Paper", 
            "Thesis/Dissertation",
            "Lab Report",
            "Reflection Paper"
        ]
    )

# Analysis Button
if st.button("🔍 Start Guided Analysis", type="primary"):
    if user_input.strip() == "":
        st.warning("⚠️ Please enter some text to analyze.")
    else:
        with st.spinner("🤔 Nova is preparing thoughtful questions about your writing..."):
            
            # Analyze citations
            citation_data = detect_citations(user_input)
            
            # Generate Socratic questions
            questions_response = generate_socratic_questions(user_input, focus)
            
            # Analyze citations with AI
            citation_feedback = analyze_citations_with_ai(user_input, citation_data)
            
            st.session_state.analysis_complete = True
            st.session_state.questions_data = questions_response
            st.session_state.citation_feedback = citation_feedback
            st.session_state.citation_data = citation_data

# Display Results
if st.session_state.analysis_complete:
    
    # Parse questions data
    try:
        questions_json = json.loads(st.session_state.questions_data)
        questions = questions_json.get("questions", [])
        reflection_prompt = questions_json.get("reflection_prompt", "")
    except:
        # Fallback if JSON parsing fails
        questions = [
            {"question": "What is the strongest part of your argument and why?", "purpose": "Identifies areas of strength"},
            {"question": "Where might readers need more explanation or evidence?", "purpose": "Highlights gaps in support"},
            {"question": "How does this piece serve your reader's needs?", "purpose": "Develops audience awareness"}
        ]
        reflection_prompt = "What would you change if you were writing this for a different audience?"
    
    st.markdown("---")
    
    # Socratic Questions Section
    st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
    st.markdown("## 🤔 Questions to Guide Your Thinking")
    st.markdown("*Take a moment to consider each question. There are no 'wrong' answers—these are meant to help you discover insights about your own writing.*")
    
    for i, q in enumerate(questions, 1):
        st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"**Question {i}:** {q['question']}")
        st.markdown(f"*This question helps you: {q['purpose']}*")
        
        # Student response area
        response_key = f"response_{i}"
        st.text_area(
            f"Your thoughts on Question {i}:",
            key=response_key,
            height=80,
            placeholder="Reflect on this question... there's no right or wrong answer."
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Reflection prompt
    if reflection_prompt:
        st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"**Final Reflection:** {reflection_prompt}")
        st.text_area(
            "Your reflection:",
            key="final_reflection",
            height=100,
            placeholder="Consider your overall goals and audience..."
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Citation Analysis Section
    st.markdown('<div class="citation-alert">', unsafe_allow_html=True)
    st.markdown("## 📚 Research & Citation Insights")
    
    # Citation statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Citations Found", st.session_state.citation_data['total_citations'])
    with col2:
        st.metric("URLs Detected", st.session_state.citation_data['url_count'])
    with col3:
        recent_text = "Yes" if st.session_state.citation_data['has_recent_sources'] else "Check dates"
        st.metric("Recent Sources", recent_text)
    
    # AI citation feedback
    st.markdown("### 💡 Research Integration Feedback")
    st.markdown(st.session_state.citation_feedback)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Next Steps
    st.markdown('<div class="strength-highlight">', unsafe_allow_html=True)
    st.markdown("## 🚀 Next Steps")
    st.markdown("""
    **After reflecting on these questions:**
    1. **Revise** based on your insights from the questions above
    2. **Strengthen** your research integration using the citation feedback
    3. **Share** your draft with a peer or instructor for additional perspective
    4. **Return** to Nova with your revised draft for another round of guided analysis
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Reset button
    if st.button("📝 Analyze New Text"):
        st.session_state.analysis_complete = False
        st.rerun()

# Footer for iframe context
st.markdown("---")
st.markdown("*Nova AI Writing Coach - Designed for academic writing development*")
