from django.shortcuts import render
from django.urls import reverse_lazy
from django.http import Http404
from django.core.exceptions import (
    ImproperlyConfigured,
    FieldError,
)

from django.views.generic.base import (
    ContextMixin, 
    TemplateResponseMixin, 
    View,
)
from django.views.generic.edit import ModelFormMixin
from django.views.generic.list import MultipleObjectMixin

from django.contrib.admin.utils import flatten_fieldsets
from django.db.models import ForeignKey

##
from .models import Transaction, TransactionRecord
from .utils import ph_modelform_factory, ph_inlineformset_factory


def index(request):
    return render(request, "psqlj/index.html", {})


######################
# TODO:
#  make the Mixin classes so it can be used with Dates Mixins



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
    
    def get_context_data(self, **kwargs):
        """extend from parent"""
        
        # inlineformset need context["form"] value, get context from super
        context = super().get_context_data(**kwargs)

        # 1. add inlineformset to context
        if "inlineformset" not in context:
            context["inlineformset"] = self.get_inline_formset(context)

        return context


    def get_form_class(self):
        """override ModelFormMixin's get_form_class()"""

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

    ##
    def get_help_texts(self):
        return self.help_texts

    def get_inline_formset(self, context):
        if self.inline:
        
            # Instantiate the inline model wrapper
            iw = self.inline()      
            Formset        = iw.create_formset(self.model)
            formset_params = iw.get_formset_params(context)

            return Formset(**formset_params)

        return None




class InlineModelFormMixin(FieldsetsModelFormMixin):
    """Wrapper for inline-model"""
    fk_name = None
    extra = 5

    _default_fkfield = None

    def create_formset(self, master_model=None):
        if master_model is None:
            master_model = self.get_master_model()

        return ph_inlineformset_factory(
                    master_model,
                    self.model,
                    **self.get_createformset_kwargs()
                )

    def get_formset_params(self, context):
        """
        Provide the standard parameters for a Formset class based on the context.
        """
        params = { 
            "prefix"    : self.get_prefix(),
            "instance"  : context["form"].instance,
        }
        return params


    def get_allinlines_of(self, master_obj):
        queryset = self.get_queryset()

        origin_fkname = self.get_default_fk_name()
        queryset = queryset.filter(**{origin_fkname: master_obj})

        return list(queryset)

    ##
    def get_master_model(self):
        """
        Return remote model of the first ForeignKey field.
        """
        if self._default_fkfield is None:
            self._get_default_fk_field()
        return self._default_fkfield.remote_field.model


    def get_createformset_kwargs(self):
        kwargs = {
            "fk_name" : self.get_fk_name(),
            "fields"  : self.get_fields(),
            "extra"   : self.get_extra(),
            "can_delete_extra": False,
        }
        return kwargs


    def get_fk_name(self):
        return self.fk_name

    def get_extra(self):
        return self.extra

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


class ListObjectWrapper(MultipleObjectMixin):
    model = Transaction


class MasterCreateView(TemplateResponseMixin, BaseMasterCreateView):
    model = Transaction
    fields = ["tdate", "desc"]
    help_texts = {
            "tdate": "Transcation Date..",
            "desc" : "Description..",
        }
    template_name = "psqlj/psqlj_createview.html"
    inline = InlineModelWrapper
    listobject = ListObjectWrapper
    

########################
########################

class Subview:
    def __init__(self, request, **kwargs):
        self.request = request
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise TypeError(
                    "%s() received an invalid keyword %r."
                    "It only accepts arguments that are already "
                    "attributes of the class." % (self.__class__, key)
                
            setattr(self, key, value)


class ModelFormSubview(ModelFormMixin, Subview):
    help_texts = None


    def get_form_class(self):
        """override ModelFormMixin's get_form_class()"""

        if self.model is not None:
            model = self.model
        elif getattr(self, "object", None) is not None:
            model = self.object.__class__
        else:
            model = self.get_queryset().model

        if self.fields is None:
            raise ImproperlyConfigured(
                "Define either 'fieldsets' or 'fields' to use "
                "MasterModelFormMixin (base class of %s)." 
                % self.__class__.__name__
            )

        try:
            return ph_modelform_factory(
                    model, 
                    fields=self.fields,
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


class InlineModelFormSubview(InlineModelFormMixin):
    model = None

    def get_context_data(self, **kwargs):
        pass


class ModelListSubview(MultipleObjectMixin):
    model = None

    def get_context_data(self, **kwargs):
        pass


class ViewOne(TemplateResponseMixin, View, ContextMixin):
    model_subview = None
    inline_model = None
    model_list = None
    template_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if model_subview is not None:
            msv = model_subview(self.request)
            context.update(msv.get_context_data())

        if inline_model is not None:
            # idem

        if model_list is not None:
            # idem

    def get(self):
        pass

    def post(self):
        pass

