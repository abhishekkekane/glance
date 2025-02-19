# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy

from glance.common import config
from glance.common import exception
from glance import context
import glance.tests.functional.db as db_tests
from glance.tests import utils as test_utils


def build_namespace_fixture(**kwargs):
    namespace = {
        'namespace': u'MyTestNamespace',
        'display_name': u'test-display-name',
        'description': u'test-description',
        'visibility': u'public',
        'protected': 0,
        'owner': u'test-owner'
    }
    namespace.update(kwargs)
    return namespace


def build_resource_type_fixture(**kwargs):
    resource_type = {
        'name': u'MyTestResourceType',
        'protected': 0
    }
    resource_type.update(kwargs)
    return resource_type


def build_association_fixture(**kwargs):
    association = {
        'name': u'MyTestResourceType',
        'properties_target': 'test-properties-target',
        'prefix': 'test-prefix'
    }
    association.update(kwargs)
    return association


def build_object_fixture(**kwargs):
    # Full testing of required and schema done via rest api tests
    object = {
        'namespace_id': 1,
        'name': u'test-object-name',
        'description': u'test-object-description',
        'required': u'fake-required-properties-list',
        'json_schema': u'{fake-schema}'
    }
    object.update(kwargs)
    return object


def build_property_fixture(**kwargs):
    # Full testing of required and schema done via rest api tests
    property = {
        'namespace_id': 1,
        'name': u'test-property-name',
        'json_schema': u'{fake-schema}'
    }
    property.update(kwargs)
    return property


class TestMetadefDriver(test_utils.BaseTestCase):

    """Test Driver class for Metadef tests."""

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestMetadefDriver, self).setUp()
        config.parse_args(args=[])
        context_cls = context.RequestContext
        self.adm_context = context_cls(is_admin=True,
                                       auth_token='user:user:admin')
        self.context = context_cls(is_admin=False,
                                   auth_token='user:user:user')
        self.db_api = db_tests.get_db(self.config)
        db_tests.reset_db(self.db_api)

    def _assert_saved_fields(self, expected, actual):
        for k in expected.keys():
            self.assertEqual(expected[k], actual[k])


class MetadefNamespaceTests(object):

    def test_namespace_create(self):
        fixture = build_namespace_fixture()
        created = self.db_api.metadef_namespace_create(self.context, fixture)
        self.assertIsNotNone(created)
        self._assert_saved_fields(fixture, created)

    def test_namespace_get(self):
        fixture = build_namespace_fixture()
        created = self.db_api.metadef_namespace_create(self.context, fixture)
        self.assertIsNotNone(created)
        self._assert_saved_fields(fixture, created)

        found = self.db_api.metadef_namespace_get(
            self.context, created['namespace'])
        self.assertIsNotNone(found, "Namespace not found.")

    def test_namespace_get_all_with_resource_types_filter(self):
        ns_fixture = build_namespace_fixture()
        ns_created = self.db_api.metadef_namespace_create(
            self.context, ns_fixture)
        self.assertIsNotNone(ns_created, "Could not create a namespace.")
        self._assert_saved_fields(ns_fixture, ns_created)

        fixture = build_association_fixture()
        created = self.db_api.metadef_resource_type_association_create(
            self.context, ns_created['namespace'], fixture)
        self.assertIsNotNone(created, "Could not create an association.")

        rt_filters = {'resource_types': fixture['name']}
        found = self.db_api.\
            metadef_namespace_get_all(self.context, filters=rt_filters,
                                      sort_key='created_at')
        self.assertEqual(len(found), 1)
        for item in found:
            self._assert_saved_fields(ns_fixture, item)

    def test_namespace_update(self):
        delta = {'owner': u'New Owner'}
        fixture = build_namespace_fixture()

        created = self.db_api.metadef_namespace_create(self.context, fixture)
        self.assertIsNotNone(created['namespace'])
        self.assertEqual(created['namespace'], fixture['namespace'])
        delta_dict = copy.deepcopy(created)
        delta_dict.update(delta.copy())

        updated = self.db_api.metadef_namespace_update(
            self.context, created['id'], delta_dict)
        self.assertEqual(delta['owner'], updated['owner'])

    def test_namespace_delete(self):
        fixture = build_namespace_fixture()
        created = self.db_api.metadef_namespace_create(self.context, fixture)
        self.assertIsNotNone(created, "Could not create a Namespace.")
        self.db_api.metadef_namespace_delete(
            self.context, created['namespace'])
        self.assertRaises(exception.NotFound,
                          self.db_api.metadef_namespace_get,
                          self.context, created['namespace'])

    def test_namespace_delete_with_content(self):
        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(
            self.context, fixture_ns)
        self._assert_saved_fields(fixture_ns, created_ns)

        # Create object content for the namespace
        fixture_obj = build_object_fixture()
        created_obj = self.db_api.metadef_object_create(
            self.context, created_ns['namespace'], fixture_obj)
        self.assertIsNotNone(created_obj)

        # Create property content for the namespace
        fixture_prop = build_property_fixture(namespace_id=created_ns['id'])
        created_prop = self.db_api.metadef_property_create(
            self.context, created_ns['namespace'], fixture_prop)
        self.assertIsNotNone(created_prop)

        # Create associations
        fixture_assn = build_association_fixture()
        created_assn = self.db_api.metadef_resource_type_association_create(
            self.context, created_ns['namespace'], fixture_assn)
        self.assertIsNotNone(created_assn)

        deleted_ns = self.db_api.metadef_namespace_delete(
            self.context, created_ns['namespace'])

        self.assertRaises(exception.NotFound,
                          self.db_api.metadef_namespace_get,
                          self.context, deleted_ns['namespace'])


