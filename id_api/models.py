from django.db import models

#Model to store ID card images
class IDCard(models.Model):
    image = models.ImageField(upload_to='id_cards/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"ID Card {self.id}"