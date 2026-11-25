from django.contrib import admin

from app.accounts.models import User
from .models import Facility


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("facility_code", "facility_name")
    search_fields = ("facility_code", "facility_name")
    filter_horizontal = ("users",)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Only doctors can be picked as users of a facility.
        if db_field.name == "users":
            kwargs["queryset"] = User.objects.filter(role=User.Role.DOCTOR).order_by("email")
        return super().formfield_for_manytomany(db_field, request, **kwargs)
