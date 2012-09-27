from django import forms

class UploadForm(forms.Form):
    file = forms.FileField()
    name = forms.CharField(max_length=50)

class AnswerForm(forms.Form):
    answer = forms.CharField(max_length=200)
    result = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[('correct', 'correct!'),
                 ('presumed_correct', 'presumed correct'),
                 ('incorrect', 'incorrect')],
        label='')
