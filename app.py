import streamlit as st
import openai
import os
import re
from typing import Dict

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
        padding: 1.5rem;
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
    .stButton > button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
</style>
""", unsafe_allow_html=True)

def get_writing_prompts():
    """Define prompts and personas for different writing types"""
    return {
        "Discussion Post": {
            "persona": "You are Nova, an AI writing coach specializing in online discussion facilitation. You help students create engaging, thoughtful discussion posts that demonstrate critical thinking and encourage peer dialogue.",
            "prompt_template": """Analyze this discussion post focusing on:
1. **Engagement**: Does it invite response and build on the prompt?
2. **Critical Thinking**: Are claims supported with reasoning or evidence?
3. **Peer Connection**: Does it reference course materials or invite dialogue?
4. **Clarity**: Is the main point clear and well-organized?

Provide 2-3 specific, actionable suggestions and ask 1-2 Socratic questions that help the student deepen their analysis."""
        },
        
        "Learning Journal": {
            "persona": "You are Nova, an AI writing coach who specializes in reflective writing. You help students develop metacognitive awareness and connect personal experiences to academic learning.",
            "prompt_template": """Analyze this learning journal entry focusing on:
1. **Reflection Depth**: Does it go beyond summary to analyze learning?
2. **Personal Connection**: How well does it connect experience to concepts?
3. **Metacognition**: Does it show awareness of the learning process?
4. **Growth Mindset**: Does it identify specific areas for development?

Provide encouraging feedback with 2-3 suggestions for deepening reflection, and ask 1-2 questions that help them explore their learning further."""
        },
        
        "Academic Paper": {
            "persona": "You are Nova, an AI writing coach specializing in academic writing. You help students develop clear arguments, integrate sources effectively, and write with scholarly precision.",
            "prompt_template": """Analyze this academic writing focusing on:
1. **Argument Structure**: Is there a clear thesis with logical support?
2. **Evidence Integration**: Are sources used effectively to support claims?
3. **Academic Voice**: Is the tone appropriate for scholarly writing?
4. **Organization**: Do ideas flow logically with clear transitions?

Provide specific feedback on strengthening the argument and ask 1-2 questions that help the student think critically about their evidence and reasoning."""
        },
        
        "Thesis Statement": {
            "persona": "You are Nova, an AI writing coach who specializes in helping students craft strong thesis statements. You focus on arguability, specificity, and clarity.",
            "prompt_template": """Analyze this thesis statement focusing on:
1. **Arguability**: Does it present a debatable claim rather than fact?
2. **Specificity**: Is it focused enough to be supported in the paper?
3. **Clarity**: Is the main argument immediately clear to readers?
4. **Scope**: Is it appropriately sized for the assignment?

