import streamlit as st
import subprocess
from pathlib import Path
import re

# UI Configuration
st.set_page_config(page_title="Video Converter Pro", page_icon="🎥", layout="wide")
st.title("🎥 Video Converter Pro")
st.markdown("### Convert your videos to multiple formats and qualities")

# Constants
RESOLUTIONS = ['1920:1080', '1280:720', '854:480', '640:360']
BITRATES = ['1000k', '500k', '250k', '125k']
CODECS = {
    'h265': {
        'ext': '.mp4',
        'params': ['-c:v', 'libx265', '-preset', 'fast', '-c:a', 'aac', '-b:a', '128k']
    },
    'vp8': {
        'ext': '.webm',
        'params': ['-c:v', 'libvpx', '-c:a', 'libvorbis']
    },
    'vp9': {
        'ext': '.webm',
        'params': ['-c:v', 'libvpx-vp9', '-c:a', 'libvorbis']
    },
    'av1': {
        'ext': '.mp4',
        'params': ['-c:v', 'libaom-av1', '-strict', 'experimental']
    }
}

def validate_resolution(resolution):
    """Validate resolution format (e.g., '1920:1080')"""
    if not resolution or not isinstance(resolution, str):
        raise ValueError("Resolution must be a non-empty string")
    
    pattern = r'^\d+:\d+$'
    if not re.match(pattern, resolution):
        raise ValueError("Resolution must be in format 'width:height' (e.g., '1920:1080')")
    
    width, height = map(int, resolution.split(':'))
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive integers")
    
    return True

def validate_bitrate(bitrate):
    """Validate bitrate format (e.g., '1000k')"""
    if not bitrate or not isinstance(bitrate, str):
        raise ValueError("Bitrate must be a non-empty string")
    
    pattern = r'^\d+k$'
    if not re.match(pattern, bitrate):
        raise ValueError("Bitrate must be in format 'numberk' (e.g., '1000k')")
    
    return True

def validate_input_path(input_path):
    """Validate input path"""
    if not input_path or not isinstance(input_path, (str, Path)):
        raise ValueError("Input path must be a non-empty string or Path object")
    
    # Convert to string and check if it's just whitespace
    if isinstance(input_path, str) and not input_path.strip():
        raise ValueError("Input path cannot be empty or whitespace only")
    
    return True

def build_ffmpeg_command(input_path, output_path, codec, resolution, bitrate):
    """Build FFmpeg command with input validation"""
    # Validate inputs
    validate_input_path(input_path)
    validate_resolution(resolution)
    validate_bitrate(bitrate)
    
    if codec not in CODECS:
        raise KeyError(f"Unsupported codec: {codec}")
    
    return [
        'ffmpeg', '-i', str(input_path),
        '-vf', f'scale={resolution}',
        '-b:v', bitrate, '-y',
        *CODECS[codec]['params'],
        str(output_path)
    ]

def convert_video(input_path, codec, resolution, bitrate, is_single=True):
    """Convert video with input validation"""
    # Validate inputs
    validate_input_path(input_path)
    validate_resolution(resolution)
    validate_bitrate(bitrate)
    
    prefix = "output_single" if is_single else "output"
    output_path = f"{prefix}_{codec}_{resolution.replace(':', 'x')}_{bitrate}{CODECS[codec]['ext']}"
    
    try:
        result = subprocess.run(
            build_ffmpeg_command(input_path, output_path, codec, resolution, bitrate),
            capture_output=True, text=True, check=True
        )
        return True, output_path
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def encode_ladder(input_path, codec):
    """Generate encoding ladder with input validation"""
    validate_input_path(input_path)
    if codec not in CODECS:
        raise KeyError(f"Unsupported codec: {codec}")
    
    return [convert_video(input_path, codec, res, br, False) 
            for res, br in zip(RESOLUTIONS, BITRATES)]

# File uploader
uploaded_file = st.file_uploader("Choose a video file", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file:
    # Save uploaded file temporarily
    temp_path = Path("temp_input" + Path(uploaded_file.name).suffix)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Two columns layout
    col1, col2 = st.columns(2)
    
    # Single Conversion Column
    with col1:
        st.markdown("### Single Conversion")
        codec = st.selectbox("Select Codec", list(CODECS.keys()), key="single_codec")
        resolution = st.selectbox("Select Resolution", RESOLUTIONS, key="single_res")
        bitrate = st.selectbox("Select Bitrate", BITRATES, key="single_bitrate")
        
        if st.button("Convert Single"):
            with st.spinner("Converting..."):
                success, result = convert_video(str(temp_path), codec, resolution, bitrate)
                if success:
                    st.success(f"Conversion complete! Output saved as: {result}")
                else:
                    st.error(f"Error during conversion: {result}")
    
    # Encoding Ladder Column
    with col2:
        st.markdown("### Encoding Ladder")
        codec_ladder = st.selectbox("Select Codec", list(CODECS.keys()), key="ladder_codec")
        
        if st.button("Generate Encoding Ladder"):
            with st.spinner("Generating encoding ladder..."):
                results = encode_ladder(str(temp_path), codec_ladder)
                for success, result in results:
                    if success:
                        st.success(f"✅ Successfully created: {result}")
                    else:
                        st.error(f"❌ Error: {result}")
    
    # Cleanup
    if st.button("Clear All"):
        try:
            temp_path.unlink(missing_ok=True)
            for f in Path().glob("output_*"):
                f.unlink()
            st.success("All temporary files cleared!")
        except Exception as e:
            st.error(f"Error clearing files: {str(e)}")
else:
    st.info("👆 Upload a video file to get started!") 