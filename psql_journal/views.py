from django.shortcuts import render
from django.urls import reverse_lazy
from django.core.exceptions import ImproperlyConfigured

from django.views.generic.edit import CreateView, ModelFormMixin
from django.views.generic import ListView
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View
from django.views.generic.list import MultipleObjectMixin

from django.forms import (
    modelformset_factory, 
    modelform_factory, 
    inlineformset_factory,
)

from .models import (
    TwoInputFields, 
    Transaction, 
    TransactionRecord,
)
from django.contrib.admin.utils import flatten_fieldsets
from django.db.models import ForeignKey
from django.http import Http404

from .utils import ph_modelform_factory, ph_inlineformset_factory


def index(request):
    return render(request, "psqlj/index.html", {})


class TwoInputCreateView(CreateView):
    model = TwoInputFields
    fields = ["str1", "str2"]
    template_name = "psqlj/add.html"
    success_url = reverse_lazy("psqlj:list")

    
class TwoInputListView(ListView):
    model = TwoInputFields
    template_name = "psqlj/list.html"



##############
# a Formset CreateView
#TODO: formset_valid() and formset_invalid()

class FormsetMixin(ContextMixin):

    initial = {}
    formset_class = None
    success_url = None
    prefix = None

    def get_initial(self):
        return self.initial.copy()

    def get_prefix(self):
        return self.prefix

    def get_formset_class(self):
        return self.formset_class

    def get_formset(self, formset_class=None):
        if formset_class is None:
            formset_class = self.get_formset_class()
        return formset_class(**self.get_formset_kwargs())

    def get_formset_kwargs(self):
        kwargs = {
            "initial"   : self.get_initial(),
            "prefix"    : self.get_prefix(),
        }
        if self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def get_success_url(self):
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return str(self.success_url)

    def form_valid(self, formset):
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, formset):
        return self.render_to_response(self.get_context_data(formset=formset))

    def get_context_data(self, **kwargs):
        if "formset" not in kwargs:
            kwargs["formset"] = self.get_formset()
        return super().get_context_data(**kwargs)


class ModelFormsetMixin(FormsetMixin):
    fields = None

    def get_formset_class(self):
        if self.fields is not None and self.formset_class:
            raise ImproperlyConfigured("Specifying both 'fields' and 'formset_class' is not permitted."
            )
        if self.formset_class:
            return self.formset_class
        else:
            if self.model is not None:
                model = self.model
            else:
                model = self.get_queryset().model

            if self.fields is None:
                raise ImproperlyConfigured(
                    "Using ModelFormsetMixin without "
                    "the 'fields' attribute is prohibited."
                )
            return modelformset_factory(model, **self.get_modelformset_factory_kwargs())

    def get_modelformset_factory_kwargs(self):
        kwargs = {
            "fields": self.fields,
        }
        return kwargs


class ProcessFormsetView(View):
    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        if formset.is_valid():
            return self.form_valid(formset)
        else:
            return self.form_invalid(formset)

    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)
    

class BaseMultipleCreateView(ModelFormsetMixin, ProcessFormsetView):
    """Base view to create mulitple objects."""
    extra = 10
    max_num = 10

    def get_modelformset_factory_kwargs(self):
        kwargs = super().get_modelformset_factory_kwargs()
        kwargs.update(
            {
                "extra" : self.extra,
                "max_num" : self.max_num,
            }
        )
        return kwargs

class TwoInputMultipleCreateView(TemplateResponseMixin, BaseMultipleCreateView):
    """Finally, a View to create multiple objects."""

    model = TwoInputFields
    fields = ["str1", "str2"]
    template_name = "psqlj/multiple_add.html"
    success_url = reverse_lazy("psqlj:list")

    def get_formset_kwargs(self):
        """ 
        BaseModelFormSet will fill the existing values to input elements 
        according to the model's queryset when it contruct the form. 
        This is useful when we want to edit values.
        But we want to create new ones here, so set queryset to none.
        """
        kwargs = super().get_formset_kwargs()
        if self.request.method == "GET":
            kwargs.update(
                {
                    "queryset": TwoInputFields.objects.none(),
                }
            )
        return kwargs

