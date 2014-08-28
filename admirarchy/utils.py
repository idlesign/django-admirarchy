from django.conf import settings
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.options import ModelAdmin

from .exceptions import AdmirarchyConfigurationError


class HierarchicalModelAdmin(ModelAdmin):
    """Customized Model admin handling hierarchies navigation."""

    hierarchy = False
    change_list_template = 'admin/admirarchy/change_list.html'

    def get_changelist(self, request, **kwargs):
        """Returns an appropriate ChangeList for ModelAdmin.

        Initializes hierarchies handling.

        :param request:
        :param kwargs:
        :return:
        """
        Hierarchy.init_hierarchy(self)
        return HierarchicalChangeList

    def change_view(self, *args, **kwargs):
        """Renders detailed model edit page."""
        self.hierarchy.hook_change_view(self, args, kwargs)
        return super(HierarchicalModelAdmin, self).change_view(*args, **kwargs)

    def action_checkbox(self, obj):
        """Renders checkboxes.

        Disable checkbox for parent item navigation link.

        """
        if getattr(obj, Hierarchy.UPPER_LEVEL_LINK_MARKER, False):
            return ''
        return super(HierarchicalModelAdmin, self).action_checkbox(obj)

    def hierarchy_nav(self, obj):
        """Renders hierarchy navigation elements (folders)."""

        result_repr = ''  # For items without children.
        ch_count = getattr(obj, Hierarchy.CHILD_COUNT_MODEL_ATTR, 0)

        if ch_count:  # For items with children.
            icon = 'icon icon-folder'
            title = _('Objects inside: %s') % ch_count
            if getattr(obj, Hierarchy.UPPER_LEVEL_LINK_MARKER, False):
                icon = 'icon icon-folder-up'
                title = _('Upper level')
            url = './'
            if obj.pk:
                url = '?pid=%s' % obj.pk

            #url = add_preserved_filters({'preserved_filters': changelist.preserved_filters, 'opts': changelist.opts}, url)
            result_repr = format_html('<a href="{0}" class="{1}" title="{2}"></a>', url, icon, title)
        return result_repr
    hierarchy_nav.short_description = ''


class HierarchicalChangeList(ChangeList):
    """Customized ChangeList used by HierarchicalModelAdmin to handle hierarchies."""

    def __init__(self, *args):
        """Adds hierarchy navigation column if necessary.

        :param args:
        :return:
        """
        self.hierarchy = args[-1].hierarchy  # model_admin
        if not isinstance(self.hierarchy, NoHierarchy):
            args = list(args)
            args[2] = [self.hierarchy.NAV_FIELD_MARKER] + list(args[2])  # list_display
        super(HierarchicalChangeList, self).__init__(*args)

    def get_queryset(self, request):
        """Constructs a query set.

        :param request:
        :return:
        """
        self.hierarchy.hook_get_queryset(self, request)
        return super(HierarchicalChangeList, self).get_queryset(request)

    def get_results(self, request):
        """Gets query set results.

        :param request:
        :return:
        """
        super(HierarchicalChangeList, self).get_results(request)
        self.hierarchy.hook_get_results(self)

    def check_field_exists(self, field_name):
        """Implements field exists check for debugging purposes.

        :param field_name:
        :return:
        """
        if settings.DEBUG:
            try:
                self.lookup_opts.get_field_by_name(field_name)
            except FieldDoesNotExist as e:
                raise AdmirarchyConfigurationError(e)


########################################################


class Hierarchy(object):

    PARENT_ID_QS_PARAM = 'pid'  # Parent ID query string parameter.
    CHILD_COUNT_MODEL_ATTR = 'child_count'  # Attribute given to every model.
    UPPER_LEVEL_LINK_MARKER = 'dummy'
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
        self.pid_field = parent_id_field
        self.pid_field_real = '%s_id' % parent_id_field

    def hook_change_view(self, changelist, view_args, view_kwargs):
        """Triggered by `ModelAdmin.change_view()`.

        Replaces parent item dropdown list with a lookup dialog.

        """
        # TODO Implement in-popups functioning.
        changelist.raw_id_fields += (self.pid_field,)

    def hook_get_queryset(self, changelist, request):
        """Triggered by `ChangeList.get_queryset()`."""
        changelist.check_field_exists(self.pid_field)
        pid = self.get_pid_from_request(changelist, request)
        changelist.params[self.pid_field] = pid
        return pid

    def hook_get_results(self, changelist):
        """Triggered by `ChangeList.get_results()`."""
        get_parent = lambda m: getattr(m, self.pid_field_real, None)
        result_list = list(changelist.result_list)
        parent_id = get_parent(result_list[0])
        if parent_id:
            parent = changelist.model.objects.get(pk=parent_id)
            parent = changelist.model(pk=get_parent(parent))
            setattr(parent, self.CHILD_COUNT_MODEL_ATTR, 1)
            setattr(parent, self.UPPER_LEVEL_LINK_MARKER, True)
            result_list = [parent] + result_list
        kwargs_filter = {'%s__in' % self.pid_field: result_list}
        stats_qs = changelist.model.objects.filter(**kwargs_filter).values_list(self.pid_field).annotate(cnt=models.Count(self.pid_field))
        stats = {item[0]: item[1] for item in stats_qs}
        for item in result_list:
            if not hasattr(item, self.CHILD_COUNT_MODEL_ATTR):
                try:
                    setattr(item, self.CHILD_COUNT_MODEL_ATTR, stats[item.id])
                except KeyError:
                    setattr(item, self.CHILD_COUNT_MODEL_ATTR, 0)
        changelist.result_list = result_list
