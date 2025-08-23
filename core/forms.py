from django import forms


class VideoForm(forms.Form):
    video_url = forms.URLField(
        label='Facebook Video URL',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Paste public Facebook video link (post/reel)',
            'required': True
        })
    )
    

class YourForm(forms.Form):
    video_url = forms.URLField(
        label="Facebook Video URL",
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Facebook video link...'
        })
    )
    
    
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Your Name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Your Email'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Your Message'
    }))