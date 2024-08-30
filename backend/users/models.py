from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """
    Custom user model.
    """
    USER = 'user'
    ADMIN = 'admin'
    ROLE_USER = [
        (USER, 'User'),
        (ADMIN, 'Admin')
    ]

    username_validator = RegexValidator(
        regex=r'^[\w.@+-]+\Z',
        message=(
            'Username can only contain letters, digits, and '
            'the following symbols: @/./+/-/_'
        )
    )

    username = models.CharField(
        'Username',
        max_length=150,
        unique=True,
        validators=[username_validator]
    )
    first_name = models.CharField('First_name', max_length=150)
    last_name = models.CharField('Last_name', max_length=150)
    email = models.EmailField('email_address', unique=True)
    role = models.CharField(max_length=15, choices=ROLE_USER, default=USER)
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        default=None
    )
    password = models.CharField(max_length=150, verbose_name='Password')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def admin(self):
        return self.role == self.ADMIN

    def __str__(self):
        return f'user: {self.username}; role: {self.role}'


class Follow(models.Model):
    """
    Model to discribe users following one another.
    """
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
        ]

    def __str__(self):
        return f'user:{self.user}; following: {self.following};'
