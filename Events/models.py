from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.html import mark_safe

class Event(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Enter the name of the event",
        verbose_name="Event Name"
    )
    date = models.DateField(
        help_text="Select the date of the event",
        verbose_name="Event Date"
    )
    location = models.CharField(
        max_length=255,
        help_text="Enter the location/venue of the event",
        verbose_name="Event Location"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Event Creator",
        related_name='created_events'
    )
    img = models.ImageField(
        upload_to='event_images/',
        null=True,
        blank=True,
        verbose_name="Event Image",
        help_text="Upload an image for the event (optional)"
    )
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Start Time",
        help_text="Enter the start time of the event"
    )
    stop_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="End Time",
        help_text="Enter the end time of the event"
    )

    class Meta:
        ordering = ['-date', 'name']
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return f"{self.name} - {self.date}"

    def get_absolute_url(self):
        return reverse('event-detail', args=[str(self.id)])

class EventRegistration(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Participant",
        related_name='event_registrations'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        verbose_name="Event",
        related_name='registrations'
    )
    registration_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Registration Date"
    )

    class Meta:
        ordering = ['-registration_date']
        verbose_name = "Event Registration"
        verbose_name_plural = "Event Registrations"
        unique_together = ['user', 'event']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.event.name}"

class BarcodeScan(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Participant",
        related_name='barcode_scans'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        verbose_name="Event",
        related_name='barcode_scans'
    )
    scan_time = models.DateTimeField(
        verbose_name="Scan Time"
    )
    time_taken = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        verbose_name="Time Taken",
        help_text="Time taken to complete the event"
    )

    class Meta:
        ordering = ['time_taken']
        verbose_name = "Barcode Scan"
        verbose_name_plural = "Barcode Scans"
        indexes = [
            models.Index(fields=['time_taken']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.event.name}"

class QRCodeData(models.Model):
    data = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="QR Code Data"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creation Date"
    )

    class Meta:
        verbose_name = "QR Code Data"
        verbose_name_plural = "QR Code Data"

    def __str__(self):
        return f"QR Code: {self.data}"

class AboutSection(models.Model):
    subtitle = models.CharField(
        max_length=255,
        help_text="Enter a subtitle for the about section",
        verbose_name="Subtitle"
    )
    description = models.TextField(
        help_text="Enter the main description (use paragraphs separated by \\n)",
        verbose_name="Description"
    )
    image = models.ImageField(
        upload_to='about_images/',
        help_text="Upload an image for the about section",
        verbose_name="Image"
    )

    class Meta:
        verbose_name = "About Section"
        verbose_name_plural = "About Sections"

    def __str__(self):
        return self.subtitle

class Stat(models.Model):
    about_section = models.ForeignKey(
        AboutSection,
        related_name='stats',
        on_delete=models.CASCADE,
        verbose_name="About Section"
    )
    number = models.CharField(
        max_length=50,
        help_text="Enter the statistic number (e.g., 300+)",
        verbose_name="Statistic Number"
    )
    text = models.CharField(
        max_length=100,
        help_text="Enter the statistic description",
        verbose_name="Statistic Description"
    )

    class Meta:
        verbose_name = "Statistic"
        verbose_name_plural = "Statistics"

    def __str__(self):
        return f"{self.number} {self.text}"