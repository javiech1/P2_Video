import streamlit as st
import subprocess
import os
from pathlib import Path

st.set_page_config(
    page_title="Video Converter Pro",
    page_icon="🎥",
    layout="wide"
)

st.title("🎥 Video Converter Pro")
st.markdown("### Convert your videos to multiple formats and qualities")

def encode_ladder(input_path, codec="h265", resolutions=None, bitrates=None):
    if resolutions is None:
        resolutions = ['1920:1080', '1280:720', '854:480', '640:360']
    if bitrates is None:
        bitrates = ['1000k', '500k', '250k', '125k']
    
    ext = '.mp4' if codec in ['h265', 'av1'] else '.webm'
    results = []

    for resolution, bitrate in zip(resolutions, bitrates):
        output_path = f"output_{codec}_{resolution.replace(':', 'x')}_{bitrate}.{ext.lstrip('.')}"
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f'scale={resolution}',
            '-b:v', bitrate,
            '-y'
        ]
        if codec == 'h265':
            cmd.extend([
                '-c:v', 'libx265',
                '-preset', 'fast',
                '-c:a', 'aac',
                '-b:a', '128k'
            ])
        elif codec == 'vp8':
            cmd.extend([
                '-c:v', 'libvpx',
                '-c:a', 'libvorbis'
            ])
        elif codec == 'vp9':
            cmd.extend([
                '-c:v', 'libvpx-vp9',
                '-c:a', 'libvorbis'
            ])
        elif codec == 'av1':
            cmd.extend([
                '-c:v', 'libaom-av1',
                '-strict', 'experimental'
            ])
        cmd.append(output_path)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            results.append(f"✅ Successfully created: {output_path}")
        except subprocess.CalledProcessError as e:
            results.append(f"❌ Error creating {output_path}: {e.stderr}")
    return results

def convert_single(input_path, codec, resolution, bitrate):
    ext = '.mp4' if codec in ['h265', 'av1'] else '.webm'
    output_path = f"output_single_{codec}_{resolution.replace(':', 'x')}_{bitrate}.{ext.lstrip('.')}"
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', f'scale={resolution}',
        '-b:v', bitrate,
        '-y'
    ]
    
    if codec == 'h265':
        cmd.extend([
            '-c:v', 'libx265',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '128k'
        ])
    elif codec == 'vp8':
        cmd.extend([
            '-c:v', 'libvpx',
            '-c:a', 'libvorbis'
        ])
    elif codec == 'vp9':
        cmd.extend([
            '-c:v', 'libvpx-vp9',
            '-c:a', 'libvorbis'
        ])
    elif codec == 'av1':
        cmd.extend([
            '-c:v', 'libaom-av1',
            '-strict', 'experimental'
        ])
    
    cmd.append(output_path)
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return output_path

# File uploader
uploaded_file = st.file_uploader("Choose a video file", type=['mp4', 'mov', 'avi', 'mkv'])

if uploaded_file is not None:
    # Save uploaded file temporarily
    temp_path = Path("temp_input" + os.path.splitext(uploaded_file.name)[1])
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Two columns layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Single Conversion")
        codec = st.selectbox(
            "Select Codec (Single)",
            ["h265", "vp8", "vp9", "av1"],
            key="single_codec"
        )
        resolution = st.selectbox(
            "Select Resolution",
            ["1920:1080", "1280:720", "854:480", "640:360"],
            key="single_res"
        )
        bitrate = st.selectbox(
            "Select Bitrate",
            ["1000k", "500k", "250k", "125k"],
            key="single_bitrate"
        )
        if st.button("Convert Single"):
            with st.spinner("Converting..."):
                try:
                    output_path = convert_single(str(temp_path), codec, resolution, bitrate)
                    st.success(f"Conversion complete! Output saved as: {output_path}")
                except Exception as e:
                    st.error(f"Error during conversion: {str(e)}")
    
    with col2:
        st.markdown("### Encoding Ladder")
        codec_ladder = st.selectbox(
            "Select Codec (Ladder)",
            ["h265", "vp8", "vp9", "av1"],
            key="ladder_codec"
        )
        if st.button("Generate Encoding Ladder"):
            with st.spinner("Generating encoding ladder..."):
                try:
                    results = encode_ladder(str(temp_path), codec_ladder)
                    for result in results:
                        if "✅" in result:
                            st.success(result)
                        else:
                            st.error(result)
                except Exception as e:
                    st.error(f"Error during ladder generation: {str(e)}")
    
    # Cleanup
    if st.button("Clear All"):
        try:
            os.remove(temp_path)
            for f in Path(".").glob("output_*"):
                os.remove(f)
            st.success("All temporary files cleared!")
        except Exception as e:
            st.error(f"Error clearing files: {str(e)}")

else:
    st.info("👆 Upload a video file to get started!") 