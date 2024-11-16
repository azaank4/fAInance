import os
import pathlib
import mdformat
import numpy as np
import cv2
import pymupdf4llm
from pdf2image import convert_from_path
import requests
import json
import speech_recognition as sr
from re import sub
import pyttsx3
import streamlit as st
from tempfile import NamedTemporaryFile

# Part 1: Extract images from the PDF
def extract_graphs_and_diagrams(pdf_path, data_dir="data"):
    output_path = os.path.join(data_dir, "images")
    os.makedirs(output_path, exist_ok=True)

    poppler_path = r"C:\poppler-24.08.0\Library\bin"
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
    for page_num, page in enumerate(pages):
        page_cv = np.array(page)
        page_cv = cv2.cvtColor(page_cv, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(page_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 10000:
                x, y, w, h = cv2.boundingRect(contour)
                diagram = page_cv[y:y+h, x:x+w]
                image_path = f"{output_path}/page_{page_num + 1}_diagram_{i + 1}.png"
                cv2.imwrite(image_path, diagram)

# Part 2: Extract text from the PDF
def extract_pdf_to_markdown(input_pdf, data_dir="data"):
    md_text = pymupdf4llm.to_markdown(input_pdf)
    formatted_content = mdformat.text(md_text)
    data_dir_path = pathlib.Path(data_dir)
    data_dir_path.mkdir(exist_ok=True)
    output_md_path = data_dir_path / pathlib.Path(input_pdf).with_suffix('.md').name
    output_md_path.write_text(formatted_content, encoding='utf-8')
    return output_md_path

# Part 3: Query OpenRouter models
def query_openrouter_models(md_file_path, models, prompt):
    with open(md_file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()
    responses = []
    for model in models:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer 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",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": f"Analyze the following markdown content: {md_content}"},
                    {"role": "user", "content": prompt}
                ]
            }
        )
        if response.status_code == 200:
            result = response.json()
            model_reply = result['choices'][0]['message']['content']
            responses.append((model, model_reply))
        else:
            responses.append((model, f"Error: {response.status_code}"))
    return responses

# Part 4: Record Voice Input
def record_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Recording... Please speak now.")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError as e:
            return f"Error: {e}"

# Part 5: Text-to-Speech
def text_to_speech(response_text):
    try:
        engine = pyttsx3.init()
        cleaned_text = sub(r'[^a-zA-Z0-9\s.,?!]', '', response_text)
        engine.say(cleaned_text)
        engine.runAndWait()
    except Exception as e:
        st.error(f"TTS Error: {e}")

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)
os.makedirs("data/images", exist_ok=True)

# Streamlit App
st.title("fAInance: Financial Report Analyzer")
uploaded_pdf = st.file_uploader("Upload your PDF", type=["pdf"])
models = ["meta-llama/llama-3.2-11b-vision-instruct:free"]

# Initialize session state
if "markdown_file" not in st.session_state:
    st.session_state["markdown_file"] = None
if "images_extracted" not in st.session_state:
    st.session_state["images_extracted"] = False

if uploaded_pdf:
    # Create a temporary file to store the uploaded PDF
    with NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_pdf.getvalue())
        pdf_path = tmp_file.name
        
    st.success("PDF Uploaded Successfully!")

    if not st.session_state["images_extracted"]:
        with st.spinner("Extracting images..."):
            extract_graphs_and_diagrams(pdf_path)
        st.session_state["images_extracted"] = True
        st.success("Images Extracted Successfully!")

    if not st.session_state["markdown_file"]:
        with st.spinner("Extracting text..."):
            st.session_state["markdown_file"] = extract_pdf_to_markdown(pdf_path)
        st.success("Text Extracted Successfully!")

    # Clean up temporary file
    os.unlink(pdf_path)

    st.info("You can now interact with the document.")
    prompt = st.text_input("Enter your prompt or click 'Record Voice'")
    voice_prompt = st.button("Record Voice")
    if voice_prompt:
        prompt = record_text()
        st.text_area("Recorded Prompt", value=prompt, height=100)

    if prompt:
        st.info("The model is processing...")
        responses = query_openrouter_models(st.session_state["markdown_file"], models, prompt)
        for model, reply in responses:
            st.subheader(f"Model: {model}")
            st.write(reply)
            text_to_speech(reply)
