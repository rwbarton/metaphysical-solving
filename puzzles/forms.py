from django import forms

class UploadForm(forms.Form):
    file = forms.FileField()
    name = forms.CharField(max_length=50)

class AnswerForm(forms.Form):
    answer = forms.CharField(max_length=200)

    request = forms.BooleanField(label="Request?", required=False)

    # The default required=True means you have to check the box...
    backsolved = forms.BooleanField(label="Backsolved?", required=False)

    phone = forms.CharField(max_length=30)