######################
# TODO:
#  make the Mixin classes so it can be used with Dates Mixins

# a "Many To One" CreateView, 
#   take 1 parent model(One) and 1 child model(Many), 
#   so the user only need to focus on the template (UI presentation)

# PLAN:
#  needed functionality from:
#   TemplateResponseMixin
#   ContextMixin
#    FormMixin (lack INLINES)
#    SingleObjectMixin (lack INLINES)
#     ModelFormMixin (lack INLINES)
#   View
#    ProcessFormView (need to modify??)
#

class TmpFieldsetsMixin(ModelFormMixin):
    fieldsets = None
    object = None

    def get_fields(self):
        if self.fieldsets:
            return flatten_fieldsets(self.fieldsets)
        return self.fields

    def get_fieldsets(self):
        if self.fieldsets:
            return self.fieldsets
        return [(None, {"fields": self.get_fields()})]



class MainFormMixin(TmpFieldsetsMixin):
    inline = None            # one inline class

    #def get_inlines(self):
    #    return self.inlines

    def get_form_class(self):
        if self.model is not None:
            model = self.model
        elif getattr(self, "object", None) is not None:
            model = self.object.__class__
        else:
            model = self.get_queryset().model

        fields = self.get_fields()
        if self.fields is None:
            raise ImproperlyConfigured(
                "Define either 'fieldsets' or 'fields' to use "
                "CompleteFormMixin (base class of %s)." 
                % self.__class__.__name__
            )

        try:
            return modelform_factory(model, fields=fields)
        except FieldError as e:
            raise FieldError(
                "%s. Check fieldsets/fields attributes of class %s."
                % (e, self.__class__.__name__)
            )

    def create_formsets(self):
        if self.inline:
            inline = self.inline()
            Formset = inline.get_formset()
            formset_params = inline.get_formset_kwargs()

            formset = Formset(**formset_params)
            return formset

        return None
            

class InlineFormsetMixin(TmpFieldsetsMixin):
    parent_model = None
    fk_name = None
    extra = 5

    prefix = None

    def get_formset(self, **kwargs):
        defaults = {
            "fk_name" : self.fk_name,
            "extra" : self.extra,
            "fields": self.get_fields(),
            **kwargs,
        }
        return inlineformset_factory(self.parent_model, self.model, **defaults) 

    def get_formset_kwargs(self, **kwargs_ext):
        kwargs = {
            "prefix": self.prefix,

        }
        kwargs.update(kwargs_ext)
        return kwargs


class ProcessMainFormView(View):

    def get(self, request, *args, **kwargs):
        nkwargs = {
            "form": self.get_form(),
            "formset": self.create_formsets(),
        }
        return self.render_to_response(self.get_context_data(**nkwargs))


class BaseMainFormView(MainFormMixin, ProcessMainFormView):
    """A Base view for testing"""

class InlineFormset(InlineFormsetMixin):
    model = TransactionRecord
    fields = ["account", "amount"]
    parent_model = Transaction

class MainFormView(TemplateResponseMixin, BaseMainFormView):
    model = Transaction
    fields = ["tdate", "desc"]
    template_name = "psqlj/mainform_test.html"
    inline = InlineFormset


#####################################
#####################################
#####################################
# to import: SingleObjectMixin, models.ForeignKey

class FieldsetsModelFormMixin(ModelFormMixin):
    """Add and prioritize fieldsets."""
    fieldsets = None
    object = None

    def get_fields(self):
        if self.fieldsets:
            return flatten_fieldsets(self.fieldsets)
        return self.fields

    def get_fieldsets(self):
        if self.fieldsets:
            return self.fieldsets
        return [(None, {"fields": self.get_fields()})]



