import os
import streamlit as st

port = int(os.environ.get("PORT", 8080))
import streamlit as st
from PIL import Image
import io
import base64
from gtts import gTTS
import os
import tempfile
import time

# Page configuration
st.set_page_config(
    page_title="AI Vision & Voice Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark theme with animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        color: #ffffff;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #a0a0b0;
        font-size: 1.2rem;
        margin-bottom: 3rem;
    }
    
    /* Card styling */
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 2rem;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #667eea;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Input styling */
    .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
        font-size: 1rem !important;
    }
    
    .stSelectbox>div>div {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* File uploader styling */
    .stFileUploader>div>button {
        background: rgba(102, 126, 234, 0.2) !important;
        border: 2px dashed #667eea !important;
        border-radius: 12px !important;
        color: #667eea !important;
    }
    
    /* Progress bar */
    .stProgress>div>div>div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Audio player styling */
    audio {
        width: 100%;
        border-radius: 12px;
        margin-top: 1rem;
    }
    
    /* Success message */
    .success-msg {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 12px;
        padding: 1rem;
        color: #22c55e;
        text-align: center;
        margin-top: 1rem;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        text-align: center;
        color: #667eea;
        font-size: 1.2rem;
        margin: 2rem 0;
    }
    
    /* Video container */
    .video-container {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 16px;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: rgba(255, 255, 255, 0.05);
        padding: 0.5rem;
        border-radius: 16px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #a0a0b0 !important;
        font-weight: 600;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.02);
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎬 AI Vision & Voice Studio</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Transform images into videos and text into lifelike speech</p>', unsafe_allow_html=True)

# Initialize session state
if 'video_generated' not in st.session_state:
    st.session_state.video_generated = False
if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False
if 'video_description' not in st.session_state:
    st.session_state.video_description = ""

# Sidebar for API keys and settings
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")
    
    # API Key inputs (simulated for demo)
    st.text_input("🔑 OpenAI API Key", type="password", placeholder="sk-...", key="openai_key")
    st.text_input("🔑 ElevenLabs API Key", type="password", placeholder="...", key="eleven_key")
    
    st.markdown("---")
    st.markdown("### 📊 Usage Stats")
    st.metric("Videos Generated", "0")
    st.metric("Audio Clips Created", "0")
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("For best results, use high-quality images and clear text descriptions.")

# Create tabs for different sections
tab1, tab2 = st.tabs(["🎥 AI Video Generator", "🔊 Voice Synthesizer"])

# Tab 1: Image to Video
with tab1:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🖼️ Upload & Animate</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Drop your image here",
            type=['png', 'jpg', 'jpeg', 'webp'],
            help="Supported formats: PNG, JPG, JPEG, WEBP"
        )
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True, output_format="auto")
            
            # Store image in session for processing
            st.session_state.uploaded_image = image
    
    with col2:
        st.markdown("### ✨ Video Settings")
        
        video_description = st.text_area(
            "Describe the motion/animation",
            placeholder="E.g., 'Camera slowly zooms in, gentle wind moves the trees, sun sets in background...'",
            height=120
        )
        
        duration = st.slider("Duration (seconds)", 5, 30, 20)
        
        style = st.selectbox(
            "Animation Style",
            ["Cinematic", "Realistic", "Artistic", "3D Animation", "Slow Motion"]
        )
        
        quality = st.select_slider(
            "Quality",
            options=["Draft", "Standard", "High", "Ultra"],
            value="High"
        )
        
        if st.button("🎬 Generate Video", key="gen_video"):
            if uploaded_file is None:
                st.error("⚠️ Please upload an image first!")
            elif not video_description:
                st.error("⚠️ Please describe the animation!")
            else:
                # Simulate video generation process
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                stages = [
                    "Analyzing image composition...",
                    "Generating motion vectors...",
                    "Rendering frames...",
                    "Applying cinematic effects...",
                    "Finalizing video..."
                ]
                
                for i, stage in enumerate(stages):
                    status_text.markdown(f'<div class="loading">{stage}</div>', unsafe_allow_html=True)
                    progress_bar.progress((i + 1) * 20)
                    time.sleep(0.8)
                
                status_text.empty()
                progress_bar.empty()
                
                # Store description for display
                st.session_state.video_description = video_description
                st.session_state.video_generated = True
                
                st.success("✅ Video generated successfully!")
    
    # Display generated video placeholder
    if st.session_state.video_generated:
        st.markdown('<div class="video-container">', unsafe_allow_html=True)
        st.markdown("### 🎞️ Generated Video Preview")
        
        # Create a placeholder video using HTML5 video element with a demo video
        video_html = """
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 16px; background: linear-gradient(45deg, #667eea, #764ba2);">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: white;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">▶️</div>
                <div style="font-size: 1.2rem; font-weight: 600;">AI Generated Video</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">Duration: 20s | Quality: High</div>
            </div>
        </div>
        """
        st.markdown(video_html, unsafe_allow_html=True)
        
        st.markdown(f"**Description:** {st.session_state.video_description}")
        st.markdown(f"**Settings:** {style} style • {quality} quality • {duration}s duration")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.button("💾 Download MP4", key="dl_mp4")
        with col_dl2:
            st.button("🔄 Regenerate", key="regen")
        with col_dl3:
            st.button("📤 Share", key="share")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Tab 2: Text to Speech
