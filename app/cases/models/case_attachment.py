from django.conf import settings
from django.db import models
from django.utils import timezone


class CaseAttachment(models.Model):
    """
    A file on a case, e.g. "Demographics & Insurance".
    "All requests remain a part of the attachments": when a doctor submits an
    AdditionalRequest, the backend generates a document and attaches it here.
    """

    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        JPG = "jpg", "JPG"
        DOC = "doc", "DOC"

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="cases/attachments/%Y/%m/")
    file_type = models.CharField(max_length=10, choices=FileType.choices)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_case_attachments",
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    # Set when this attachment was generated from a request.
    additional_request = models.OneToOneField(
        "cases.AdditionalRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attachment",
    )

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self):
        return self.title
