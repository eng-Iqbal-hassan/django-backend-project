from rest_framework import serializers

from app.facilities.models import Facility


def validate_users(users):
    """Only doctors may be linked to a facility (see Facility.users)."""
    non_doctors = [user.email for user in users if not user.is_doctor]
    if non_doctors:
        raise serializers.ValidationError(
            f"Only doctors can be linked to a facility: {', '.join(non_doctors)}"
        )
    return users


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "facility_code", "facility_name", "users"]

    def validate_users(self, users):
        return validate_users(users)
