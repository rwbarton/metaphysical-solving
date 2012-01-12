from django import forms

class UploadForm(forms.Form):
    file = forms.FileField()
    name = forms.CharField(max_length=50)

