from django.shortcuts import render
from django.core.exceptions import ImproperlyConfigured

from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import ModelFormMixin, ProcessFormView

from django.contrib.admin.utils import flatten_fieldsets
from django.urls import reverse
from django.http import HttpResponseRedirect

##
from .models import Transaction, TransactionRecord
from .utils import ph_modelform_factory, ph_inlineformset_factory


def index(request):
    return render(request, "psqlj/index.html", {})


######################
# TODO:
#  make the Mixin classes so it can be used with Dates Mixins


class PhModelFormMixin(ModelFormMixin):
    """
    copying Django Admin fieldsets option and use modified _factory()
    which use help_text as help label.
    """
    fieldsets = None
    help_texts = None
    

    def get_context_data(self, **kwargs):
        """
        Insert additional information to show:
        - list of model's object
        """
        if "object_list" not in kwargs:
            kwargs["object_list"] = self.model._default_manager.all()
        return super().get_context_data(**kwargs)


    def get_form_class(self):
        """override ModelFormMixin's get_form_class()"""

        if self.model is not None:
            model = self.model
        elif getattr(self, "object", None) is not None:
            model = self.object.__class__
        else:
            model = self.get_queryset().model

        fields = self.get_fields()
        if fields is None:
            raise ImproperlyConfigured(
                "Define either 'fieldsets' or 'fields' to use "
                "PhModelFormMixin (base class of %s)." 
                % self.__class__.__name__
            )

        try:
            return ph_modelform_factory(
                    model, 
                    fields=fields,
                    help_texts=self.get_help_texts(),
            )

        except FieldError as e:
            raise FieldError(
                "%s. Check fieldsets/fields attributes of class %s."
                % (e, self.__class__.__name__)
            )

    ##
    def get_help_texts(self):
        return self.help_texts


    def get_fields(self):
        if self.fieldsets:
            return flatten_fieldsets(self.fieldsets)
        return self.fields

    def get_fieldsets(self):
        if self.fieldsets:
            return self.fieldsets
        return [(None, {"fields": self.get_fields()})]


class FormsetMixin():

    def get_formset(self):
        Formset = self.create_inline_formset()
        if Formset:
            return Formset(**self.get_formset_kwargs())
        else:
            return None

    def create_inline_formset(self):
        return None

    def get_formset_kwargs(self):
        """
        Return the keyword arguments for instantiating the formset.
        """
        kwargs = { "instance": self.object }

        if self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs


class BasePhCreateView(TemplateResponseMixin, 
                       PhModelFormMixin, 
                       ProcessFormView,
                       FormsetMixin):
    """Base Master Model Form view"""
    object = None

    def get_context_data(self, **kwargs):
        """
        Formset is to be added after object and form are in context.
        """
        context = super().get_context_data(**kwargs)

        formset = self.get_formset()
        if (formset is not None) and ("formset" not in context):
            context['formset'] = formset
        return context


    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.get_formset()

        if form.is_valid() and (formset is None or formset.is_valid()):
            return self.form_valid((form, formset,))
        else:
            return self.form_invalid((form, formset,))


    def form_valid(self, forms):
        form, formset = forms

        self.object = form.save()
        if formset:
            formset.instance = self.object
            formset.save()
        return HttpResponseRedirect(self.get_success_url())


    def form_invalid(self, forms):
        form, formset = forms

        return self.render_to_response(
                    self.get_context_data(form=form,
                                          formset=formset
                    ))


class MasterCreateView(BasePhCreateView):
    model = Transaction
    fields = ["tdate", "desc"]
    help_texts = {
            "tdate": "Transcation Date..",
            "desc" : "Description..",
        }
    template_name = "psqlj/psqlj_createview.html"
   

    def create_inline_formset(self):
        return ph_inlineformset_factory(
                    Transaction,
                    TransactionRecord,
                    fields      = ['account', 'amount', 'record_num'],
                    extra       = 2,
                    help_texts  = {
                        "account": "Account no...",
                        "amount" : "Amount...",
                    },
                    can_delete_extra = False,
                )
   
    def get_success_url(self):
       return reverse("psqlj:index")

