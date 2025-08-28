
from google.cloud import vision

def extract_text_from_image(image_file) -> str:
    """
    Extract text from an uploaded image using Google Vision OCR.

    Args:
        image_file: Uploaded image file (BytesIO or similar)

    Returns:
        str: Extracted text or error message
    """
    try:
        client = vision.ImageAnnotatorClient()
        content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if texts:
            return texts[0].description
        else:
            return "No text found"
    except Exception as e:
        return f"OCR Error: {str(e)}"