class MetadefPropertyTests(object):

    def test_property_create(self):
        fixture = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(
            self.context, fixture)
        self.assertIsNotNone(created_ns)
        self._assert_saved_fields(fixture, created_ns)

        fixture_prop = build_property_fixture(namespace_id=created_ns['id'])
        created_prop = self.db_api.metadef_property_create(
            self.context, created_ns['namespace'], fixture_prop)
        self._assert_saved_fields(fixture_prop, created_prop)

    def test_property_get(self):
        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(
            self.context, fixture_ns)
        self.assertIsNotNone(created_ns)
        self._assert_saved_fields(fixture_ns, created_ns)

        fixture_prop = build_property_fixture(namespace_id=created_ns['id'])
        created_prop = self.db_api.metadef_property_create(
            self.context, created_ns['namespace'], fixture_prop)

        found_prop = self.db_api.metadef_property_get(
            self.context, created_ns['namespace'], created_prop['name'])
        self._assert_saved_fields(fixture_prop, found_prop)

    def test_property_get_all(self):
        ns_fixture = build_namespace_fixture()
        ns_created = self.db_api.metadef_namespace_create(
            self.context, ns_fixture)
        self.assertIsNotNone(ns_created, "Could not create a namespace.")
        self._assert_saved_fields(ns_fixture, ns_created)

        fixture1 = build_property_fixture(namespace_id=ns_created['id'])
        created_p1 = self.db_api.metadef_property_create(
            self.context, ns_created['namespace'], fixture1)
        self.assertIsNotNone(created_p1, "Could not create a property.")

        fixture2 = build_property_fixture(namespace_id=ns_created['id'],
                                          name='test-prop-2')
        created_p2 = self.db_api.metadef_property_create(
            self.context, ns_created['namespace'], fixture2)
        self.assertIsNotNone(created_p2, "Could not create a property.")

        found = self.db_api.\
            metadef_property_get_all(self.context, ns_created['namespace'])
        self.assertEqual(len(found), 2)

    def test_property_update(self):
        delta = {'name': u'New-name', 'json_schema': u'new-schema'}

        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(
            self.context, fixture_ns)
        self.assertIsNotNone(created_ns['namespace'])

        prop_fixture = build_property_fixture(namespace_id=created_ns['id'])
        created_prop = self.db_api.metadef_property_create(
            self.context, created_ns['namespace'], prop_fixture)
        self.assertIsNotNone(created_prop, "Could not create a property.")

        delta_dict = copy.deepcopy(created_prop)
        delta_dict.update(delta.copy())

        updated = self.db_api.metadef_property_update(
            self.context, created_ns['namespace'],
            created_prop['id'], delta_dict)
        self.assertEqual(delta['name'], updated['name'])
        self.assertEqual(delta['json_schema'], updated['json_schema'])

    def test_property_delete(self):
        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(
            self.context, fixture_ns)
        self.assertIsNotNone(created_ns['namespace'])

        prop_fixture = build_property_fixture(namespace_id=created_ns['id'])
        created_prop = self.db_api.metadef_property_create(
            self.context, created_ns['namespace'], prop_fixture)
        self.assertIsNotNone(created_prop, "Could not create a property.")

        self.db_api.metadef_property_delete(
            self.context, created_ns['namespace'], created_prop['name'])
        self.assertRaises(exception.NotFound,
                          self.db_api.metadef_property_get,
                          self.context, created_ns['namespace'],
                          created_prop['name'])

    def test_property_delete_namespace_content(self):
        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(
            self.context, fixture_ns)
        self.assertIsNotNone(created_ns['namespace'])

        prop_fixture = build_property_fixture(namespace_id=created_ns['id'])
        created_prop = self.db_api.metadef_property_create(
            self.context, created_ns['namespace'], prop_fixture)
        self.assertIsNotNone(created_prop, "Could not create a property.")

        self.db_api.metadef_property_delete_namespace_content(
            self.context, created_ns['namespace'])
        self.assertRaises(exception.NotFound,
                          self.db_api.metadef_property_get,
                          self.context, created_ns['namespace'],
                          created_prop['name'])


