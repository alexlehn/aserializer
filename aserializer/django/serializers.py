# -*- coding: utf-8 -*-
import inspect

from aserializer.utils import py2to3
from aserializer.base import Serializer, SerializerBase
from aserializer import fields as serializer_fields

try:
    from django.db import models as django_models
    model_field_mapping = {
        django_models.AutoField: serializer_fields.IntegerField,
        django_models.FloatField: serializer_fields.FloatField,
        django_models.IntegerField: serializer_fields.IntegerField,
        django_models.PositiveIntegerField: serializer_fields.PositiveIntegerField,
        django_models.SmallIntegerField: serializer_fields.IntegerField,
        django_models.PositiveSmallIntegerField: serializer_fields.PositiveIntegerField,
        django_models.DateTimeField: serializer_fields.DatetimeField,
        django_models.DateField: serializer_fields.DateField,
        django_models.TimeField: serializer_fields.TimeField,
        django_models.DecimalField: serializer_fields.DecimalField,
        django_models.EmailField: serializer_fields.EmailField,
        django_models.CharField: serializer_fields.StringField,
        django_models.URLField: serializer_fields.UrlField,
        django_models.SlugField: serializer_fields.StringField,
        django_models.TextField: serializer_fields.StringField,
        django_models.CommaSeparatedIntegerField: serializer_fields.StringField,
        django_models.BooleanField: serializer_fields.BooleanField,
        django_models.NullBooleanField: serializer_fields.BooleanField,
    }
except ImportError:
    django_models = None
    model_field_mapping = {}


class DjangoModelSerializerBase(SerializerBase):

    def __new__(cls, name, bases, attrs):
        new_class = super(DjangoModelSerializerBase, cls).__new__(cls, name, bases, attrs)
        cls.set_fields_from_model(new_class=new_class,
                                  fields=new_class._base_fields,
                                  model=new_class._meta.model)
        return new_class

    @staticmethod
    def get_all_fieldnames(fields):
        result = []
        for name, field in fields.items():
            result.append(name)
            if field.map_field:
                result.append(field.map_field)
        return list(set(result))

    @classmethod
    def set_fields_from_model(cls, new_class, fields, model):
        setattr(new_class, 'model_fields', [])
        if django_models is None or model is None:
            return
        opts = model._meta.concrete_model._meta

        all_field_names = cls.get_all_fieldnames(fields)
        for model_field in opts.fields:
            if model_field.name not in all_field_names:
                if cls.add_model_field(fields, model_field):
                    new_class.model_fields.append(model_field.name)
            else:
                new_class.model_fields.append(model_field.name)

    @staticmethod
    def get_field_class(model_field, mapping=None):
        if mapping is None:
            mapping = model_field_mapping
        for model in mapping:
            if isinstance(model_field, model):
                return mapping[model]
        return None

    @classmethod
    def get_field_from_modelfield(cls, model_field, **kwargs):
        field_class = cls.get_field_class(model_field)
        if model_field.primary_key:
            kwargs['identity'] = True
            kwargs['required'] = False
            kwargs['on_null'] = serializer_fields.HIDE_FIELD
        if model_field.null or model_field.blank:
            kwargs['required'] = False
        if model_field.has_default():
            kwargs['default'] = model_field.get_default()
        if model_field.flatchoices:
            kwargs['choices'] = model_field.flatchoices
            return serializer_fields.ChoiceField(**kwargs)

        if isinstance(model_field, django_models.CharField):
            kwargs.update({'max_length': getattr(model_field, 'max_length')})
        elif isinstance(model_field, django_models.DecimalField):
            kwargs.update({'decimal_places': getattr(model_field, 'decimal_places')})
        if field_class is None:
            return
        return field_class(**kwargs)

    @classmethod
    def add_model_field(cls, fields, model_field, **kwargs):
        _field = cls.get_field_from_modelfield(model_field, **kwargs)
        if _field is None:
            return False
        _field.add_name(model_field.name)
        fields[model_field.name] = _field
        return True


class NestedDjangoModelSerializer(py2to3.with_metaclass(DjangoModelSerializerBase, Serializer)):
    with_registry = False


class DjangoModelSerializer(py2to3.with_metaclass(DjangoModelSerializerBase, Serializer)):
    pass
