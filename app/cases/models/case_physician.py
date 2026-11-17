from django.db import models


class CasePhysician(models.Model):
    """
    Links a physician to a case with a role, e.g. "Dr. Phoebe Buffay (Attending)".
    Used by the "My cases only" toggle and the Physician filter.
    """

    class Role(models.TextChoices):
        ATTENDING = "attending", "Attending"
        REFERRING = "referring", "Referring"
        CONSULTING = "consulting", "Consulting"

    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        related_name="case_physicians",
    )
    physician = models.ForeignKey(
        "cases.Physician",
        on_delete=models.PROTECT,
        related_name="case_links",
    )
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "physician", "role"],
                name="unique_case_physician_role",
            ),
        ]

    def __str__(self):
        return f"{self.physician} ({self.get_role_display()})"
