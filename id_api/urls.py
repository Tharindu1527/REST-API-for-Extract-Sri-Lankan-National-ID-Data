from django.urls import path
from .views import IDCardOCRView

urlpatterns = [
    path('extract/', IDCardOCRView.as_view(), name='extract_id_data'),
]