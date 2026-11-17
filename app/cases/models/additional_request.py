from django.conf import settings
from django.db import models


class AdditionalRequest(models.Model):
    """
    The "+" button on a case. All four request forms share this table.

    Fields used per type:
        UPDATE_CASE_DETAILS   details ("Request case updates")
        TALK_TO_PATHOLOGIST   reason, callback_number
        TEST_CANCELLATION     details ("Tests to be cancelled"), reason
        ADD_ONS               details ("Request add ons")
    """

    class RequestType(models.TextChoices):
        UPDATE_CASE_DETAILS = "update_case_details", "Update Case Details"
        TALK_TO_PATHOLOGIST = "talk_to_pathologist", "Talk to a Pathologist"
        TEST_CANCELLATION = "test_cancellation", "Test Cancellation"
        ADD_ONS = "add_ons", "Add ons"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        IN_REVIEW = "in_review", "In review"
        RESOLVED = "resolved", "Resolved"

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="additional_requests",
    )
    # The logged-in user who submitted the form.
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="additional_requests",
    )
    request_type = models.CharField(max_length=30, choices=RequestType.choices)

    # Full name typed on the form.
    requested_by = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    callback_number = models.CharField(max_length=30, blank=True)

    is_electronically_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.case}"
