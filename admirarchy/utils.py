from __future__ import unicode_literals

from copy import copy

from django.conf import settings
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .exceptions import AdmirarchyConfigurationError


class HierarchicalModelAdmin(ModelAdmin):
    """Customized Model admin handling hierarchies navigation."""

    hierarchy = False  # type: Hierarchy
    change_list_template = 'admin/admirarchy/change_list.html'
    _current_changelist = None

    def get_changelist(self, request, **kwargs):
        """Returns an appropriate ChangeList for ModelAdmin.

        Initializes hierarchies handling.

        :param request:
        :param kwargs:
        :rtype: HierarchicalChangeList
        """
        Hierarchy.init_hierarchy(self)

        return HierarchicalChangeList

    def change_view(self, *args, **kwargs):
        """Renders detailed model edit page."""
        Hierarchy.init_hierarchy(self)

        self.hierarchy.hook_change_view(self, args, kwargs)

        return super(HierarchicalModelAdmin, self).change_view(*args, **kwargs)

    def action_checkbox(self, obj):
        """Renders checkboxes.

        Disable checkbox for parent item navigation link.

        """
        if getattr(obj, Hierarchy.UPPER_LEVEL_MODEL_ATTR, False):
            return ''

        return super(HierarchicalModelAdmin, self).action_checkbox(obj)

    def hierarchy_nav(self, obj):
        """Renders hierarchy navigation elements (folders)."""

        result_repr = ''  # For items without children.
        ch_count = getattr(obj, Hierarchy.CHILD_COUNT_MODEL_ATTR, 0)

        is_parent_link = getattr(obj, Hierarchy.UPPER_LEVEL_MODEL_ATTR, False)

        if is_parent_link or ch_count:  # For items with children and parent links.
            icon = 'icon icon-folder'
            title = _('Objects inside: %s') % ch_count

            if is_parent_link:
                icon = 'icon icon-folder-up'
                title = _('Upper level')

            url = './'

            if obj.pk:
                url = '?%s=%s' % (Hierarchy.PARENT_ID_QS_PARAM, obj.pk)

            if self._current_changelist.is_popup:

                qs_get = copy(self._current_changelist._request.GET)

                try:
                    del qs_get[Hierarchy.PARENT_ID_QS_PARAM]

                except KeyError:
                    pass

                qs_get = qs_get.urlencode()
                url = ('%s&%s' if '?' in url else '%s?%s') % (url, qs_get)

            result_repr = format_html('<a href="{0}" class="{1}" title="{2}"></a>', url, icon, force_text(title))

        return result_repr

    hierarchy_nav.short_description = ''


class HierarchicalChangeList(ChangeList):
    """Customized ChangeList used by HierarchicalModelAdmin to handle hierarchies."""

    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, date_hierarchy, search_fields,
                 list_select_related, list_per_page, list_max_show_all,
                 list_editable, model_admin, *args):
        """Adds hierarchy navigation column if necessary.

        :param args:
        :return:
        """
        model_admin._current_changelist = self
        self._hierarchy = model_admin.hierarchy
        self._request = request
        if not isinstance(self._hierarchy, NoHierarchy):
            list_display = [self._hierarchy.NAV_FIELD_MARKER] + list(list_display)

        super(HierarchicalChangeList, self).__init__(
            request, model, list_display, list_display_links,
            list_filter, date_hierarchy, search_fields,
            list_select_related, list_per_page, list_max_show_all,
            list_editable, model_admin, *args)

    def get_queryset(self, request):
        """Constructs a query set.

        :param request:
        :return:
        """
        self._hierarchy.hook_get_queryset(self, request)

        return super(HierarchicalChangeList, self).get_queryset(request)

    def get_results(self, request):
        """Gets query set results.

        :param request:
        :return:
        """
        super(HierarchicalChangeList, self).get_results(request)

        self._hierarchy.hook_get_results(self)

    def check_field_exists(self, field_name):
        """Implements field exists check for debugging purposes.

        :param field_name:
        :return:
        """
        if not settings.DEBUG:
            return

        try:
            self.lookup_opts.get_field(field_name)

        except FieldDoesNotExist as e:
            raise AdmirarchyConfigurationError(e)


########################################################


class Hierarchy(object):
    """Base hierarchy class. Hierarchy classes must inherit from it."""

    PARENT_ID_QS_PARAM = 'pid'  # Parent ID query string parameter.
    CHILD_COUNT_MODEL_ATTR = 'child_count'  # Attribute given to every model.
    UPPER_LEVEL_MODEL_ATTR = 'dummy'  # This attribute indicated the model is just a dummy upper level link.
    NAV_FIELD_MARKER = 'hierarchy_nav'

    @classmethod
    def init_hierarchy(cls, model_admin):
        """Initializes model admin with hierarchy data."""
        hierarchy = getattr(model_admin, 'hierarchy')

        if hierarchy:
            if not isinstance(hierarchy, Hierarchy):
                hierarchy = AdjacencyList()  # For `True` and etc. TODO heuristics maybe.

        else:
            hierarchy = NoHierarchy()

        model_admin.hierarchy = hierarchy

    @classmethod
    def get_pid_from_request(cls, changelist, request):
        """Gets parent ID from query string.

        :param changelist:
        :param request:
        :return:
        """
        val = request.GET.get(cls.PARENT_ID_QS_PARAM, False)
        pid = val or None

        try:
            del changelist.params[cls.PARENT_ID_QS_PARAM]

        except KeyError:
            pass

        return pid

    def hook_change_view(self, changelist, view_args, view_kwargs):
        """Triggered by `ModelAdmin.change_view()`."""

    def hook_get_results(self, changelist):
        """Triggered by `ChangeList.get_results()`."""

    def hook_get_queryset(self, changelist, request):
        """Triggered by `ChangeList.get_queryset()`."""


