from wtforms.widgets import html_params, TextInput
from wtforms.compat import text_type
from wtforms import validators

from wtforms import DateField, TextField

class IconInputWidget(TextInput):
    def __call__(self, field, icon=None, text=None,  **kwargs):
        kwargs['type'] = u'text'
        html = u""
        html += u'<div class="input-group" >'
        html += u'<span class="input-group-addon">'
        if icon is not None:
            html += u'<span class="glyphicon glyphicon-%s"></span>' % icon
        elif text is not None:
            html += u'%s' % text
        html += u'</span>'
        html += super(IconInputWidget, self).__call__(field, **kwargs)
        html += u'</div>'
        return html

class IPWidget(IconInputWidget):
    """ Bootstrap IPv4 Widget """
    def __init__(self, version=4, **kwargs):
        self.version = version

    def __call__(self, field, **kwargs):
        attribute = 'data-bv-ip-ipv4'
        text = "IPv4"
        if self.version == 6:
            attribute = 'data-bv-ip-ipv6'
            text = "IPv6"
        kwargs[attribute] = u""
        return super(IPWidget, self).__call__(field, text=text, **kwargs)


class bDateWidget(IconInputWidget):
    """ Bootstrap Date Widget """
    def __init__(self, data_date_viewmode="days", date_view_format="yyyy-mm-dd", **kwargs):
        self.data_date_viewmode = data_date_viewmode
        self.date_view_format = date_view_format

    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-date-viewmode', self.data_date_viewmode)
        kwargs.setdefault('data-date-format', self.date_view_format)
        kwargs['data-date-autoclose'] = u'True'
        kwargs['data-provide'] = u'datepicker'
        kwargs['class'] = kwargs['class'] + u' span2 date-picker'
        return super(bDateWidget, self).__call__(field, icon="calendar", **kwargs)

class IPv4Field(TextField):
    """ Bootstrap IPv4 Field """
    def __init__(self, label, **kwargs):
        super(IPv4Field, self).__init__(label, **kwargs)
        self.validators.append(validators.IPAddress())
        self.widget = IPWidget(version=4)

    def _value(self):
        return text_type(self.data) if self.data is not None else ''

class IPv6Field(TextField):
    """ Bootstrap IPv6 Field """
    def __init__(self, label, **kwargs):
        super(IPv6Field, self).__init__(label, **kwargs)
        self.widget = IPWidget(version=6)

    def _value(self):
        return text_type(self.data) if self.data is not None else ''


class bDateField(DateField):
    """ Bootstrap Date Field """
    def __init__(self, label, date_viewmode=u"days", date_view_format="yyyy-mm-dd", **kwargs):
        super(bDateField, self).__init__(label, **kwargs)
        value = None
        self.widget = bDateWidget(data_date_viewmode=date_viewmode, date_view_format=date_view_format)

    def _value(self):
        return text_type(self.data) if self.data is not None else ''