with tab2:
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🎙️ Text to Speech</div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns([2, 1])
    
    with col3:
        text_input = st.text_area(
            "Enter your text",
            placeholder="Type or paste the text you want to convert to speech...",
            height=200,
            max_chars=5000
        )
        
        char_count = len(text_input) if text_input else 0
        st.caption(f"Character count: {char_count}/5000")
    
    with col4:
        st.markdown("### 🎛️ Voice Settings")
        
        language = st.selectbox(
            "Language",
            ["English (US)", "English (UK)", "Spanish", "French", "German", 
             "Italian", "Portuguese", "Chinese", "Japanese", "Korean", "Arabic", "Hindi"]
        )
        
        voice_gender = st.radio(
            "Voice Gender",
            ["Female", "Male"],
            horizontal=True
        )
        
        voice_style = st.select_slider(
            "Voice Style",
            options=["Natural", "Professional", "Casual", "Narrative", "Energetic"],
            value="Natural"
        )
        
        speed = st.slider("Speed", 0.5, 2.0, 1.0, 0.1)
        
        pitch = st.slider("Pitch", -10, 10, 0)
        
        if st.button("🔊 Generate Voice", key="gen_voice"):
            if not text_input:
                st.error("⚠️ Please enter some text!")
            else:
                with st.spinner("Synthesizing voice..."):
                    # Simulate processing
                    time.sleep(1.5)
                    
                    # Create TTS using gTTS (Google Text-to-Speech)
                    try:
                        lang_map = {
                            "English (US)": "en", "English (UK)": "en-uk",
                            "Spanish": "es", "French": "fr", "German": "de",
                            "Italian": "it", "Portuguese": "pt", "Chinese": "zh-cn",
                            "Japanese": "ja", "Korean": "ko", "Arabic": "ar", "Hindi": "hi"
                        }
                        
                        selected_lang = lang_map.get(language, "en")
                        
                        # Create temporary file for audio
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                            tts = gTTS(text=text_input, lang=selected_lang, slow=False)
                            tts.save(tmp_file.name)
                            tmp_file_path = tmp_file.name
                        
                        st.session_state.audio_generated = True
                        st.session_state.audio_path = tmp_file_path
                        st.session_state.audio_text = text_input
                        
                    except Exception as e:
                        st.error(f"Error generating audio: {str(e)}")
                        st.session_state.audio_generated = False
    
    # Display generated audio
    if st.session_state.get('audio_generated', False):
        st.markdown("### 🎵 Generated Audio")
        
        # Read audio file
        try:
            with open(st.session_state.audio_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            
            st.audio(audio_bytes, format='audio/mp3')
            
            col_audio1, col_audio2, col_audio3 = st.columns(3)
            with col_audio1:
                st.download_button(
                    label="💾 Download MP3",
                    data=audio_bytes,
                    file_name="generated_voice.mp3",
                    mime="audio/mp3"
                )
            with col_audio2:
                if st.button("🗑️ Clear", key="clear_audio"):
                    st.session_state.audio_generated = False
                    if os.path.exists(st.session_state.audio_path):
                        os.remove(st.session_state.audio_path)
                    st.rerun()
            with col_audio3:
                st.button("🔁 New Generation", key="new_gen")
            
            # Display transcript
            with st.expander("📄 View Transcript"):
                st.write(st.session_state.audio_text)
                
        except Exception as e:
            st.error("Error playing audio file")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Powered by Advanced AI Models • Built with Streamlit</p>
    <p style="font-size: 0.8rem;">Note: This is a demonstration app. For production use, integrate with actual AI video generation APIs.</p>
</div>
""", unsafe_allow_html=True)