class NoHierarchy(Hierarchy):
    """Dummy (disabled) hierarchy class."""


class AdjacencyList(Hierarchy):

    def __init__(self, parent_id_field='parent'):
        self.pid = None
        self.pid_field = parent_id_field
        self.pid_field_real = '%s_id' % parent_id_field

    def hook_change_view(self, changelist, view_args, view_kwargs):
        """Triggered by `ModelAdmin.change_view()`.

        Replaces parent item dropdown list with a lookup dialog.

        """
        # TODO start from an appropriate tree level when in parent lookup popup
        changelist.raw_id_fields += (self.pid_field,)

    def hook_get_queryset(self, changelist, request):
        """Triggered by `ChangeList.get_queryset()`."""
        changelist.check_field_exists(self.pid_field)
        self.pid = self.get_pid_from_request(changelist, request)
        changelist.params[self.pid_field] = self.pid

    def hook_get_results(self, changelist):
        """Triggered by `ChangeList.get_results()`."""
        result_list = list(changelist.result_list)

        if self.pid:
            # Render to upper level link.
            parent = changelist.model.objects.get(pk=self.pid)
            parent = changelist.model(pk=getattr(parent, self.pid_field_real, None))
            setattr(parent, self.UPPER_LEVEL_MODEL_ATTR, True)
            result_list = [parent] + result_list

        # Get children stats.
        kwargs_filter = {'%s__in' % self.pid_field: result_list}

        stats_qs = changelist.model.objects.filter(
            **kwargs_filter).values_list(self.pid_field).annotate(cnt=models.Count(self.pid_field))

        stats = {item[0]: item[1] for item in stats_qs}

        for item in result_list:

            if hasattr(item, self.CHILD_COUNT_MODEL_ATTR):
                continue

            try:
                setattr(item, self.CHILD_COUNT_MODEL_ATTR, stats[item.id])

            except KeyError:
                setattr(item, self.CHILD_COUNT_MODEL_ATTR, 0)

        changelist.result_list = result_list


class NestedSet(Hierarchy):

    def __init__(self, left_field='lft', right_field='rgt', level_field='level', root_level=0):
        self.pid = None
        self.parent = None
        self.left_field = left_field
        self.right_field = right_field
        self.level_field = level_field
        self.root_level = root_level

    def get_range_clause(self, obj):
        return getattr(obj, self.left_field), getattr(obj, self.right_field)

    def get_immediate_children_filter(self, obj):
        flt = {
            '%s__range' % self.left_field: self.get_range_clause(obj),
            self.level_field: getattr(obj, self.level_field) + 1
        }
        return flt

    def hook_get_queryset(self, changelist, request):
        """Triggered by `ChangeList.get_queryset()`."""
        changelist.check_field_exists(self.left_field)
        changelist.check_field_exists(self.right_field)
        self.pid = self.get_pid_from_request(changelist, request)

        # Get parent item first.
        qs = changelist.root_queryset

        if self.pid:
            self.parent = qs.get(pk=self.pid)
            changelist.params.update(self.get_immediate_children_filter(self.parent))

        else:
            changelist.params[self.level_field] = self.root_level
            self.parent = qs.get(**{key: val for key, val in changelist.params.items() if not key.startswith('_')})

    def hook_get_results(self, changelist):
        """Triggered by `ChangeList.get_results()`."""

        # Poor NestedSet guys they've punished themselves once chosen that approach,
        # and now we punish them again with all those DB hits.

        result_list = list(changelist.result_list)

        # Get children stats.
        filter_kwargs = {'%s' % self.left_field: models.F('%s' % self.right_field) - 1}  # Leaf nodes only.
        filter_kwargs.update(self.get_immediate_children_filter(self.parent))

        stats_qs = changelist.result_list.filter(**filter_kwargs).values_list('id')
        leafs = [item[0] for item in stats_qs]

        for result in result_list:

            if result.id in leafs:
                setattr(result, self.CHILD_COUNT_MODEL_ATTR, 0)
            else:
                setattr(result, self.CHILD_COUNT_MODEL_ATTR, '>1')  # Too much pain to get real stats, so that'll suffice.

        if self.pid:
            # Render to upper level link.
            parent = self.parent

            filter_kwargs = {
                '%s__lt' % self.left_field: getattr(parent, self.left_field),
                '%s__gt' % self.right_field: getattr(parent, self.right_field),
            }

            try:
                granparent_id = changelist.model.objects.filter(**filter_kwargs).order_by('-%s' % self.left_field)[0].id
            except IndexError:
                granparent_id = None

            if granparent_id != parent.id:
                parent = changelist.model(pk=granparent_id)

            setattr(parent, self.UPPER_LEVEL_MODEL_ATTR, True)
            result_list = [parent] + result_list

        changelist.result_list = result_list
