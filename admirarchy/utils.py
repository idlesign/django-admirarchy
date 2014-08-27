from django.db import models
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.options import ModelAdmin


class HierarchicalChangeList(ChangeList):

    def __init__(self, *args, **kwargs):
        self.hierarchy = args[-1].hierarchy  # model_admin
        if not isinstance(self.hierarchy, NoHierarchy):
            # Add hierarchy navigation column.
            args = list(args)
            args[2] = [self.hierarchy.NAV_FIELD_MARKER] + list(args[2])  # list_display
        super(HierarchicalChangeList, self).__init__(*args)

    def get_queryset(self, request):
        self.hierarchy.update_changelist(self, request=request)
        return super(HierarchicalChangeList, self).get_queryset(request)

    def get_results(self, request):
        super(HierarchicalChangeList, self).get_results(request)
        if self.hierarchy:
            self.result_list = self.hierarchy.get_updated_changelist_results(self.result_list, model=self.model)


class HierarchicalModelAdmin(ModelAdmin):

    hierarchy = False
    change_list_template = 'admin/admirarchy/change_list.html'

    def get_changelist(self, request, **kwargs):
        Hierarchy.init_hierarchy(self)
        return HierarchicalChangeList

    def change_view(self, *args, **kwargs):
        if self.hierarchy:
            self.raw_id_fields += ('parent',)
        return super(HierarchicalModelAdmin, self).change_view(*args, **kwargs)

    def action_checkbox(self, obj):
        if getattr(obj, Hierarchy.UP_MARKER, False):
            return ''
        return super(HierarchicalModelAdmin, self).action_checkbox(obj)

    def hierarchy_nav(self, obj):
        result_repr = ''  # No children.
        ch_count = getattr(obj, Hierarchy.CHILD_COUNT_ATTR, 0)
        if ch_count:  # Has children
            icon = 'icon icon-folder'
            title = _('Objects inside: %s') % ch_count
            if getattr(obj, Hierarchy.UP_MARKER, False):
                icon = 'icon icon-folder-up'
                title = _('Upper level')
            url = './'
            if obj.pk:
                url = '?pid=%s' % obj.pk
            #url = add_preserved_filters({'preserved_filters': changelist.preserved_filters, 'opts': changelist.opts}, url)
            result_repr = format_html('<a href="{0}" class="{1}" title="{2}"></a>', url, icon, title)
        return result_repr
    hierarchy_nav.short_description = ''


########################################################


class Hierarchy(object):

    HIERARCHY_PARENT_ID = 'pid'
    CHILD_COUNT_ATTR = 'child_count'
    NAV_FIELD_MARKER = 'hierarchy_nav'
    UP_MARKER = 'dummy'

    @classmethod
    def init_hierarchy(cls, model_admin):
        hierarchy = getattr(model_admin, 'hierarchy')
        if hierarchy:
            if not isinstance(hierarchy, Hierarchy):
                hierarchy = AdjacentList()
        else:
            hierarchy = NoHierarchy()
        model_admin.hierarchy = hierarchy

    def get_updated_changelist_results(self, result_list, model):
        return result_list

    def update_changelist(self, changelist, request):
        changelist.hierarchy = self
        param_value = None
        if not isinstance(self, NoHierarchy):
            val = request.GET.get(self.HIERARCHY_PARENT_ID, False)
            param_value = val or None
            try:
                del changelist.params[self.HIERARCHY_PARENT_ID]
            except KeyError:
                pass
        return param_value


class NoHierarchy(Hierarchy):
    """"""


class AdjacentList(Hierarchy):

    def __init__(self, parent_id_field='parent'):
        self.pid_field = parent_id_field
        self.pid_field_real = '%s_id' % parent_id_field

    def update_changelist(self, changelist, request):
        param_value = super(AdjacentList, self).update_changelist(changelist, request)
        changelist.params[self.pid_field] = param_value
        return param_value

    def get_updated_changelist_results(self, result_list, model):
        get_parent = lambda m: getattr(m, self.pid_field_real, None)
        result_list = list(result_list)
        parent_id = get_parent(result_list[0])
        if parent_id:
            parent = model.objects.get(pk=parent_id)
            parent = model(pk=get_parent(parent))
            setattr(parent, self.CHILD_COUNT_ATTR, 1)
            setattr(parent, self.UP_MARKER, True)
            result_list = [parent] + result_list
        kwargs_filter = {'%s__in' % self.pid_field: result_list}
        stats_qs = model.objects.filter(**kwargs_filter).values_list(self.pid_field).annotate(cnt=models.Count(self.pid_field))
        stats = {item[0]: item[1] for item in stats_qs}
        for item in result_list:
            if not hasattr(item, self.CHILD_COUNT_ATTR):
                try:
                    setattr(item, self.CHILD_COUNT_ATTR, stats[item.id])
                except KeyError:
                    setattr(item, self.CHILD_COUNT_ATTR, 0)
        return result_list
