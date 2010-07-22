from django.db import models
from django.db.models import Field, CharField
from django.utils.translation import ugettext_lazy as _

#class ListField(models.Field):
#    def __init__(self, field_type, *args, **kwargs):
#        self.field_type = field_type
#        kwargs['blank'] = True
#        if 'default' not in kwargs:
#            kwargs['default'] = lambda: None if self.null else []
#        super(ListField, self).__init__(*args, **kwargs)
#
#    def db_type(self, connection):
#        if hasattr(self.field_type, "db_type"):
#            return 'ListField:' + self.field_type.db_type(connection=connection)
#        return 'ListField: %s' % self.field_type
#
#    def call_for_each(self, function_name, values, *args, **kwargs):
#        #forcing type cast
#        if isinstance(values, (list, tuple)) and len(values):
#            for i, value in enumerate(values):
#                try:
#                    values[i] = getattr(self.field_type, function_name)(value, *args, **kwargs)
#                except AttributeError:
#                    #fix to allow str, unicode, datetime elements
#                    pass
#        return values
#
#    def to_python(self, value):
#        return self.call_for_each( 'to_python', value)
#
#    def get_prep_value(self, value):
#        return self.call_for_each('get_prep_value', value)
#
#    def get_db_prep_value(self, value, connection, prepared=False):
#        return self.call_for_each('get_db_prep_value', value, connection=connection,
#            prepared=prepared)
#
#    def get_db_prep_save(self, value, connection):
#        return self.call_for_each('get_db_prep_save', value, connection=connection)
#
#    def formfield(self, **kwargs):
#        return None

class ListField(Field):
    """A list field that wraps a standard field, allowing multiple instances
    of the field to be used as a list in the database.
    """

    default_error_messages = {
        'invalid': _(u'This value must be a list or an iterable.'),
        'invalid_value': _(u'Invalid value in list.'),
    }

    description = _("List Field")
    _internaltype = None
    def __init__(self, type, *args, **kwargs):
        self._internaltype = type
        kwargs['blank'] = True
        if 'default' not in kwargs:
            kwargs['default'] = []
            
        Field.__init__(self, *args, **kwargs)

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. 
        """
        if not isinstance(value, list) and (not hasattr(value, "__iter__")):
            raise exceptions.ValidationError(self.error_messages['invalid'])

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])
        if self._internaltype is not None:
            for v in value:
                if not isinstance(v, self._internaltype):
                    raise exceptions.ValidationError(self.error_messages['invalid_value'])
        
    def get_prep_value(self, value):
        if value is None:
            return None
        return list(value)

    def to_python(self, value):
        if value is None:
            return []
        return value

    def get_default(self):
        "Returns the default value for this field."
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default
        return []

class SortedListField(ListField):
    """A ListField that sorts the contents of its list before writing to
    the database in order to ensure that a sorted list is always
    retrieved.
    """

    description = _("Sorted Field")
    _ordering = None

    def __init__(self, *args, **kwargs):
        if 'ordering' in kwargs.keys():
            self._ordering = kwargs.pop('ordering')
        self._internaltype = type
        super(SortedListField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if value is None:
            return None
        if not isinstance(value, list) and (not hasattr(value, "__iter__")):
            raise exceptions.ValidationError(self.error_messages['invalid'])
        if self._ordering is not None:
            return sorted(value, key=itemgetter(self._ordering))
        return sorted(value)
    
class DictField(Field):
    """A dictionary field that wraps a standard Python dictionary.
    Key cannot contains . or $ for query problems.
    """
    description = _("Dict Field")

    default_error_messages = {
        'invalid': _(u'This value must be a dictionary.'),
        'invalid_key': _(u'Invalid dictionary key name - Keys cannot contains . or $ for query problems'),
    }

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. 
        """
        if not isinstance(value, dict):
            raise exceptions.ValidationError(self.error_messages['invalid'])


        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])

    def get_default(self):
        "Returns the default value for this field."
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default
        return {}

class SetListField(Field):
    """A list field that allows only one instance for item.
    """

    description = _("List Set Field")
    _internaltype = None
    default_error_messages = {
        'invalid': _(u'This value must be a set.'),
        'invalid_value': _(u'Invalid value in list.'),
    }

    def __init__(self, *args, **kwargs):
        kwargs['blank'] = True
        if 'default' not in kwargs:
            kwargs['default'] = set()
        if 'type' in kwargs:
            self._internaltype = kwargs.pop("type")

        Field.__init__(self, *args, **kwargs)
    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. 
        """
        if not isinstance(value, set):
            raise exceptions.ValidationError(self.error_messages['invalid'])

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])
        if self._internaltype is not None:
            for v in value:
                if not isinstance(v, self._internaltype):
                    raise exceptions.ValidationError(self.error_messages['invalid_value'])

    def get_default(self):
        "Returns the default value for this field."
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default
        return set()


    def get_db_prep_value(self, value, connection, prepared=False):
        """Returns field's value prepared for interacting with the database
        backend.

        Used by the default implementations of ``get_db_prep_save``and
        `get_db_prep_lookup```
        """
        if not prepared:
            value = list(self.get_prep_value(value))
        return value
    
    def get_prep_value(self, value):
        if value is None:
            return None
        if not isinstance(value, set):
            if hasattr(value, "__iter__"):
                value = set(value)
        return set(value)
    
    def to_python(self, value):
        """
        Converts the input value into the expected Python data type, raising
        django.core.exceptions.ValidationError if the data can't be converted.
        Returns the converted value.
        """
        if value is None:
            return set()
        return set(value)


    
class BlobField(models.Field):
    """
    A field for storing blobs of binary data
    """
    def get_internal_type(self):
        return 'BlobField'

    def formfield(self, **kwargs):
        # A file widget is provided, but use  model FileField or ImageField 
        # for storing specific files most of the time
        from .widgets import BlobWidget
        from django.forms import FileField
        defaults = {'form_class': FileField, 'widget': BlobWidget}
        defaults.update(kwargs)
        return super(BlobField, self).formfield(**defaults)

    def get_db_prep_value(self, value, connection, prepared=False):        
        try:
            # Sees if the object passed in is file-like
            return value.read()
        except:
            return str(value)

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        raise TypeError("BlobFields do not support lookups")

    def value_to_string(self, obj):
        return str(self._get_val_from_obj(obj))
