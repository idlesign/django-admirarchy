# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django import VERSION

from .testapp.models import AdjacencyListModel, NestedSetModel


VERSION_PRE_19 = VERSION < (1, 9)


def actual_test(model_id, user_create, request_client):

    user = user_create(superuser=True)

    client = request_client()
    assert client.login(username=user.username, password='password')

    url_base = '/admin/testapp/%s/' % model_id

    resp = client.get(url_base)

    assert 'Объектов внутри' in resp.rendered_content

    if VERSION_PRE_19:
        assert '/1/' in resp.rendered_content
    else:
        assert '/1/change/' in resp.rendered_content

    assert 'href="?pid=1"' in resp.rendered_content
    assert model_id + '_parent' in resp.rendered_content
    assert model_id + '_child1' not in resp.rendered_content
    assert model_id + '_child2' not in resp.rendered_content

    resp = client.get(url_base + '?pid=1')

    assert 'Верхний уровень' in resp.rendered_content

    if VERSION_PRE_19:
        assert '/1/' not in resp.rendered_content
        assert '/2/?_changelist_filters=pid%3D1' in resp.rendered_content
        assert '/3/?_changelist_filters=pid%3D1' in resp.rendered_content


    else:
        assert '/1/change/' not in resp.rendered_content
        assert '/2/change/?_changelist_filters=pid%3D1' in resp.rendered_content
        assert '/3/change/?_changelist_filters=pid%3D1' in resp.rendered_content

    assert model_id + '_parent' not in resp.rendered_content
    assert model_id + '_child1' in resp.rendered_content
    assert model_id + '_child2' in resp.rendered_content

    # Foreign key popup.
    resp = client.get(url_base + '?_to_field=id&_popup=1')

    print(resp.rendered_content)

    assert '?pid=1&amp;' in resp.rendered_content
    assert '_popup=1' in resp.rendered_content
    assert model_id + '_parent' in resp.rendered_content


def test_adjacency_list(request_client, user_create):

    def make_node(title, parent=None):
        node = AdjacencyListModel(title=title, parent=parent)
        node.save()
        return node

    parent = make_node('parent')
    make_node('child1', parent=parent)
    make_node('child2', parent=parent)

    actual_test('adjacencylistmodel', user_create, request_client)



def test_nested_set(request_client, user_create):

    def make_node(title, left, right, level):
        node = NestedSetModel(title=title, lft=left, rgt=right, level=level)
        node.save()
        return node

    make_node('parent', left=1, right=6, level=0)
    make_node('child1', left=2, right=3, level=1)
    make_node('child2', left=4, right=5, level=1)

    actual_test('nestedsetmodel', user_create, request_client)
