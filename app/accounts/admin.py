from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from app.accounts.models import PasswordResetOTP, User
from app.facilities.models import Facility


class UserAddForm(UserCreationForm):
    """Form for the 'Add user' page: email, name, role and the password typed twice."""

    class Meta:
        model = User
        fields = ("email", "name", "role")

    def clean_email(self):
        return self.cleaned_data["email"].lower()


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"

    def clean_email(self):
        return self.cleaned_data["email"].lower()


class FacilityLinkFormSet(BaseInlineFormSet):
    """Only doctors may be linked to facilities."""

    def clean(self):
        super().clean()
        # self.instance is the user with the role submitted on this same page,
        # so changing a linked doctor to Admin is also caught.
        if self.instance.role == User.Role.DOCTOR:
            return
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("facility") and not form.cleaned_data.get("DELETE"):
                raise ValidationError(
                    "Only doctors can be linked to facilities. "
                    "Remove the facilities or set the role to Doctor."
                )


class FacilityInline(admin.TabularInline):
    """Link a user (doctor) to facilities from the user's page.

    The ManyToManyField is defined on Facility (Facility.users), so we edit the join table here.
    """

    model = Facility.users.through
    formset = FacilityLinkFormSet
    extra = 1
    verbose_name = "Facility"
    verbose_name_plural = "Facilities"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserEditForm
    add_form = UserAddForm
    inlines = [FacilityInline]

    list_display = ("email", "name", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "name")
    ordering = ("email",)

    # Edit page
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("name", "role")}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "classes": ("collapse",),
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    # Add page
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    """Read-only view of reset codes, useful for debugging the forgot-password flow."""

    list_display = ("user", "created_at", "expires_at", "attempts", "used_at")
    list_filter = ("used_at",)
    search_fields = ("user__email",)
    readonly_fields = ("user", "code_hash", "created_at", "expires_at", "attempts", "used_at")

    def has_add_permission(self, request):
        return False
