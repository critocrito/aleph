import json
import datetime

from aleph.core import db
from aleph.index.entities import index_entity
from aleph.views.util import validate
from aleph.tests.util import TestCase


class EntitiesApiTestCase(TestCase):

    def setUp(self):
        super(EntitiesApiTestCase, self).setUp()
        self.rolex = self.create_user(foreign_id='user_3')
        self.col = self.create_collection()
        book = {
            'schema': 'PlainText',
            'properties': {
                'name': 'The Book',
                'fileName': 'book.txt',
            }
        }
        self.book = self.create_entity(book, self.col)
        self.book_id = self.col.ns.sign(self.book.id)
        self.data = {
            'schema': 'LegalEntity',
            'properties': {
                'name': 'Winnie the Pooh',
                'country': 'pa',
                'proof': self.book_id,
                'incorporationDate': datetime.datetime(1926, 12, 24).isoformat()  # noqa
            }
        }
        self.ent = self.create_entity(self.data, self.col)
        self.id = self.col.ns.sign(self.ent.id)
        self.data2 = {
            'schema': 'LegalEntity',
            'properties': {
                'name': 'Tom & Jerry',
                'country': 'pa',
                'proof': self.book_id,
                'incorporationDate': datetime.datetime(1940, 2, 10).isoformat()  # noqa
            }
        }
        self.ent2 = self.create_entity(self.data2, self.col)
        self.id2 = self.col.ns.sign(self.ent.id)
        db.session.commit()
        self.col_id = str(self.col.id)
        index_entity(self.book)
        index_entity(self.ent)
        index_entity(self.ent2)

    def test_index(self):
        url = '/api/2/entities?filter:schemata=Thing'
        res = self.client.get(url+'&facet=collection_id')
        assert res.status_code == 200, res
        assert res.json['total'] == 0, res.json
        assert len(res.json['facets']['collection_id']['values']) == 0, \
            res.json
        _, headers = self.login(is_admin=True)
        res = self.client.get(url+'&facet=collection_id', headers=headers)
        assert res.status_code == 200, res
        assert res.json['total'] == 3, res.json
        assert len(res.json['facets']['collection_id']['values']) == 1, \
            res.json
        col0 = res.json['facets']['collection_id']['values'][0]
        assert col0['id'] == self.col_id, res.json
        assert col0['label'] == self.col.label, res.json
        assert len(res.json['facets']) == 1, res.json
        res = self.client.get(url+'&facet=countries', headers=headers)
        assert len(res.json['facets']) == 1, res.json
        assert 'values' in res.json['facets']['countries'], res.json
        validate(res.json['results'][0], 'Entity')

    def test_export(self):
        self.load_fixtures()
        url = '/api/2/search/export?filter:schemata=Thing&q=pakistan'
        res = self.client.get(url)
        assert res.status_code == 403, res

        _, headers = self.login(is_admin=True)
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res
        assert 'application/zip' in res.headers.get('Content-Type')

    def test_view(self):
        url = '/api/2/entities/%s' % self.id
        res = self.client.get(url)
        assert res.status_code == 403, res
        _, headers = self.login(is_admin=True)
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res
        assert 'LegalEntity' in res.json['schema'], res.json
        assert 'Winnie' in res.json['name'], res.json
        validate(res.json, 'Entity')

    def test_update(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities/%s' % self.id
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res

        data = res.json
        data['properties']['name'] = ['Winne the little Shit']
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, res.json
        validate(res.json, 'Entity')
        assert 'little' in res.json['name'], res.json

        data['properties'].pop('name', None)
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 400, res.json

    def test_create(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'RealEstate',
            'collection_id': self.col_id,
            'properties': {
                'name': "Our house",
                'summary': "In the middle of our street"
            }
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, res.json
        assert 'middle' in res.json['properties']['summary'][0], res.json
        validate(res.json, 'Entity')

    def test_create_collection_object(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'RealEstate',
            'collection': {
                'id': self.col_id,
                'label': 'blaaa'
            },
            'properties': {
                'name': "Our house",
                'summary': "In the middle of our street"
            }
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, res.json
        assert res.json['collection']['id'] == self.col_id, res.json
        validate(res.json, 'Entity')

    def test_create_nested(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'Person',
            'collection_id': self.col_id,
            'properties': {
                'name': "Osama bin Laden",
                'alias': ["Usama bin Laden", "Osama bin Ladin"],
                'address': 'Home, Netherlands'
            }
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, res.json
        assert 2 == len(res.json['properties'].get('alias', [])), res.json

    def test_remove_nested(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'Person',
            'collection_id': self.col_id,
            'properties': {
                'name': "Osama bin Laden",
                'alias': ["Usama bin Laden", "Osama bin Ladin"]
            }
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, (res.status_code, res.json)
        data = res.json
        data['properties']['alias'].pop()
        assert 1 == len(data['properties']['alias']), data
        url = '/api/2/entities/%s' % data['id']
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, (res.status_code, res.json)
        assert 1 == len(res.json['properties'].get('alias', [])), res.json

    def test_delete_entity(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'Person',
            'properties': {
                'name': "Osama bin Laden",
            },
            'collection_id': self.col_id
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, (res.status_code, res.json)
        data = res.json
        url = '/api/2/entities/%s' % data['id']
        res = self.client.delete(url, headers=headers)
        assert res.status_code == 204, res.status_code
        res = self.client.get(url, headers=headers)
        assert res.status_code == 404, res.status_code

    def test_similar_entity(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'Person',
            'collection_id': self.col_id,
            'properties': {
                'name': "Osama bin Laden",
            }
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        data = {
            'schema': 'Person',
            'collection_id': self.col_id,
            'properties': {
                'name': "Osama bin Laden",
            }
        }
        obj = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        url = '/api/2/entities/%s/similar' % obj.json['id']
        similar = self.client.get(url, headers=headers)
        assert similar.status_code == 200, (similar.status_code, similar.json)
        text = similar.data.decode('utf-8')
        assert obj.json['id'] not in text, obj.id
        assert obj.json['id'] not in text, obj.id
        data = similar.json
        assert len(data['results']) == 1, data
        assert 'Laden' in data['results'][0]['name'], data
        assert b'Pooh' not in res.data, res.data
        validate(data['results'][0], 'Entity')

    def test_match(self):
        _, headers = self.login(is_admin=True)
        data = {
            'schema': 'Person',
            'collection_id': self.col_id,
            'properties': {
                'name': "Osama bin Laden",
            }
        }
        res = self.client.post('/api/2/entities',
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        data = {
            'schema': 'Person',
            'properties': {
                'name': "Osama bin Laden",
            }
        }
        matches = self.client.post('/api/2/match',
                                   data=json.dumps(data),
                                   headers=headers,
                                   content_type='application/json')
        assert matches.status_code == 200, (matches.status_code, matches.json)
        data = matches.json
        assert len(data['results']) == 1, data
        assert 'Laden' in data['results'][0]['name'], data
        assert b'Pooh' not in res.data, res.data
        validate(data['results'][0], 'Entity')

    def test_entity_references(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities/%s/references' % self.book_id
        res = self.client.get(url)
        assert res.status_code == 403, res.status_code
        res = self.client.get(url, headers=headers)
        results = res.json['results']
        assert len(results) == 1, results
        assert results[0]['count'] == 2, results
        validate(res.json['results'][0], 'EntityReference')

    def test_entity_tags(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'Person',
            'collection_id': self.col_id,
            'properties': {
                'name': "Blaaaa blubb",
                'phone': '+491769817271'
            }
        }
        resa = self.client.post(url, data=json.dumps(data),
                                headers=headers,
                                content_type='application/json')
        data = {
            'schema': 'Person',
            'collection_id': self.col_id,
            'properties': {
                'name': "Nobody Man",
                'phone': '+491769817271'
            }
        }
        resa = self.client.post(url, data=json.dumps(data),
                                headers=headers,
                                content_type='application/json')
        url = '/api/2/entities/%s/tags' % resa.json['id']
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, (res.status_code, res.json)
        results = res.json['results']
        assert len(results) == 1, results
        assert results[0]['value'] == '+491769817271', results
        validate(res.json['results'][0], 'EntityTag')

    def test_undelete(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        data = {
            'schema': 'Person',
            'properties': {
                'name': "Mr. Mango",
            },
            'collection_id': self.col_id
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, (res.status_code, res.json)
        id1 = res.json['id']

        url = '/api/2/entities/%s' % id1
        res = self.client.delete(url, headers=headers)
        assert res.status_code == 204, res.status_code
        res = self.client.get(url, headers=headers)
        assert res.status_code == 404, res.status_code

        # test undelete with property update
        url = '/api/2/entities/%s' % id1
        data = {
            'schema': 'Person',
            'properties': {
                'name': "Mr. Mango",
                'status': 'ripe',
            },
            'collection_id': self.col_id
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, res.status_code
        validate(res.json, 'Entity')
        assert res.json['properties']['name'] == ['Mr. Mango'], res.json
        assert res.json['properties']['status'] == ['ripe'], res.json

        url = '/api/2/entities/%s' % id1
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res.status_code
        assert res.json['properties']['name'] == ['Mr. Mango'], res.json
        assert res.json['properties']['status'] == ['ripe'], res.json

        # Test undelete existing entity
        url = '/api/2/entities/%s' % id1
        data = {
            'schema': 'Person',
            'properties': {
                'name': "Mr. Mango",
                'status': 'ripe',
                'email': 'mango@mango.yum',
            }
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, res.status_code
        validate(res.json, 'Entity')
        assert res.json['properties']['name'] == ['Mr. Mango'], res.json
        assert res.json['properties']['status'] == ['ripe'], res.json
        assert res.json['properties']['email'] == ['mango@mango.yum'], res.json  # noqa

        # test create entity with undelete
        id2 = "randomid"
        url = '/api/2/entities/%s' % id2
        data = {
            'schema': 'Person',
            'properties': {
                'name': 'Mr. Banana',
            },
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 404, res.status_code
        data['collection_id'] = self.col_id
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        assert res.status_code == 200, res.status_code
        validate(res.json, 'Entity')
        assert res.json['id'] != id2, res.json
        assert res.json['properties']['name'] == ['Mr. Banana'], res.json

    def test_recursive_delete(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        headers['Content-Type'] = 'application/json'
        data1 = json.dumps({
            'schema': 'Person',
            'properties': {
                'name': "Osama bin Laden",
            },
            'collection_id': self.col_id
        })
        res1 = self.client.post(url, data=data1, headers=headers)
        id1 = res1.json['id']
        data2 = json.dumps({
            'schema': 'Organization',
            'properties': {
                'name': 'Al-Qaeda',
            },
            'collection_id': self.col_id
        })
        res2 = self.client.post(url, data=data2, headers=headers)
        id2 = res2.json['id']
        data3 = json.dumps({
            'schema': 'Membership',
            'properties': {
                'member': id1,
                'organization': id2,
            },
            'collection_id': self.col_id
        })
        res3 = self.client.post(url, data=data3, headers=headers)
        id3 = res3.json['id']

        # Deleting a thing, deletes associated edge.
        url = '/api/2/entities/%s' % id1
        res = self.client.delete(url, headers=headers)
        assert res.status_code == 204, res.status_code
        url = '/api/2/entities/%s' % id3
        res = self.client.get(url, headers=headers)
        assert res.status_code == 404, res.status_code
        url = '/api/2/entities/%s' % id2
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res.status_code

        # undelete
        url = '/api/2/entities/%s' % id1
        res = self.client.post(url, data=data1, headers=headers)
        assert res.json['id'] == id1, (res.json['id'], id1)
        url = '/api/2/entities/%s' % id3
        self.client.post(url, data=data3, headers=headers)
        url = '/api/2/entities/%s' % id1
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res.status_code
        url = '/api/2/entities/%s' % id3
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res.status_code

        # Deleting a edge, should not delete associated things
        url = '/api/2/entities/%s' % id3
        res = self.client.delete(url, headers=headers)
        assert res.status_code == 204, res.status_code
        url = '/api/2/entities/%s' % id1
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res.status_code
        url = '/api/2/entities/%s' % id2
        res = self.client.get(url, headers=headers)
        assert res.status_code == 200, res.status_code

    def test_maintain_property_order(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities'
        countries = ['gb', 'us', 'nl', 'in', 'jp', 'au', 'nz', 'sl']
        data = {
            'schema': 'Person',
            'properties': {
                'name': "Mr. Banana",
                'country': countries
            },
            'collection_id': self.col_id
        }
        res = self.client.post(url,
                               data=json.dumps(data),
                               headers=headers,
                               content_type='application/json')
        url = '/api/2/entities/%s' % res.json['id']
        res = self.client.get(url, headers=headers)
        assert res.json['properties']['country'] == countries, res.json['properties']['country']  # noqa

    def test_sort_by_date(self):
        _, headers = self.login(is_admin=True)
        url = '/api/2/entities?filter:schemata=Thing&sort=dates%3Aasc'
        res = self.client.get(url, headers=headers, content_type='application/json')  # noqa
        assert res.json['results'][0]['id'] == self.ent.id, res.json
        assert res.json['results'][1]['id'] == self.ent2.id, res.json
        assert res.json['results'][2]['id'] == self.book.id, res.json
        url = '/api/2/entities?filter:schemata=Thing&sort=dates%3Adesc'
        res = self.client.get(url, headers=headers, content_type='application/json')  # noqa
        assert res.json['results'][0]['id'] == self.ent2.id, res.json
        assert res.json['results'][1]['id'] == self.ent.id, res.json
        assert res.json['results'][2]['id'] == self.book.id, res.json
