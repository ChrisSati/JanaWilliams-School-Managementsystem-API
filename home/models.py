from django.db import models

class Slide(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="slides/")
    order = models.PositiveIntegerField(default=0)  # for slide ordering

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order']





class AdmissionAnnouncement(models.Model):
    title = models.CharField(max_length=255)
    highlight = models.CharField(max_length=100, blank=True)  # e.g., "Announcement !"
    description = models.TextField()
    button_text = models.CharField(max_length=100, default="Join to our School Now")
    image = models.ImageField(upload_to="admissions/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



# Cards displayed on homepage
class Card(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='cards/')

    def __str__(self):
        return self.title

# Staff (Administrative Staff)
class Staff(models.Model):
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="staff/")

    def __str__(self):
        return self.full_name

# Home popup content
class HomePopup(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="popup/")

    def __str__(self):
        return self.title