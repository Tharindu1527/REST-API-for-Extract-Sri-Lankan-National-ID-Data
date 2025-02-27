# Sri Lankan ID Card OCR API

A Django REST API that extracts information from Sri Lankan National ID cards using OCR (Optical Character Recognition). The API processes images and returns the extracted data in Sinhala language as JSON.

## Features

- REST API endpoint to upload and process ID card images
- OCR processing using Tesseract with Sinhala language support
- Extraction of key information:
  - Full Name
  - National ID Number
  - Date of Birth
  - Address (if available)
- JSON response with extracted data
- Dockerized environment for easy deployment

## Prerequisites

- Docker and Docker Compose
- Tesseract OCR with Sinhala language support

## Setup and Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/Tharindu1527/REST-API-for-Extract-Sri-Lankan-National-ID-Data.git
   cd REST-API-for-Extract-Sri-Lankan-National-ID-Data
   ```

2. Build and run the Docker container:
   ```bash
   docker-compose up --build
   ```

3. The API will be available at `http://localhost:8000/api/id/extract/`

### Local Development

1. Install Tesseract OCR with Sinhala language support:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-sin
   
   # macOS
   brew install tesseract
   brew install tesseract-lang # includes Sinhala language
   ```

2. Set up a virtual environment and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Update the `TESSERACT_CMD` in `settings.py` to point to your Tesseract installation.

4. Run migrations and start the development server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## API Usage

### Endpoint

- `POST /api/id/extract/`

### Request

Send a `POST` request with form-data containing:
- `image`: The ID card image file

### Response

A JSON object containing:
```json
{
  "full_name": "සම්පූර්ණ නම",
  "id_number": "හැඳුනුම්පත් අංකය",
  "date_of_birth": "උපන් දිනය",
  "address": "ලිපිනය"
}
```

## Limitations

- OCR accuracy depends on image quality
- Specific field recognition depends on the format of the ID card
- The system works best with clear, well-lit images