class MasterModelFormMixin(FieldsetsModelFormMixin):
    """the parent with 0 or 1 child/inline"""
    inline = None
    help_texts = None
    
    def get_help_texts(self):
        return self.help_texts

    def get_form_class(self):
        if self.model is not None:
            model = self.model
        elif getattr(self, "object", None) is not None:
            model = self.object.__class__
        else:
            model = self.get_queryset().model

        fields = self.get_fields()
        if self.fields is None:
            raise ImproperlyConfigured(
                "Define either 'fieldsets' or 'fields' to use "
                "MasterModelFormMixin (base class of %s)." 
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


    def get_inline_formset(self, **extfsparams):
        if self.inline:
            # Instantiate the inline model wrapper
            iw = self.inline()      
            Formset        = iw.create_formset()
            formset_params = iw.get_formset_params(**extfsparams)

            return Formset(**formset_params)

        return None


    def get_context_data(self, **kwargs):
        
        # we need context["form"] value, so lets execute super first
        context = super().get_context_data(**kwargs)

        formset_kwargs = { 
            "instance": context["form"].instance, 
        }
        # if we are editing an existing object
        if self.request.method == "GET" and self.object:
            formset_kwargs["instance"] = self.object 

        if "inlineformset" not in context:
            context["inlineformset"] = self.get_inline_formset(**formset_kwargs)
        return context


class InlineModelFormMixin(FieldsetsModelFormMixin):
    """Wrapper for inline-model"""
    fk_name = None
    extra = 5

    _default_fkfield = None

    def get_fk_name(self):
        return self.fk_name

    def _get_default_fk_field(self):
        """Save the first Foreign Key field."""
        opts = self.model._meta
        for f in opts.fields:
            if isinstance(f, ForeignKey):
                self._default_fkfield = f
                #breakpoint()
                return f

    def get_default_fk_name(self):
        if self._default_fkfield is None:
            self._get_default_fk_field()
        return self._default_fkfield.name

    def get_extra(self):
        return self.extra

    def get_master_model(self):
        """
        Return remote model of the first ForeignKey field.
        Currently using auto-finding. 
        Another implementation is give the parent_model as arg.
        """
        if self._default_fkfield is None:
            self._get_default_fk_field()
        return self._default_fkfield.remote_field.model


    def create_formset(self):
        return ph_inlineformset_factory(
                    self.get_master_model(),
                    self.model,
                    **self.get_createformset_kwargs()
                )

    def get_createformset_kwargs(self):
        kwargs = {
            "fk_name" : self.get_fk_name(),
            "fields"  : self.get_fields(),
            "extra"   : self.get_extra(),
            "can_delete_extra": False,
        }
        return kwargs

    def get_formset_params(self, **extparams):
        params = {
            "prefix": self.get_prefix(),
        }
        params.update(extparams)
        return params

    def get_allinlines_of(self, master_obj):
        queryset = self.get_queryset()

        origin_fkname = self.get_default_fk_name()
        queryset = queryset.filter(**{origin_fkname: master_obj})

        return list(queryset)


class ProcessMasterFormView(View):
    """Render a form with its inlines on GET and processes them on POST."""

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        raise Http404("Post not ready yet")

    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class BaseMasterCreateView(MasterModelFormMixin, ProcessMasterFormView):
    """Base Master Model Form view"""
    object = None


class InlineModelWrapper(InlineModelFormMixin):
    model = TransactionRecord
    fields = ["account", "amount"]
    help_texts = {
            "account": "Account no...",
            "amount" : "Amount...",
        }

    def get_createformset_kwargs(self):
        kwargs = super().get_createformset_kwargs()
        kwargs["help_texts"] = self.help_texts
        return kwargs


class MasterCreateView(TemplateResponseMixin, BaseMasterCreateView):
    model = Transaction
    fields = ["tdate", "desc"]
    help_texts = {
            "tdate": "Transcation Date..",
            "desc" : "Description..",
        }
    template_name = "psqlj/psqlj_createview.html"
    inline = InlineModelWrapper

