# -*- coding: utf-8 -*-

import uuid
import decimal

from collections import Iterable
from aserializer.fields.base import BaseSerializerField, IgnoreField, SerializerFieldValueError
from aserializer.fields import validators as v


class TypeField(BaseSerializerField):

    def __init__(self, name, fixed=False, *args, **kwargs):
        super(TypeField, self).__init__(*args, **kwargs)
        self.name = name
        self.identity = True
        self.error_messages = {}
        self.fixed = fixed

    def validate(self):
        pass

    def set_value(self, value):
        if not self.fixed:
            self.name = value

    def to_native(self):
        return unicode(self.name)

    def to_python(self):
        return unicode(self.name)

    def __get__(self, instance, owner):
        pass

    def __set__(self, instance, value):
        pass


class IntegerField(BaseSerializerField):

    validators = [v.validate_integer, ]

    def __init__(self, max_value=None, min_value=None, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)
        if max_value is not None:
            self._validators.append(v.MaxValueValidator(max_value))
        if min_value is not None:
            self._validators.append(v.MinValueValidator(min_value))

    @staticmethod
    def to_int(value):
        if value in v.VALIDATORS_EMPTY_VALUES:
            return None
        return int(value)

    def _to_native(self):
        return self.to_int(self.value)

    def _to_python(self):
        return self.to_int(self.value)


class FloatField(IntegerField):
    validators = [v.validate_float, ]

    @staticmethod
    def to_float(value):
        if value in v.VALIDATORS_EMPTY_VALUES:
            return None
        return float(value)

    def _to_native(self):
        return self.to_float(self.value)

    def _to_python(self):
        return self.to_float(self.value)


class DecimalField(IntegerField):
    OUTPUT_AS_FLOAT = 0
    OUTPUT_AS_STRING = 1
    validators = [v.validate_decimal, ]

    def __init__(self, decimal_places=3, precision=None, max_value=None, min_value=None, output=None, **kwargs):
        super(DecimalField, self).__init__(max_value=max_value, min_value=min_value, **kwargs)
        self.decimal_places = decimal_places
        self.precision = precision
        if self.value and not isinstance(self.value, decimal.Decimal):
            self.set_value(self.value)
        if output is None or output not in (0, 1):
            self.output = self.OUTPUT_AS_FLOAT
        else:
            self.output = output

    def set_value(self, value):
        context = decimal.getcontext().copy()
        if self.precision is not None:
            context.prec = self.precision
        if isinstance(value, decimal.Decimal):
            self.value = value.quantize(decimal.Decimal(".1") ** self.decimal_places, context=context)
        elif isinstance(value, (int, long, float,)):
            self.value = decimal.Decimal(value).quantize(decimal.Decimal(".1") ** self.decimal_places, context=context)
        elif isinstance(value, basestring):
            try:
                self.value = decimal.Decimal(value).quantize(decimal.Decimal(".1") ** self.decimal_places, context=context)
            except:
                self.value = value
        else:
            self.value = None

    def _to_native(self):
        if self.value in v.VALIDATORS_EMPTY_VALUES:
            return None
        if self.output == self.OUTPUT_AS_STRING:
            result = str(self.value)
        else:
            result = float(u'{}'.format(self.value))
        return result

    def _to_python(self):
        if self.value in v.VALIDATORS_EMPTY_VALUES:
            return None
        return self.value

    @staticmethod
    def __pre_eq__(other):
        if isinstance(other, decimal.Decimal):
            return other
        elif isinstance(other, (int, long)):
            return decimal.Decimal(other)
        elif isinstance(other, float):
            return decimal.Decimal(str(other))
        elif isinstance(other, basestring):
            try:
                d = decimal.Decimal(str(other))
            except:
                raise ValueError()
            else:
                return d
        raise ValueError()

    def __eq__(self, other):
        if not isinstance(self.value, decimal.Decimal):
            return False
        try:
            _other = self.__pre_eq__(other=other)
        except ValueError:
            return False
        else:
            return self.value == _other


class BooleanField(BaseSerializerField):

    def set_value(self, value):
        if value in v.VALIDATORS_EMPTY_VALUES:
            self.value = None
        elif isinstance(value, basestring) and value.lower() in ('false', '0'):
            self.value = False
        else:
            self.value = bool(value)

    def _to_native(self):
        return self.value

    def _to_python(self):
        return self.value

    def to_native(self):
        result = super(BooleanField, self).to_native()
        return bool(result)


