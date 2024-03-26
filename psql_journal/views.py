from django.shortcuts import render
from django.urls import reverse

from django.forms.models import (
    ModelForm,
    inlineformset_factory,
)
from django.forms import fields as form_fields
from django.forms import widgets as form_widgets

##
from .models import Transaction, TransactionRecord
from .viewlib import BasePhCreateView


def index(request):
    return render(request, "psqlj/index.html", {})




class TransactionCreateForm(ModelForm):
    template_name = "psqlj/forms/transaction-createform.html"
    class Meta:
        model = Transaction
        fields = ["tdate", "desc"]
        widgets = {
            "tdate": form_widgets.DateInput(attrs={
                        "placeholder": "dd/mm/yy",
                        "class": "form-control"
                    }),
            "desc": form_widgets.TextInput(attrs={
                        "placeholder": "Description..",
                        "class": "form-control"
                    }),
        }


class TransactionRecordCreateForm(ModelForm):
    template_name = "psqlj/forms/transactionrecord-createform.html"
    class Meta:
        model = TransactionRecord
        fields = ["account", "amount", "record_num"]
        widgets = {
            "account": form_widgets.TextInput(attrs={
                        "placeholder": "acc no",
                        "class": "form-control"
                    }),
            "amount": form_widgets.NumberInput(attrs={
                        "placeholder": "amount",
                        "class": "form-control"
                    }),
            "record_num": form_widgets.NumberInput(attrs={
                        "placeholder": "no",
                        "class": "form-control"
                    }),
        }



class MasterCreateView(BasePhCreateView):
    model = Transaction
    form_class = TransactionCreateForm
    template_name = "psqlj/psqlj_createview.html"
   

    def create_inline_formset(self):
        return inlineformset_factory(
                    Transaction,
                    TransactionRecord,
                    form = TransactionRecordCreateForm,
                    extra = 2,
                    can_delete_extra = False,
                )
   
    def get_success_url(self):
       return reverse("psqlj:index")