class MetadefObjectTests(object):

    def test_object_create(self):
        fixture = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(self.context,
                                                          fixture)
        self.assertIsNotNone(created_ns)
        self._assert_saved_fields(fixture, created_ns)

        fixture_object = build_object_fixture(namespace_id=created_ns['id'])
        created_object = self.db_api.metadef_object_create(
            self.context, created_ns['namespace'], fixture_object)
        self._assert_saved_fields(fixture_object, created_object)

    def test_object_get(self):
        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(self.context,
                                                          fixture_ns)
        self.assertIsNotNone(created_ns)
        self._assert_saved_fields(fixture_ns, created_ns)

        fixture_object = build_object_fixture(namespace_id=created_ns['id'])
        created_object = self.db_api.metadef_object_create(
            self.context, created_ns['namespace'], fixture_object)

        found_object = self.db_api.metadef_object_get(
            self.context, created_ns['namespace'], created_object['name'])
        self._assert_saved_fields(fixture_object, found_object)

    def test_object_get_all(self):
        ns_fixture = build_namespace_fixture()
        ns_created = self.db_api.metadef_namespace_create(self.context,
                                                          ns_fixture)
        self.assertIsNotNone(ns_created, "Could not create a namespace.")
        self._assert_saved_fields(ns_fixture, ns_created)

        fixture1 = build_object_fixture(namespace_id=ns_created['id'])
        created_o1 = self.db_api.metadef_object_create(
            self.context, ns_created['namespace'], fixture1)
        self.assertIsNotNone(created_o1, "Could not create an object.")

        fixture2 = build_object_fixture(namespace_id=ns_created['id'],
                                        name='test-object-2')
        created_o2 = self.db_api.metadef_object_create(
            self.context, ns_created['namespace'], fixture2)
        self.assertIsNotNone(created_o2, "Could not create an object.")

        found = self.db_api.\
            metadef_object_get_all(self.context, ns_created['namespace'])
        self.assertEqual(len(found), 2)

    def test_object_update(self):
        delta = {'name': u'New-name', 'json_schema': u'new-schema',
                 'required': u'new-required'}

        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(self.context,
                                                          fixture_ns)
        self.assertIsNotNone(created_ns['namespace'])

        object_fixture = build_object_fixture(namespace_id=created_ns['id'])
        created_object = self.db_api.metadef_object_create(
            self.context, created_ns['namespace'], object_fixture)
        self.assertIsNotNone(created_object, "Could not create an object.")

        delta_dict = {}
        delta_dict.update(delta.copy())

        updated = self.db_api.metadef_object_update(
            self.context, created_ns['namespace'],
            created_object['id'], delta_dict)
        self.assertEqual(delta['name'], updated['name'])
        self.assertEqual(delta['json_schema'], updated['json_schema'])

    def test_object_delete(self):
        fixture_ns = build_namespace_fixture()
        created_ns = self.db_api.metadef_namespace_create(
            self.context, fixture_ns)
        self.assertIsNotNone(created_ns['namespace'])

        object_fixture = build_object_fixture(namespace_id=created_ns['id'])
        created_object = self.db_api.metadef_object_create(
            self.context, created_ns['namespace'], object_fixture)
        self.assertIsNotNone(created_object, "Could not create an object.")

        self.db_api.metadef_object_delete(
            self.context, created_ns['namespace'], created_object['name'])
        self.assertRaises(exception.NotFound,
                          self.db_api.metadef_object_get,
                          self.context, created_ns['namespace'],
                          created_object['name'])


