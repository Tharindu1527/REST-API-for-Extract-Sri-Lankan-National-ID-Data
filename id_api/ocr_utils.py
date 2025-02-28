import cv2
import re
import pytesseract
import uuid
from PIL import Image
import os
import numpy as np
from django.conf import settings

# Configuration for Tesseract
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

#Remove background patterns using morphological operations
def remove_background_patterns(image): 
    kernel = np.ones((3, 3), np.uint8) # Create a kernel for morphological operations
    opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1) # Apply morphological opening to remove small noise  
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1) # Apply morphological closing to fill small holes
    
    return closing

#Enhance text in the image using various techniques
def enhance_text(image): 
    # Apply unsharp masking for sharpening
    gaussian = cv2.GaussianBlur(image, (0, 0), 3)
    sharpened = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(sharpened)
    
    return enhanced
#Preprocess the image to improve OCR accuracy
def preprocess_image(image_path):
    
    
    img = cv2.imread(image_path) # Read the image 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Convert to grayscale
    cleaned = remove_background_patterns(gray) # Remove background patterns 
    enhanced = enhance_text(cleaned) # Enhance text
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)

    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21) # Remove noise
    
    # Save the preprocessed image
    preprocessed_path = image_path.replace('.', '_preprocessed.')
    cv2.imwrite(preprocessed_path, denoised)
    
    # Apply Otsu's thresholding for more preprocessing
    _, otsu = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    otsu_path = image_path.replace('.', '_otsu.')
    cv2.imwrite(otsu_path, otsu)
    
    return preprocessed_path, otsu_path

"""Extract data from Sri Lankan ID card"""
def extract_id_data(image_path):    
    scan_id = str(uuid.uuid4()) # Generate a unique scan ID
    preprocessed_path, otsu_path = preprocess_image(image_path) # Preprocess the image with multiple approaches
    
    text1 = pytesseract.image_to_string(
        Image.open(preprocessed_path),
        lang='sin+eng+tam',  # Use Sinhala, English and Tamil because Sri lankan id has Sihnhala and Tamil language
        config='--psm 6 --oem 3'
    )
    
    text2 = pytesseract.image_to_string(
        Image.open(otsu_path),
        lang='sin+eng+tam',
        config='--psm 4 --oem 3' 
    )
    
    text = text1 + "\n" + text2
    
    # Clean up temporary files
    for path in [preprocessed_path, otsu_path]:
        if os.path.exists(path):
            os.remove(path)
    
    # Extract data
    full_name = extract_full_name(text)
    id_number = extract_id_number(text)
    date_of_birth = extract_dob(text)
    address = extract_address(text)
    
    print("Extracted OCR Text:", text)
    
    if id_number is None:
        id_number = extract_id_number_by_position(image_path)
    
    # Define format of the response
    data = {
        'scan_id': scan_id,
        'data': {
            'full_name': full_name if full_name else "නම හඳුනාගත නොහැක",
            'id_number': id_number if id_number else "හැඳුනුම්පත් අංකය හඳුනාගත නොහැක",
            'date_of_birth': date_of_birth if date_of_birth else "උපන් දිනය හඳුනාගත නොහැක",
            'address': address if address else "ලිපිනය හඳුනාගත නොහැක"
        }
    }
    
    return data

"""Extract ID number by looking at specific regions of the image"""
def extract_id_number_by_position(image_path):
    
    img = cv2.imread(image_path)
    height, width, _ = img.shape
    
    # Focus on the bottom 20% of the image where ID number is typically located
    bottom_region = img[int(height * 0.8):height, :]
    
    # Convert to grayscale
    gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # OCR just this region
    text = pytesseract.image_to_string(thresh, config='--psm 7 --oem 3')
    
    match = re.search(r'[A-Z]\s*\d{7}|\d{9}[Vv]|\d{12}', text)
    if match:
        return match.group(0).strip()
    
    return None

def extract_full_name(text):
    """Extract full name from the OCR text"""
    # Look for Sinhala text following name identifiers
    name_patterns = [
        r'Name[:\s]*([^\n]+)',
        r'නම[:\s]*([^\n]+)', 
        r'සම්පූර්ණ නම[:\s]*([^\n]+)', 
        r'මුල් නම[:\s]*([^\n]+)', 
        r'වෙනත් නම්[:\s]*([^\n]+)'
    ]
    
    # Check each pattern
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    # Look for large blocks of Sinhala text that might be names
    sinhala_ranges = '[\u0D80-\u0DFF]'
    sinhala_name = re.search(f'{sinhala_ranges}{{3,}}\\s+{sinhala_ranges}{{3,}}', text)
    if sinhala_name:
        return sinhala_name.group(0).strip()
    
    # Extract lines that might contain names (first few lines of ID card)
    lines = text.split('\n')
    for line in lines[:5]:  
        if len(line.strip()) > 5 and not re.search(r'\d{4}', line):
            return line.strip()
    
    return None

"""Extract ID number from the OCR text"""
def extract_id_number(text):   
    id_patterns = [
        r'(\d{9}[Vv])',  # Old format With V
        r'(\d{12})',     # New format
        r'([A-Z]\s*\d{7})',  # Format with letter prefix like F 1234567
        r'ID:?\s*(\d{9}[Vv]|\d{12}|[A-Z]\s*\d{7})',  # With ID prefix
        r'අංකය:?\s*(\d{9}[Vv]|\d{12}|[A-Z]\s*\d{7})'  # With Sinhala prefix
    ]
    
    for pattern in id_patterns:
        match = re.search(pattern, text)
        if match:
            id_number = match.group(1)
            id_number = re.sub(r'\s+', ' ', id_number).strip()
            return id_number
    
    return None

"""Extract date of birth from the OCR text"""
def extract_dob(text):  
    dob_patterns = [
        r'උපන්\s*දිනය[:\s]*([0-9]{4}[/\-\.][0-9]{2}[/\-\.][0-9]{2})',  # YYYY/MM/DD
        r'උපන්\s*දිනය[:\s]*([0-9]{2}[/\-\.][0-9]{2}[/\-\.][0-9]{4})',  # DD/MM/YYYY
        r'Date of Birth[:\s]*([0-9]{2,4}[/\-\.][0-9]{2}[/\-\.][0-9]{2,4})',  
        r'DOB[:\s]*([0-9]{2,4}[/\-\.][0-9]{2}[/\-\.][0-9]{2,4})', 
        r'([0-9]{4}[/\-\.][0-9]{2}[/\-\.][0-9]{2})',
        r'([0-9]{2}[/\-\.][0-9]{2}[/\-\.][0-9]{4})'  
    ]
    
    for pattern in dob_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

"""Extract address from the OCR text"""
def extract_address(text):   
    address_patterns = [
        r'ලිපිනය[:\s]*([^\n]+(?:\n[^\n]+)*)',  # Sinhala
        r'Address[:\s]*([^\n]+(?:\n[^\n]+)*)',  # English
        r'\d+\/\d+[\-\d]*,\s*[\u0D80-\u0DFF\s,\.\-]+'  # Pattern like 19/54-1, followed by Sinhala
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, text)
        if match:
            address = match.group(1) if '(' in pattern else match.group(0)
            return ' '.join(address.split())
    
    addr_match = re.search(r'\d+\/\d+[A-Za-z0-9\-]*,?\s*[^\n,\.]{3,}', text)
    if addr_match:
        return addr_match.group(0).strip()
    
    return None
