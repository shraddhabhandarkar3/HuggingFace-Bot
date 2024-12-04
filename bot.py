import openai
import streamlit as st
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
serpapi_key = os.getenv("SERPAPI_KEY")  # SERPAPI API Key

# SERPAPI Function for Fetching Sources
def fetch_improved_sources(query):
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "engine": "google",
            "api_key": serpapi_key,
            "num": 5,
            "tbm": "vid"  # For video results
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json()
            articles = results.get("organic_results", [])[:3]
            videos = results.get("video_results", [])[:2]
            
            sources = {
                "articles": [{"title": a["title"], "link": a["link"]} for a in articles],
                "videos": [{"title": v["title"], "link": v["link"]} for v in videos]
            }
            
            return sources
        return None
    except Exception as e:
        return None
    
def process_uploaded_file(file):
    try:
        from transformers import pipeline
        import PyPDF2
        import io
        import docx
        
        # Initialize QA pipeline
        qa_pipeline = pipeline(
            "question-answering",
            model="deepset/roberta-base-squad2",
            tokenizer="deepset/roberta-base-squad2"
        )
        
        content = ""
        # Handle different file types
        if file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page in pdf_reader.pages:
                content += page.extract_text()
                
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(file.read()))
            for para in doc.paragraphs:
                content += para.text + "\n"
                
        elif file.type == "text/plain":
            content = file.getvalue().decode('utf-8', errors='ignore')
        
        else:
            return "Unsupported file format. Please upload PDF, DOCX, or TXT files."
        
        if not content.strip():
            return "No text content could be extracted from the file."
            
        # Generate multiple relevant questions for comprehensive analysis
        questions = [
            "What are the main findings or diagnoses?",
            "What are the key recommendations?",
            "Are there any specific medications or treatments mentioned?",
            "What are the important test results or values?"
        ]
        
        # Get answers for each question
        analysis = []
        for question in questions:
            try:
                result = qa_pipeline(
                    question=question,
                    context=content[:4096],  # Limit context length to prevent token overflow
                    max_answer_length=100
                )
                if result['score'] > 0.1:  # Only include confident answers
                    analysis.append(f"{question}\n{result['answer']}")
            except Exception as e:
                continue
                
        if not analysis:
            return "Could not extract meaningful information from the document."
            
        return "\n\n".join(analysis)
        
    except Exception as e:
        return f"Error processing file: {str(e)}"

def handle_file_upload(file):
    """Wrapper function to handle file upload and processing"""
    try:
        if file is None:
            return None
            
        # Check file size
        if file.size > 200 * 1024 * 1024:  # 200MB limit
            return "File too large. Please upload a file smaller than 200MB."
            
        # Check file type
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        ]
        if file.type not in allowed_types:
            return "Invalid file type. Please upload PDF, DOCX, or TXT files."
            
        # Process file
        with st.spinner("Analyzing document..."):
            analysis = process_uploaded_file(file)
            return analysis
            
    except Exception as e:
        return f"Error handling file: {str(e)}"

def fetch_improved_sources(query):
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "engine": "google",
            "api_key": serpapi_key,
            "num": 5,
            "tbm": "vid"  # For video results
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json()
            articles = results.get("organic_results", [])[:3]
            videos = results.get("video_results", [])[:2]
            
            sources = {
                "articles": [{"title": a["title"], "link": a["link"]} for a in articles],
                "videos": [{"title": v["title"], "link": v["link"]} for v in videos]
            }
            
            return sources
        return None
    except Exception as e:
        return None