class MetadefResourceTypeTests(object):

    def test_resource_type_get_all(self):
        resource_types_orig = self.db_api.metadef_resource_type_get_all(
            self.context)

        fixture = build_resource_type_fixture()
        self.db_api.metadef_resource_type_create(self.context, fixture)

        resource_types = self.db_api.metadef_resource_type_get_all(
            self.context)

        test_len = len(resource_types_orig) + 1
        self.assertEqual(len(resource_types), test_len)


class MetadefResourceTypeAssociationTests(object):

    def test_association_create(self):
        ns_fixture = build_namespace_fixture()
        ns_created = self.db_api.metadef_namespace_create(
            self.context, ns_fixture)
        self.assertIsNotNone(ns_created)
        self._assert_saved_fields(ns_fixture, ns_created)

        assn_fixture = build_association_fixture()
        assn_created = self.db_api.metadef_resource_type_association_create(
            self.context, ns_created['namespace'], assn_fixture)
        self.assertIsNotNone(assn_created)
        self._assert_saved_fields(assn_fixture, assn_created)

    def test_association_delete(self):
        ns_fixture = build_namespace_fixture()
        ns_created = self.db_api.metadef_namespace_create(
            self.context, ns_fixture)
        self.assertIsNotNone(ns_created, "Could not create a namespace.")
        self._assert_saved_fields(ns_fixture, ns_created)

        fixture = build_association_fixture()
        created = self.db_api.metadef_resource_type_association_create(
            self.context, ns_created['namespace'], fixture)
        self.assertIsNotNone(created, "Could not create an association.")

        created_resource = self.db_api.metadef_resource_type_get(
            self.context, fixture['name'])
        self.assertIsNotNone(created_resource, "resource_type not created")

        self.db_api.metadef_resource_type_association_delete(
            self.context, ns_created['namespace'], created_resource['name'])
        self.assertRaises(exception.NotFound,
                          self.db_api.metadef_resource_type_association_get,
                          self.context, ns_created['namespace'],
                          created_resource['name'])

    def test_association_get_all_by_namespace(self):
        ns_fixture = build_namespace_fixture()
        ns_created = self.db_api.metadef_namespace_create(
            self.context, ns_fixture)
        self.assertIsNotNone(ns_created, "Could not create a namespace.")
        self._assert_saved_fields(ns_fixture, ns_created)

        fixture = build_association_fixture()
        created = self.db_api.metadef_resource_type_association_create(
            self.context, ns_created['namespace'], fixture)
        self.assertIsNotNone(created, "Could not create an association.")

        found = self.db_api.\
            metadef_resource_type_association_get_all_by_namespace(
                self.context, ns_created['namespace'])
        self.assertEqual(len(found), 1)
        for item in found:
            self._assert_saved_fields(fixture, item)


class MetadefDriverTests(MetadefNamespaceTests,
                         MetadefResourceTypeTests,
                         MetadefResourceTypeAssociationTests,
                         MetadefPropertyTests,
                         MetadefObjectTests):
    # collection class
    pass