Provide specific suggestions for strengthening the thesis and ask 1-2 questions that help the student refine their central argument."""
        }
    }

def detect_citations(text: str) -> Dict:
    """Basic citation detection and analysis"""
    apa_pattern = r'\([A-Za-z]+(?:,\s*[A-Za-z]+)*,\s*\d{4}\)'
    mla_pattern = r'\([A-Za-z]+\s+\d+\)'
    url_pattern = r'https?://[^\s]+'
    
    apa_citations = re.findall(apa_pattern, text)
    mla_citations = re.findall(mla_pattern, text)
    urls = re.findall(url_pattern, text)
    
    has_recent_sources = any('202' in citation for citation in apa_citations)
    
    return {
        "apa_count": len(apa_citations),
        "mla_count": len(mla_citations),
        "url_count": len(urls),
        "has_recent_sources": has_recent_sources,
        "total_citations": len(apa_citations) + len(mla_citations)
    }

def get_ai_feedback(text: str, writing_type: str) -> str:
    """Get tailored feedback based on writing type"""
    prompts = get_writing_prompts()
    
    if writing_type not in prompts:
        writing_type = "Academic Paper"  # Default fallback
    
    persona = prompts[writing_type]["persona"]
    prompt_template = prompts[writing_type]["prompt_template"]
    
    # Add citation context if citations are detected
    citation_data = detect_citations(text)
    citation_context = ""
    if citation_data["total_citations"] > 0:
        citation_context = f"\n\nNote: I detected {citation_data['total_citations']} citations in this text. Consider how well these sources are integrated into the argument."
    
    full_prompt = f"{prompt_template}{citation_context}\n\nKeep your response under 300 words, be encouraging but specific, and focus on the most important improvements."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": persona},
                {"role": "user", "content": f"Here is the student's {writing_type.lower()}:\n\n{text}\n\n{full_prompt}"}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        return response["choices"][0]["message"]["content"]
        
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return f"I'm having trouble connecting to provide feedback right now. Please check your API key and try again."

# Main App Interface
st.markdown('<div class="main-header"><h1>✍️ Nova: AI Writing Coach</h1><p>Get personalized feedback for your academic writing</p></div>', unsafe_allow_html=True)

# Input Section
st.markdown("### 📝 Your Writing")
user_input = st.text_area(
    "Paste your text below:",
    height=250,
    help="Paste your discussion post, journal entry, paper draft, or thesis statement",
    placeholder="Enter your writing here..."
)

# Writing Type Selection
st.markdown("### 🎯 Type of Writing")
col1, col2 = st.columns(2)

with col1:
    writing_type = st.selectbox(
        "What type of writing is this?",
        [
            "Discussion Post",
            "Learning Journal", 
            "Academic Paper",
            "Thesis Statement"
        ],
        help="Choose the type that best matches your assignment"
    )

with col2:
    # Optional context
    additional_context = st.text_input(
        "Assignment context (optional):",
        placeholder="e.g., 'for Psychology 101' or 'arguing about climate policy'",
        help="Any additional context about your assignment"
    )

# Get Feedback Button
st.markdown("### 🔍 Analysis")
if st.button("Get Nova's Feedback", type="primary"):
    if not user_input.strip():
        st.warning("⚠️ Please enter some text to analyze.")
    elif not os.environ.get("OPENAI_API_KEY"):
        st.error("❌ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    else:
        with st.spinner(f"🤔 Nova is analyzing your {writing_type.lower()}..."):
            
            # Get AI feedback
            feedback = get_ai_feedback(user_input, writing_type)
            
            # Display results
            st.markdown("---")
            
            # Main feedback section
            st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
            st.markdown(f"## 💡 Feedback for your {writing_type}")
            
            # Add context if provided
            if additional_context:
                st.markdown(f"*Context: {additional_context}*")
            
            st.markdown(feedback)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Citation analysis if applicable
            citation_data = detect_citations(user_input)
            if writing_type in ["Academic Paper", "Thesis Statement"] and citation_data["total_citations"] > 0:
                st.markdown('<div class="citation-alert">', unsafe_allow_html=True)
                st.markdown("### 📚 Citation Summary")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Citations Found", citation_data['total_citations'])
                with col2:
                    st.metric("URLs", citation_data['url_count'])
                with col3:
                    recent_text = "✓" if citation_data['has_recent_sources'] else "Check dates"
                    st.metric("Recent Sources", recent_text)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Next steps
            st.markdown('<div class="strength-highlight">', unsafe_allow_html=True)
            st.markdown("### 🚀 Next Steps")
            
            if writing_type == "Discussion Post":
                st.markdown("- **Post and engage**: Share your post and respond thoughtfully to peers\n- **Return later**: Bring back revised drafts for additional feedback")
            elif writing_type == "Learning Journal":
                st.markdown("- **Reflect deeper**: Consider the questions Nova asked\n- **Connect more**: Link to additional course concepts or experiences")
            elif writing_type == "Academic Paper":
                st.markdown("- **Revise**: Address the feedback points Nova identified\n- **Peer review**: Share with classmates or visit the writing center")
            else:  # Thesis Statement
                st.markdown("- **Refine**: Revise your thesis based on Nova's suggestions\n- **Expand**: Use your improved thesis to guide your full paper")
            
            st.markdown('</div>', unsafe_allow_html=True)

# Help section
with st.expander("❓ How to use Nova effectively"):
    st.markdown("""
    **For best results:**
    - **Be specific** about your assignment context
    - **Include complete thoughts** rather than fragments
    - **Try multiple drafts** - Nova can help you improve iteratively
    - **Focus on one piece** at a time for clearer feedback
    
    **Writing type guide:**
    - **Discussion Post**: Forum responses, online discussions
    - **Learning Journal**: Reflection essays, process writing  
    - **Academic Paper**: Research papers, essays, reports
    - **Thesis Statement**: Just your main argument/claim
    """)

# Footer
st.markdown("---")
st.markdown("*Nova AI Writing Coach - Supporting academic writing development*")
