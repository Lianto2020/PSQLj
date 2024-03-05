
from django.forms import (
    ModelForm,
    modelform_factory,
    inlineformset_factory,
)

class PhModelForm(ModelForm):
    template_name = "psqlj/forms/form-test.html"
#    template_name_div = "psqlj/forms/div.html"


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for formfield in self.fields.values():
            formfield.widget.attrs["placeholder"] = formfield.help_text
            formfield.widget.attrs.update({"class": "form-control"})


def ph_modelform_factory(model, form=PhModelForm, **kwargs):
    """
    Modify Django's modelform_factory()
    """
    return modelform_factory(model, form, **kwargs)

def ph_inlineformset_factory(parent_model, model, form=PhModelForm, **kwargs):
    return inlineformset_factory(parent_model, model, form, **kwargs)
