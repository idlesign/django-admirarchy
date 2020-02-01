from copy import copy
from typing import Type, Optional, Dict, Tuple

from django.conf import settings
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.db.models import Model, QuerySet
from django.db.models.fields import FieldDoesNotExist
from django.http import HttpRequest
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .exceptions import AdmirarchyConfigurationError


class HierarchicalModelAdmin(ModelAdmin):
    """Customized Model admin handling hierarchies navigation."""

    hierarchy = False  # type: Hierarchy
    change_list_template = 'admin/admirarchy/change_list.html'

    _current_changelist = None

    def get_changelist(self, request: HttpRequest, **kwargs) -> Type['HierarchicalChangeList']:
        """Returns an appropriate ChangeList for ModelAdmin.

        Initializes hierarchies handling.

        :param request:
        :param kwargs:

        """
        Hierarchy.init_hierarchy(self)

        return HierarchicalChangeList

    def change_view(self, *args, **kwargs):
        """Renders detailed model edit page."""
        Hierarchy.init_hierarchy(self)

        self.hierarchy.hook_change_view(self, args, kwargs)

        return super(HierarchicalModelAdmin, self).change_view(*args, **kwargs)

    def action_checkbox(self, obj: Model):
        """Renders checkboxes.

        Disable checkbox for parent item navigation link.

        """
        if getattr(obj, Hierarchy.UPPER_LEVEL_MODEL_ATTR, False):
            return ''

        return super(HierarchicalModelAdmin, self).action_checkbox(obj)

    def hierarchy_nav(self, obj: Model) -> str:
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

            changelist = self._current_changelist

            if changelist.is_popup:

                qs_get = copy(changelist._request.GET)

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

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Constructs a query set.

        :param request:

        """
        hierarchy = self._hierarchy
        hierarchy.hook_get_queryset(self, request)

        qs = super(HierarchicalChangeList, self).get_queryset(request)
        qs = hierarchy.hook_filter_queryset(self, qs)

        return qs

    def get_results(self, request: HttpRequest):
        """Gets query set results.

        :param request:

        """
        super(HierarchicalChangeList, self).get_results(request)

        self._hierarchy.hook_get_results(self)

    def check_field_exists(self, field_name: str):
        """Implements field exists check for debugging purposes.

        :param field_name:

        """
        if not settings.DEBUG:
            return

        try:
            self.lookup_opts.get_field(field_name)

        except FieldDoesNotExist as e:
            raise AdmirarchyConfigurationError(e)


########################################################


class Hierarchy:
    """Base hierarchy class. Hierarchy classes must inherit from it."""

    PARENT_ID_QS_PARAM = 'pid'  # Parent ID query string parameter.
    CHILD_COUNT_MODEL_ATTR = 'child_count'  # Attribute given to every model.
    UPPER_LEVEL_MODEL_ATTR = 'dummy'  # This attribute indicated the model is just a dummy upper level link.
    NAV_FIELD_MARKER = 'hierarchy_nav'

    @classmethod
    def init_hierarchy(cls, model_admin: HierarchicalModelAdmin):
        """Initializes model admin with hierarchy data."""

        hierarchy = getattr(model_admin, 'hierarchy')

        if hierarchy:
            if not isinstance(hierarchy, Hierarchy):
                hierarchy = AdjacencyList()  # For `True` and etc. TODO heuristics maybe.

        else:
            hierarchy = NoHierarchy()

        model_admin.hierarchy = hierarchy

    @classmethod
    def get_pid_from_request(cls, changelist: 'HierarchicalChangeList', request: HttpRequest) -> Optional[str]:
        """Gets parent ID from query string.

        :param changelist:
        :param request:

        """
        qs_param = cls.PARENT_ID_QS_PARAM

        val = request.GET.get(qs_param, False)
        pid = val or None

        changelist.params.pop(qs_param, None)

        return pid

    def hook_change_view(self, model_admin: HierarchicalModelAdmin, view_args: Tuple, view_kwargs: Dict):
        """Triggered by `ModelAdmin.change_view()`."""

    def hook_get_results(self, changelist: 'HierarchicalChangeList'):
        """Triggered by `ChangeList.get_results()`."""

    def hook_get_queryset(self, changelist: 'HierarchicalChangeList', request: HttpRequest):
        """Triggered by `ChangeList.get_queryset()`."""

    def hook_filter_queryset(self, changelist: 'HierarchicalChangeList', query_set: QuerySet) -> QuerySet:
        """Triggered by `ChangeList.get_queryset()`."""
        return query_set


class NoHierarchy(Hierarchy):
    """Dummy (disabled) hierarchy class."""


class AdjacencyList(Hierarchy):

    def __init__(self, parent_id_field: str = 'parent'):

        self.pid = None
        self.pid_field = parent_id_field
        self.pid_field_real = '%s_id' % parent_id_field

    def hook_change_view(self, model_admin: HierarchicalModelAdmin, view_args: Tuple, view_kwargs: Dict):
        """Triggered by `ModelAdmin.change_view()`.

        Replaces parent item dropdown list with a lookup dialog.

        """
        # TODO start from an appropriate tree level when in parent lookup popup
        model_admin.raw_id_fields += (self.pid_field,)

    def hook_get_queryset(self, changelist: 'HierarchicalChangeList', request: HttpRequest):
        """Triggered by `ChangeList.get_queryset()`."""
        pid_field = self.pid_field

        changelist.check_field_exists(pid_field)

        pid = self.get_pid_from_request(changelist, request)
        self.pid = pid

        if changelist.query:
            # Do not restrict search to current sub.
            return

        changelist.params[pid_field] = pid

    def hook_filter_queryset(self, changelist: 'HierarchicalChangeList', query_set: QuerySet) -> QuerySet:
        """Triggered by `ChangeList.get_queryset()`."""

        if self.pid is None:
            changelist.params.pop(self.pid_field, None)

        return query_set

    def hook_get_results(self, changelist: 'HierarchicalChangeList'):
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

    def __init__(
            self,
            left_field: str = 'lft',
            right_field: str = 'rgt',
            level_field: str = 'level',
            root_level: int = 0
    ):
        self.pid = None
        self.parent = None
        self.left_field = left_field
        self.right_field = right_field
        self.level_field = level_field
        self.root_level = root_level

    def get_range_clause(self, obj: Model) -> Tuple[int, int]:
        return getattr(obj, self.left_field), getattr(obj, self.right_field)

    def get_immediate_children_filter(self, obj: Model) -> Dict:
        flt = {
            '%s__range' % self.left_field: self.get_range_clause(obj),
            self.level_field: getattr(obj, self.level_field) + 1
        }
        return flt

    def hook_get_queryset(self, changelist: 'HierarchicalChangeList', request: HttpRequest):
        """Triggered by `ChangeList.get_queryset()`."""

        changelist.check_field_exists(self.left_field)
        changelist.check_field_exists(self.right_field)

        pid = self.get_pid_from_request(changelist, request)
        self.pid = pid

        # Get parent item first.
        qs = changelist.root_queryset

        if changelist.query:
            # Do not restrict search to current sub.
            return

        if pid:
            self.parent = qs.get(pk=pid)
            changelist.params.update(self.get_immediate_children_filter(self.parent))

        else:
            changelist.params[self.level_field] = self.root_level
            self.parent = qs.get(**{
                key: val for key, val in changelist.params.items()
                if not key.startswith('_') and key != 'q'
            })

    def hook_get_results(self, changelist: 'HierarchicalChangeList'):
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
                # Too much pain to get real stats, so that'll suffice.
                setattr(result, self.CHILD_COUNT_MODEL_ATTR, '>1')

        if self.pid:
            # Render to upper level link.
            parent = self.parent

            filter_kwargs = {
                '%s__lt' % self.left_field: getattr(parent, self.left_field),
                '%s__gt' % self.right_field: getattr(parent, self.right_field),
            }

            try:
                grandparent_id = changelist.model.objects.filter(
                    **filter_kwargs
                ).order_by('-%s' % self.left_field)[0].id

            except IndexError:
                grandparent_id = None

            if grandparent_id != parent.id:
                parent = changelist.model(pk=grandparent_id)

            setattr(parent, self.UPPER_LEVEL_MODEL_ATTR, True)
            result_list = [parent] + result_list

        changelist.result_list = result_list
