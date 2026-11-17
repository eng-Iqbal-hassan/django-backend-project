from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Report(models.Model):
    """
    One row per report version. "Report Versions" lists them newest first;
    "View ... Report" opens the latest one.
    """

    class ReportType(models.TextChoices):
        PRELIMINARY = "preliminary", "Preliminary"
        ADDENDUM = "addendum", "Addendum"
        FINAL = "final", "Final"
        CORRECTION = "correction", "Correction"
        AMENDED = "amended", "Amended"

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    # 1, 2, 3 -> "3rd Preliminary Report"
    sequence = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    file = models.FileField(upload_to="cases/reports/%Y/%m/")

    # Lab staff, e.g. "Patricia Espinal".
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_reports",
    )
    uploaded_at = models.DateTimeField(default=timezone.now)

    # The report's ID in Tiger, used for syncing.
    external_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["case", "report_type", "sequence"],
                name="unique_case_report_type_sequence",
            ),
        ]

    def __str__(self):
        return f"{self.case} - {self.get_report_type_display()} #{self.sequence}"
