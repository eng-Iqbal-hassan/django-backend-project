from django.conf import settings
from django.db import models
from django.utils import timezone


class ReportView(models.Model):
    """
    Who has read which report. Drives "Show only unread reports"
    and the "FINAL (NEW)" dashboard tile.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_views",
    )
    report = models.ForeignKey(
        "cases.Report",
        on_delete=models.CASCADE,
        related_name="views",
    )
    viewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "report"], name="unique_user_report_view"),
        ]

    def __str__(self):
        return f"{self.user} viewed {self.report}"
