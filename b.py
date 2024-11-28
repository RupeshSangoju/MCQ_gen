
import os
import random
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
from PyPDF2 import PdfReader
from docx import Document
from langdetect import detect
import streamlit as st

# Set your Groq API key
GROQ_API_KEY = "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"  # Replace with your actual API key

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    return "".join(page.extract_text() for page in reader.pages if page.extract_text())

# Function to extract text from Word document
def extract_text_from_word(file_path):
    doc = Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

# Function to prepare audio files for speech-to-text
def prepare_voice_file(path: str) -> str:
    if os.path.splitext(path)[1] == '.wav':
        return path
    elif os.path.splitext(path)[1] in ('.mp3', '.m4a', '.ogg', '.flac'):
        audio_file = AudioSegment.from_file(path, format=os.path.splitext(path)[1][1:])
        wav_file = os.path.splitext(path)[0] + '.wav'
        audio_file.export(wav_file, format='wav')
        return wav_file
    else:
        st.error(f'Unsupported audio format: {os.path.splitext(path)[1]}')

# Transcribe speech from audio
def transcribe_audio(audio_data, language="en-US"):
    recognizer = sr.Recognizer()
    try:
        result = recognizer.recognize_google(audio_data, language=language, show_all=True)
        if isinstance(result, dict) and 'alternative' in result:
            return result['alternative'][0]['transcript']
        else:
            return "No valid transcription available."
    except Exception as e:
        return f"Error during transcription: {e}"

def speech_to_text(input_path: str, language: str) -> str:
    wav_file = prepare_voice_file(input_path)
    with sr.AudioFile(wav_file) as source:
        audio_data = sr.Recognizer().record(source)
        return transcribe_audio(audio_data, language)

def extract_audio_from_video(video_path, output_audio_path="extracted_audio.wav"):
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(output_audio_path, codec='pcm_s16le')
        return output_audio_path
    except Exception as e:
        st.error(f"Error extracting audio: {e}")

def convert_video_to_text(video_path, language="en-US"):
    audio_path = extract_audio_from_video(video_path)
    if audio_path:
        return speech_to_text(audio_path, language)
    return "Failed to process the video."

# Question generation with Groq API
def query_groq(prompt):
    from groq import Groq  # Requires valid API key
    client = Groq(api_key=GROQ_API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192"
    )
    return chat_completion.choices[0].message.content.strip()

def generate_questions(question_type, syllabus, num_questions):
    prompt = f"""
    Syllabus:
    {syllabus}

    Generate {num_questions} {question_type} questions.
    """
    return query_groq(prompt)

# Streamlit UI
def main():
    st.title("Question Generator")
    st.write("Select your input type below:")
    syllabus = ""

    input_type = st.radio("Choose input type:", ("Voice", "Audio", "Text File", "Video"))

    if input_type == "Voice":
        audio_file = st.file_uploader("Upload a voice file:", type=["wav", "mp3", "m4a", "ogg", "flac"])
        if audio_file:
            temp_audio_path = f"temp_audio.{audio_file.name.split('.')[-1]}"
            with open(temp_audio_path, "wb") as f:
                f.write(audio_file.read())
            syllabus = speech_to_text(temp_audio_path, "en-US")

    elif input_type == "Audio":
        audio_file = st.file_uploader("Upload your audio file:", type=["wav", "mp3", "m4a", "ogg", "flac"])
        if audio_file:
            temp_audio_path = f"temp_audio.{audio_file.name.split('.')[-1]}"
            with open(temp_audio_path, "wb") as f:
                f.write(audio_file.read())
            syllabus = speech_to_text(temp_audio_path, "en-US")

    elif input_type == "Text File":
        file = st.file_uploader("Upload your text file (PDF, Word, or plain text):", type=["pdf", "docx", "txt"])
        if file:
            file_type = file.name.split('.')[-1]
            if file_type == "pdf":
                syllabus = extract_text_from_pdf(file)
            elif file_type == "docx":
                syllabus = extract_text_from_word(file)
            elif file_type == "txt":
                syllabus = file.read().decode("utf-8")
            else:
                st.warning("Unsupported file type.")
    
    elif input_type == "Video":
        video_file = st.file_uploader("Upload your video file (MP4, AVI, MKV):", type=["mp4", "avi", "mkv"])
        if video_file:
            temp_video_path = f"temp_video.{video_file.name.split('.')[-1]}"
            with open(temp_video_path, "wb") as f:
                f.write(video_file.read())
            syllabus = convert_video_to_text(temp_video_path, "en-US")

    if not syllabus:
        st.warning("Please provide valid input.")
        return

    st.write("Extracted Text:")
    st.write(syllabus)

    question_type = st.radio("Choose question type:", ("MCQ", "Fill in the Blanks", "True/False", "Matching"))
    num_questions = st.number_input("Enter number of questions to generate:", min_value=1, max_value=50, step=1)

    if st.button("Generate Questions"):
        questions = generate_questions(question_type, syllabus, num_questions)
        st.write("Generated Questions:")
        st.write(questions)

if __name__ == "__main__":
    main()