class StringField(BaseSerializerField):
    validators = [v.validate_string, ]

    def __init__(self, max_length=None, min_length=None, **kwargs):
        super(StringField, self).__init__( **kwargs)
        if max_length is not None:
            self._validators.append(v.MaxStringLengthValidator(max_length))
        if min_length is not None:
            self._validators.append(v.MinStringLengthValidator(min_length))

    @staticmethod
    def to_unicode(value):
        if value in v.VALIDATORS_EMPTY_VALUES:
            return u''
        return unicode(value)

    def _to_native(self):
        return self.to_unicode(self.value)

    def _to_python(self):
        return self.to_unicode(self.value)


class EmailField(StringField):
    validators = [v.validate_email, ]


class UUIDField(BaseSerializerField):
    validators = [v.validate_uuid, ]

    def _to_native(self):
        if self.value in v.VALIDATORS_EMPTY_VALUES:
            return u''
        return unicode(self.value)

    def _to_python(self):
        if self.value in v.VALIDATORS_EMPTY_VALUES:
            return None
        if isinstance(self.value, uuid.UUID):
            return self.value
        self.value = uuid.UUID(str(self.value))
        return self.value


class UrlField(BaseSerializerField):

    validators = [v.validate_url, ]

    def __init__(self, base=None, *args, **kwargs):
        super(UrlField, self).__init__(*args, **kwargs)
        self.uri_base = base
        if self.uri_base and not str(self.uri_base).endswith('/'):
            self.uri_base = '{}/'.format(self.uri_base)
        if self.value:
            self.set_value(value=self.value)

    @staticmethod
    def to_unicode(value):
        if value in v.VALIDATORS_EMPTY_VALUES:
            return u''
        return unicode(value)

    def set_value(self, value):
        if self.uri_base:
            self.value = '{}{}'.format(self.uri_base, value)
        else:
            self.value = value

    def _to_native(self):
        return self.to_unicode(self.value)

    def _to_python(self):
        return self.to_unicode(self.value)


class ChoiceField(BaseSerializerField):

    error_messages = {
        'required': 'This field is required.',
        'invalid': 'Invalid choice value.',
    }

    def __init__(self, choices=(), *args, **kwargs):
        super(ChoiceField, self).__init__(*args, **kwargs)
        self.choices = choices
        self.python_value = None

    def validate(self):
        super(ChoiceField, self).validate()
        if self.value in v.VALIDATORS_EMPTY_VALUES:
            return
        for val in self.choices:
            if isinstance(val, (list, tuple)):
                try:
                    val2 = val[0]
                    key2 = val[1]
                except:
                    continue
                else:
                    if self.value == key2:
                        self.python_value = val2
                        return
            else:
                if self.value == val:
                    self.python_value = val
                    return
        raise SerializerFieldValueError(self._error_messages['invalid'], field_names=self.names)

    def _to_native(self):
        return self.value

    def _to_python(self):
        return self.python_value


class ListField(BaseSerializerField):

    def __init__(self, field, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)
        self._field_cls = field
        self.items = []
        self._python_items = []
        self._native_items = []

    def validate(self):
        if self.items:
            _errors = []
            for field in self.items:
                try:
                    field.validate()
                except SerializerFieldValueError, e:
                    _errors.append(e.errors)
            if _errors:
                raise SerializerFieldValueError(_errors)
        elif self.required:
            raise SerializerFieldValueError(self._error_messages['required'], field_names=self.names)

    def add_item(self, value):
        field = self._field_cls()
        field.set_value(value=value)
        self.items.append(field)

    def set_value(self, value):
        self.items[:] = []
        self._native_items[:] = []
        self._python_items[:] = []
        if isinstance(value, Iterable):
            for item in value:
                self.add_item(value=item)

    def _to_native(self):
        if not self._native_items:
            for field in self.items:
                self._native_items.append(field.to_native())
        return self._native_items

    def _to_python(self):
        if not self._python_items:
            for field in self.items:
                self._python_items.append(field.to_python())
        return self._python_items


    def append(self, value):
        self.add_item(value=value)
        self.validate()

    def __iter__(self):
        return self.to_python().__iter__()

    def __get__(self, instance, owner):
        if instance is None:
            return self
        field = self._get_field_from_instance(instance=instance)
        return field

    def __set__(self, instance, value):
        if instance is None:
            return
        field = self._get_field_from_instance(instance=instance)
        if field is None:
            return
        self.ignore = False
        for name in self.names:
            try:
                value = instance.clean_field_value(name, value)
            except IgnoreField:
                self.ignore = True
        field.set_value(value=value)
        field.validate()
        instance.update_field(field)

    def __setitem__(self, i, value):
        del self.items[i]
        self.add_item(value=value)
        self.validate()

    def __getitem__(self, y):
        return self.to_python()[y]

    def __len__(self):
        return len(self.items)

    def __contains__(self, value):
        return value in self.to_python()
