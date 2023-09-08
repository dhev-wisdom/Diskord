from django.forms import ModelForm, FileInput, ImageField, CharField, Textarea
from .models import Room, UserProfile
from django.contrib.auth.models  import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['image', 'bio']

class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']

def validate_image_size(value):
    limit = 500 * 24
    if value.size > limit:
        raise ValidationError(_('Image size must be 500KB or less.'))

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        exclude = ['email']

    image = ImageField(
        required=False,
        label='Profile Picture',
        widget=FileInput(attrs={'accept': 'image/*'}),
        validators=[validate_image_size],
    )
    bio = CharField(
        required=False,
        widget=Textarea(attrs={'rows': 1}),
        label='Bio'
    )
    def clean(self):
        cleaned_data = super().clean()
        image = self.cleaned_data['image']
        
        if image is None:
            cleaned_data['image'] = None
        
        if image:
            print("image size: ", image.size)
            limit = 500 * 1024
            if image.size > limit:
                raise ValidationError({'image': [_('Image size must be 500KB or less.')]})

        return cleaned_data