import os
import pathlib
import mdformat
import numpy as np
import cv2
import pymupdf4llm
from pdf2image import convert_from_path
import concurrent.futures
import requests
import json
import speech_recognition as sr
import keyboard
from gtts import gTTS
import playsound
from re import sub

# Part 1: Extract images from the PDF and save them in the data folder
def extract_graphs_and_diagrams(pdf_path, data_dir="data"):
    print("Extracting images...")
    output_path = os.path.join(data_dir, "images")
    os.makedirs(output_path, exist_ok=True)

    # Define the poppler path
    poppler_path = r"C:\poppler-24.08.0\Library\bin"

    # Convert each page of the PDF to an image
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
    for page_num, page in enumerate(pages):
        # Convert PIL image to OpenCV format
        page_cv = np.array(page)
        page_cv = cv2.cvtColor(page_cv, cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(page_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours of potential diagrams
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Loop through contours to find large areas that could be diagrams
        for i, contour in enumerate(contours):
            # Filter by area size to ignore small elements
            area = cv2.contourArea(contour)
            if area > 10000:  # Adjust area threshold as needed
                x, y, w, h = cv2.boundingRect(contour)
                diagram = page_cv[y:y+h, x:x+w]
                image_path = f"{output_path}/page_{page_num + 1}_diagram_{i + 1}.png"
                cv2.imwrite(image_path, diagram)
                print(f"Saved diagram: {image_path}")

# Part 2: Extract text from the PDF and save as Markdown in the data folder
def extract_pdf_to_markdown(input_pdf, data_dir="data"):
    print("Extracting and formatting text...")
    md_text = pymupdf4llm.to_markdown(input_pdf)
    formatted_content = mdformat.text(md_text)

    # Create data directory if it doesn't exist
    data_dir_path = pathlib.Path(data_dir)
    data_dir_path.mkdir(exist_ok=True)

    # Save the Markdown file
    output_md_path = data_dir_path / pathlib.Path(input_pdf).with_suffix('.md').name
    output_md_path.write_text(formatted_content, encoding='utf-8')

    print(f"Markdown file created successfully in {data_dir}.")
    return output_md_path

# Part 3: Query OpenRouter models using the extracted markdown
def query_openrouter_models(md_file_path, models):
    with open(md_file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()

    print("Markdown content loaded. You can now speak your queries.")

    while True:
        print("\nHold spacebar to speak your prompt (say 'exit' to quit)")
        prompt = record_text()
        
        if not prompt:  # If speech recognition failed
            continue
        if prompt.lower() == "exit":
            print("Exiting program.")
            break

        # Define a function to query each model
        def query_model(model):
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {YOUR_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Analyze the following markdown content: {md_content}"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            return model, response

        # Use ThreadPoolExecutor to run queries concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            responses = list(executor.map(query_model, models))

        # Process and print responses
        for model, response in responses:
            if response.status_code == 200:
                result = response.json()
                model_reply = result['choices'][0]['message']['content']
                print(f"Model: {model}")
                print(f"Response: {model_reply}")
                print("-" * 50)
                # Add speech output
                text_to_speech(model_reply)
            else:
                error_message = f"Error for model {model}: {response.status_code}"
                print(error_message)
                text_to_speech(error_message)
                print("-" * 50)

def record_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.1)
        print("Listening... Hold spacebar to speak.")
        
        while not keyboard.is_pressed('space'):
            continue  # Wait for spacebar press
            
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Couldn't understand the audio. Please try again.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""

def text_to_speech(response_text):
    # Clean the text by removing special characters and markdown symbols
    cleaned_text = sub(r'[^a-zA-Z0-9\s.,?!]', '', response_text)
    try:
        tts = gTTS(text=cleaned_text, lang='en')
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            playsound.playsound(fp.name)
            import os
            os.unlink(fp.name)
    except Exception as e:
        print(f"TTS Error: {e}")

# Main program
if __name__ == "__main__":
    # Specify the input PDF file
    input_pdf = "June report short.pdf"  # Replace with your PDF file name

    # Models to query
    models = [
        # "microsoft/phi-3.5-mini-128k-instruct",
        "meta-llama/llama-3.2-11b-vision-instruct:free", 
        # "google/gemini-flash-1.5-8b"
        # Add more models if needed
    ]

    # Extract images and save them
    extract_graphs_and_diagrams(input_pdf)

    # Extract text and get the Markdown file path
    markdown_file = extract_pdf_to_markdown(input_pdf)

    # Query OpenRouter models with the extracted markdown content
    query_openrouter_models(markdown_file, models)
