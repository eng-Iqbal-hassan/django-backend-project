from typing import TYPE_CHECKING

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from app.accounts.choices import Role

if TYPE_CHECKING:
    from app.facilities.models import Facility


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, name, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, name, password, **extra_fields)

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SALESMAN)
        if not extra_fields.get("is_staff") or not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_staff=True and is_superuser=True")
        return self._create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Application user. Email is unique and is the login identifier.
    `password` is provided by AbstractBaseUser (stored hashed).
    """

    # Defined in choices.py so other apps can import it without importing User.
    # Kept here as well so `User.Role.DOCTOR` still works.
    Role = Role

    email = models.EmailField(unique=True, max_length=254)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)

    # Needed for Django admin / auth framework.
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # `user.facilities` is provided by Facility.users (ManyToManyField).
    # Annotation only (no value), so Django ignores it; it just tells the IDE it exists.
    facilities: "models.Manager[Facility]"

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    def has_facility_access(self, facility):
        """True if this doctor is linked to the given facility (object or facility_id)."""
        facility_id = getattr(facility, "pk", facility)
        return self.facilities.filter(pk=facility_id).exists()

    def __str__(self):
        return self.email
