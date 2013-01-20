from django import forms

class UploadForm(forms.Form):
    file = forms.FileField()
    name = forms.CharField(max_length=50)

class AnswerForm(forms.Form):
    answer = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=64)
