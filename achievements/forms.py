from achievements.models import Achievement
from django import forms
from django.conf import settings
import os
import hashlib


class AchievementForm(forms.ModelForm):
    existing_icons = forms.ChoiceField(label="Or choose an existing image", required=False, choices=[])

    class Meta:
        model = Achievement
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        folder_path = os.path.join(settings.MEDIA_ROOT, 'stregsystem/achievement')
        choices = [('', '---')]
        if os.path.exists(folder_path):
            for filename in sorted(os.listdir(folder_path)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    path = os.path.join('stregsystem/achievement', filename)
                    choices.append((path, filename))
        self.fields['existing_icons'].choices = choices

    def save(self, commit=True):
        instance = super().save(commit=False)

        new_upload = self.files.get('icon')
        selected_icon_path = self.cleaned_data.get('existing_icons')

        if new_upload:
            uploaded_bytes = new_upload.read()
            uploaded_hash = hashlib.md5(uploaded_bytes).hexdigest()

            folder_path = os.path.join(settings.MEDIA_ROOT, 'stregsystem/achievement')
            match_found = False

            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                # Check for matching hash
                with open(file_path, 'rb') as f:
                    existing_hash = hashlib.md5(f.read()).hexdigest()
                    if uploaded_hash == existing_hash:
                        # Match found — use existing file
                        instance.icon.name = os.path.join('stregsystem/achievement', filename)
                        match_found = True
                        break

            if not match_found:
                # No match — reset file pointer and let Django upload it
                new_upload.seek(0)  # important!
                instance.icon = new_upload

        elif selected_icon_path:
            # No upload, but existing image selected
            instance.icon.name = selected_icon_path

        if commit:
            instance.save()
        return instance
