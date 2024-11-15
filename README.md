Here's a README.md file for your project:

```markdown:README.md
# PDF Analysis and Interactive Query System

A Python application that extracts content from PDF files, processes it, and allows users to query the content using AI models through OpenRouter API.

## Features

- PDF content extraction to markdown format
- Automatic extraction of graphs and diagrams from PDFs
- Text-to-Speech capability for AI responses
- Support for multiple AI models through OpenRouter
- Interactive query interface

## Prerequisites

### Required Software
- Python 3.8+
- Poppler (for PDF processing)
  - Windows: Download from [Poppler Releases](https://github.com/oschwartz10612/poppler-windows/releases/)
  - Linux: `sudo apt-get install poppler-utils`
  - macOS: `brew install poppler`

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. Install the required packages:
```bash
pip install mdformat numpy opencv-python pymupdf4llm pdf2image requests speechrecognition keyboard gtts playsound pygame
```

3. Set up your OpenRouter API key:
- Sign up at [OpenRouter](https://openrouter.ai/)
- Replace `YOUR_API_KEY` in the code with your actual API key

## Usage

1. Place your PDF file in the project directory

2. Update the PDF filename in `main.py`:
```python
input_pdf = "your_file.pdf"
```

3. Run the application:
```bash
python main.py
```

4. Interact with the system:
- The program will extract text and images from your PDF
- Enter queries about the PDF content
- Receive AI-generated responses with text-to-speech output

## Project Structure

```
project/
├── main.py          # Main application file
├── data/            # Generated data directory
│   ├── images/      # Extracted images from PDF
│   └── *.md         # Extracted markdown content
├── requirements.txt
└── README.md
```

## Features in Detail

### PDF Processing
- Extracts text content and converts it to markdown format
- Identifies and extracts graphs, diagrams, and images
- Saves extracted content in organized directories

### AI Integration
- Connects to OpenRouter API
- Supports multiple AI models
- Concurrent model querying for faster responses

### User Interface
- Text input for queries
- Text-to-Speech output for responses
- Support for multiple AI model responses

## Contributing

Feel free to submit issues and enhancement requests!

## License

[Your chosen license]

## Acknowledgments

- OpenRouter for AI model access
- Poppler for PDF processing
- All other open-source libraries used in this project
```

You'll also want to create a `requirements.txt` file:

```text:requirements.txt
mdformat
numpy
opencv-python
pymupdf4llm
pdf2image
requests
SpeechRecognition
keyboard
gTTS
playsound
pygame
```
