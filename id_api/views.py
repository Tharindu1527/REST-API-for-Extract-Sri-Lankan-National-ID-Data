from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import IDCardSerializer
from .ocr_utils import extract_id_data
import os

class IDCardOCRView(APIView):
    """API view to process ID card image and extract data"""
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        # Validate and save the uploaded image
        serializer = IDCardSerializer(data=request.data)
        if serializer.is_valid():
            id_card = serializer.save()
            
            try:
                # Extract data from the image
                image_path = id_card.image.path
                result = extract_id_data(image_path)
                
                # Convert None values to Sinhala "not found" messages
                if result['data']['full_name'] is None:
                    result['data']['full_name'] = "නම හඳුනාගත නොහැක"
                
                if result['data']['id_number'] is None:
                    result['data']['id_number'] = "හැඳුනුම්පත් අංකය හඳුනාගත නොහැක"
                
                if result['data']['date_of_birth'] is None:
                    result['data']['date_of_birth'] = "උපන් දිනය හඳුනාගත නොහැක"
                
                if result['data']['address'] is None:
                    result['data']['address'] = "ලිපිනය හඳුනාගත නොහැක"
                
                # Return the extracted data with scan_id
                return Response(result, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response(
                    {
                        "error": "OCR ක්‍රියාවලිය අසාර්ථක විය",  # "OCR processing failed" in Sinhala
                        "details": str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            finally:
                # Clean up the uploaded image
                if id_card.image and os.path.isfile(id_card.image.path):
                    id_card.delete()
        
        return Response(
            {
                "error": "වලංගු නොවන ඉල්ලීමක්",  # "Invalid request" in Sinhala
                "details": serializer.errors
            }, 
            status=status.HTTP_400_BAD_REQUEST
        )