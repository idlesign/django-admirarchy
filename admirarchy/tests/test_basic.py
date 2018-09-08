from django import VERSION

from .testapp.models import AdjacencyListModel


VERSION_PRE_19 = VERSION < (1, 9)


def test_adjacency_list(settings, request_client, user_create):

    def make_node(title, parent=None):
        node = AdjacencyListModel(title=title, parent=parent)
        node.save()
        return node

    parent = make_node('parent')
    make_node('child1', parent=parent)
    make_node('child2', parent=parent)

    user = user_create(superuser=True)

    client = request_client()
    assert client.login(username=user.username, password='password')

    url_base = '/admin/testapp/adjacencylistmodel/'

    resp = client.get(url_base)

    assert 'Upper level' not in resp.rendered_content

    if VERSION_PRE_19:
        assert '/1/' in resp.rendered_content
    else:
        assert '/1/change/' in resp.rendered_content

    assert 'href="?pid=1"' in resp.rendered_content
    assert 'adjlist_parent' in resp.rendered_content
    assert 'adjlist_child1' not in resp.rendered_content
    assert 'adjlist_child2' not in resp.rendered_content

    resp = client.get(url_base + '?pid=1')

    assert 'Upper level' in resp.rendered_content

    if VERSION_PRE_19:
        assert '/1/' not in resp.rendered_content
        assert '/2/?_changelist_filters=pid%3D1' in resp.rendered_content
        assert '/3/?_changelist_filters=pid%3D1' in resp.rendered_content


    else:
        assert '/1/change/' not in resp.rendered_content
        assert '/2/change/?_changelist_filters=pid%3D1' in resp.rendered_content
        assert '/3/change/?_changelist_filters=pid%3D1' in resp.rendered_content

    assert 'adjlist_parent' not in resp.rendered_content
    assert 'adjlist_child1' in resp.rendered_content
    assert 'adjlist_child2' in resp.rendered_content
