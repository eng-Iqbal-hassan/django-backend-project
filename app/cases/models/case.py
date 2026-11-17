from django.db import models


class Case(models.Model):
    """The central record. Reports, attachments and requests all belong to a case."""

    # Values from the Status filter.
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PRELIMINARY_1 = "preliminary_1", "1st Preliminary"
        PRELIMINARY_2 = "preliminary_2", "2nd Preliminary"
        PRELIMINARY_3 = "preliminary_3", "3rd Preliminary"
        ADDENDUM_1 = "addendum_1", "1st Addendum"
        ADDENDUM_2 = "addendum_2", "2nd Addendum"
        ADDENDUM_3 = "addendum_3", "3rd Addendum"
        ADDENDUM_4 = "addendum_4", "4th Addendum"
        FINAL = "final", "Final"
        CORRECTION = "correction", "Correction"
        AMENDED = "amended", "Amended"

    # e.g. "LB24-00501"
    case_number = models.CharField(max_length=50, unique=True)
    patient = models.ForeignKey(
        "cases.Patient",
        on_delete=models.PROTECT,
        related_name="cases",
    )
    # One sample per case, so one specimen type. Same table Pick-ups use.
    specimen_type = models.ForeignKey(
        "pickups.SampleType",
        on_delete=models.PROTECT,
        related_name="cases",
    )
    facility = models.ForeignKey(
        "facilities.Facility",
        on_delete=models.PROTECT,
        related_name="cases",
    )
    physicians = models.ManyToManyField(
        "cases.Physician",
        through="cases.CasePhysician",
        related_name="cases",
    )

    received_date = models.DateField()
    # Follows the latest report; a case with no reports is "Pending".
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    signed_off_at = models.DateTimeField(null=True, blank=True)

    # The case's ID in Tiger, used for syncing.
    external_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-received_date", "-id"]
        indexes = [
            models.Index(fields=["facility", "status"]),
            models.Index(fields=["received_date"]),
        ]

    def __str__(self):
        return self.case_number