# OpenAI Chat Function
def chat_with_openai(query, conversation_history):
    try:
        messages = [{"role": "system", "content": "You are a helpful Health and Wellness Coach. Always provide detailed responses and ask relevant follow-up questions."}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": query})
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        reply = response.choices[0].message["content"]
        return reply, conversation_history
    except Exception as e:
        return f"Error: {str(e)}", conversation_history
    
def generate_quiz(conversation):
    quiz_questions = []
    topics = []
    
    for message in conversation:
        if message['role'] == 'assistant':
            content = message['content']
            # Extract key points from bot responses
            topics.append(content)
    
    # Generate questions based on topics
    for topic in topics:
        question = {
            'question': f"Based on our discussion: {topic[:100]}...",
            'options': ['True', 'False'],
            'correct_answer': 'True'
        }
        quiz_questions.append(question)
    
    return quiz_questions

def display_quiz():
    if len(st.session_state["conversation"]) > 0:
        quiz = generate_quiz(st.session_state["conversation"])
        st.subheader("Knowledge Check Quiz")
        score = 0
        for i, q in enumerate(quiz):
            user_answer = st.radio(q['question'], q['options'], key=f"quiz_{i}")
            if user_answer == q['correct_answer']:
                score += 1
        if st.button("Submit Quiz"):
            st.success(f"Your score: {score}/{len(quiz)}")

# Streamlit Page Configuration
import streamlit as st

# Streamlit Page Configuration
st.set_page_config(page_title="Health Coach", layout="wide")

# Custom CSS
st.markdown("""
<style>
    /* Base styles */
    .stApp {
        background-color: #0E1117 !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-18ni7ap {
        background-color: transparent !important;
    }
    
    /* Main container */
    .main-content {
        position: fixed;
        top: 0;
        right: 0;
        width: calc(100% - 250px);
        height: 100vh;
        display: flex;
        flex-direction: column;
        background-color: #343541;
    }
    
    /* Chat container */
    .chat-container {
        position: fixed;
        top: 0;
        right: 0;
        width: calc(100% - 250px);
        height: calc(100vh - 180px);
        overflow-y: auto;
        padding: 20px;
        margin-bottom: 180px;
        background-color: #343541;
    }
    
    /* Message styling */
    .user-message, .bot-message {
        padding: 24px;
        width: 100%;
    }
    
    .user-message {
        background-color: #343541;
    }
    
    .bot-message {
        background-color: #444654;
    }
    
    .message-inner {
        display: flex;
        align-items: flex-start;
        max-width: 800px;
        margin: 0 auto;
        gap: 15px;
    }
    
    .message-content {
        color: #ECECF1;
        font-size: 16px;
        line-height: 1.5;
        width: 100%;
    }
    .avatar {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        padding: 3px;
        background-color: #FFFFFF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Ensure proper message container styling */
    .message-inner {
        display: flex;
        align-items: flex-start;
        max-width: 800px;
        margin: 0 auto;
        gap: 15px;
        background: transparent;
    }
    /* Input area */
    .input-area {
        position: fixed;
        bottom: 0;
        right: 0;
        width: calc(100% - 250px);
        background-color: #343541;
        padding: 20px;
        border-top: 1px solid rgba(255,255,255,0.1);
        z-index: 1000;
    }
    
    /* File upload styling */
    .upload-container {
        background-color: #40414F;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px dashed rgba(255,255,255,0.2);
    }
    
    /* Resources styling */
    .resources-section {
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    .resource-link {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        color: #66B2FF;
        text-decoration: none;
    }
    
    .resource-icon {
        width: 20px;
        height: 20px;
    }
    
    /* Input styling */
    .stTextInput input {
        background-color: #40414F !important;
        border: none !important;
        color: white !important;
        padding: 12px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
    }
            
    /* Resource link styling */
    .message-content a {
        color: #66B2FF;
        text-decoration: none;
        display: block;
        margin: 5px 0;
        padding: 5px 0;
    }

    .message-content a:hover {
        text-decoration: underline;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #40414F !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
    }
    
    /* Hide Streamlit components */
    #MainMenu, footer, .stDeployButton {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Health Coach")
    st.markdown("### Chat History")
    
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    # New Chat button
    if st.button("New Chat"):
        st.session_state["conversation"] = []
        st.rerun()
    
    # Display saved chats
    for i, chat in enumerate(st.session_state["chat_history"]):
        if st.button(f"Chat {i+1}: {chat['title']}", key=f"chat_{i}"):
            st.session_state["conversation"] = chat["conversation"]
            st.rerun()

# Main Chat Interface
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Chat Container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Initialize conversation state
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Display Messages
# Display Messages
for message in st.session_state["conversation"]:
    if message["role"] == "user":
        st.markdown(f"""
            <div class="user-message">
                <div class="message-inner">
                    <img class="avatar" src="https://img.icons8.com/ios-filled/50/ffffff/user-circle.png">
                    <div class="message-content">{message['content']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        content = message['content']
        if 'sources' in message:
            sources = message['sources']
            if sources:
                content += "\n\nRelevant Resources:\n"
                for article in sources.get("articles", []):
                    content += f'\n<a href="{article["link"]}" target="_blank">• {article["title"]}</a>'
                for video in sources.get("videos", []):
                    content += f'\n<a href="{video["link"]}" target="_blank">📺 {video["title"]}</a>'
        
        st.markdown(f"""
            <div class="bot-message">
                <div class="message-inner">
                    <img class="avatar" src="https://img.icons8.com/ios-filled/50/ffffff/bot.png">
                    <div class="message-content">{content}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Fixed Input Area
st.markdown('<div class="input-area">', unsafe_allow_html=True)

# File Upload
st.markdown('<div class="upload-container">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload medical reports or articles",
    type=['txt', 'pdf', 'docx'],
    help="Limit 200MB per file • TXT, PDF, DOCX"
)
st.markdown('</div>', unsafe_allow_html=True)

# Message Input
cols = st.columns([8, 1])
with cols[0]:
    query = st.text_input("Type your message...", 
                         key=f"query_input_{len(st.session_state.get('conversation', []))}")
with cols[1]:
    send_button = st.button("Send", 
                           key=f"send_button_{len(st.session_state.get('conversation', []))}")

st.markdown('</div></div>', unsafe_allow_html=True)

def generate_resources_html(sources):
    if not sources:
        return ""
    
    html = '<div class="resources-section"><h4>Relevant Resources:</h4>'
    
    icons = {
        'youtube.com': 'https://img.icons8.com/color/48/000000/youtube-play.png',
        'facebook.com': 'https://img.icons8.com/color/48/000000/facebook-new.png',
        'twitter.com': 'https://img.icons8.com/color/48/000000/twitter.png',
        'default': 'https://img.icons8.com/ios-filled/50/000000/link.png'
    }
    
    for article in sources.get("articles", []):
        icon_url = next((icon for domain, icon in icons.items() if domain in article["link"]), icons['default'])
        html += f"""
            <a href="{article['link']}" target="_blank" class="resource-link">
                <img class="resource-icon" src="{icon_url}">
                {article['title']}
            </a>
        """
    
    for video in sources.get("videos", []):
        html += f"""
            <a href="{video['link']}" target="_blank" class="resource-link">
                <img class="resource-icon" src="{icons['youtube.com']}">
                {video['title']}
            </a>
        """
    
    html += '</div>'
    return html

# Message handling
if send_button and query.strip():
    st.session_state["conversation"].append({"role": "user", "content": query})
    
    with st.spinner("Thinking..."):
        bot_reply, _ = chat_with_openai(query, st.session_state["conversation"])
        sources = fetch_improved_sources(query)
        
        st.session_state["conversation"].append({
            "role": "assistant", 
            "content": bot_reply,
            "sources": sources
        })
    st.rerun()

# Save Chat Button
if len(st.session_state.get("conversation", [])) > 0:
    if st.button("Save Chat", key="save_chat"):
        first_message = st.session_state["conversation"][0]["content"]
        chat_title = first_message[:20] + "..."
        st.session_state["chat_history"].append({
            "title": chat_title,
            "conversation": st.session_state["conversation"]
        })
        st.success("Chat saved!")