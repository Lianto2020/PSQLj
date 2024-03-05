from django import forms

class DualTextInputWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = [
            forms.TextInput(),
            forms.TextInput(),
        ]
        super().__init__(widgets, attrs)

    def decompres(self, value):
        return [None, None]
