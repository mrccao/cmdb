from wtforms.widgets import html_params, TextInput
from wtforms.compat import text_type

from wtforms import DateField

class IconInputWidget(TextInput):
    def __call__(self, field, icon, **kwargs):
        kwargs['type'] = u'text'
        html = u""
        html += u'<div class="input-group" >'
        html += u'<span class="input-group-addon">'
        html += u'<span class="glyphicon glyphicon-%s"></span>' % icon
        html += u'</span>'
        html += super(IconInputWidget, self).__call__(field, **kwargs)
        html += u'</div>'
        return html


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
        return super(bDateWidget, self).__call__(field, "calendar", **kwargs)


class bDateField(DateField):
    """ Bootstrap Date Field """
    def __init__(self, label, date_viewmode=u"days", date_view_format="yyyy-mm-dd", **kwargs):
        super(bDateField, self).__init__(label, **kwargs)
        value = None
        self.widget = bDateWidget(data_date_viewmode=date_viewmode, date_view_format=date_view_format)

    def _value(self):
        return text_type(self.data) if self.data is not None else ''

