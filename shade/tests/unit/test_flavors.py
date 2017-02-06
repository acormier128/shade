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


import shade
from shade.tests import fakes
from shade.tests.unit import base


class TestFlavors(base.RequestsMockTestCase):

    def test_create_flavor(self):

        self.register_uri(
            'POST', '{endpoint}/flavors'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavor': fakes.FAKE_FLAVOR},
            validate=dict(
                json={'flavor': {
                    "name": "vanilla",
                    "ram": 65536,
                    "vcpus": 24,
                    "swap": 0,
                    "os-flavor-access:is_public": True,
                    "rxtx_factor": 1.0,
                    "OS-FLV-EXT-DATA:ephemeral": 0,
                    "disk": 1600,
                    "id": None
                }}))

        self.register_uri(
            'GET', '{endpoint}/flavors/{id}'.format(
                endpoint=fakes.ENDPOINT, id=fakes.FLAVOR_ID),
            json={'flavor': fakes.FAKE_FLAVOR})

        self.op_cloud.create_flavor(
            'vanilla', ram=65536, disk=1600, vcpus=24,
        )
        self.assert_calls()

    def test_delete_flavor(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': fakes.FAKE_FLAVOR_LIST})
        self.register_uri(
            'DELETE', '{endpoint}/flavors/{id}'.format(
                endpoint=fakes.ENDPOINT, id=fakes.FLAVOR_ID))
        self.assertTrue(self.op_cloud.delete_flavor('vanilla'))

        self.assert_calls()

    def test_delete_flavor_not_found(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': fakes.FAKE_FLAVOR_LIST})

        self.assertFalse(self.op_cloud.delete_flavor('invalid'))

        self.assert_calls()

    def test_delete_flavor_exception(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': fakes.FAKE_FLAVOR_LIST})
        self.register_uri(
            'DELETE', '{endpoint}/flavors/{id}'.format(
                endpoint=fakes.ENDPOINT, id=fakes.FLAVOR_ID),
            status_code=503)
        self.assertRaises(shade.OpenStackCloudException,
                          self.op_cloud.delete_flavor, 'vanilla')

    def test_list_flavors(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': fakes.FAKE_FLAVOR_LIST})
        for flavor in fakes.FAKE_FLAVOR_LIST:
            self.register_uri(
                'GET', '{endpoint}/flavors/{id}/os-extra_specs'.format(
                    endpoint=fakes.ENDPOINT, id=flavor['id']),
                json={'extra_specs': {}})

        flavors = self.cloud.list_flavors()

        # test that new flavor is created correctly
        found = False
        for flavor in flavors:
            if flavor['name'] == 'vanilla':
                found = True
                break
        self.assertTrue(found)
        needed_keys = {'name', 'ram', 'vcpus', 'id', 'is_public', 'disk'}
        if found:
            # check flavor content
            self.assertTrue(needed_keys.issubset(flavor.keys()))
        self.assert_calls()

    def test_get_flavor_by_ram(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': fakes.FAKE_FLAVOR_LIST})
        for flavor in fakes.FAKE_FLAVOR_LIST:
            self.register_uri(
                'GET', '{endpoint}/flavors/{id}/os-extra_specs'.format(
                    endpoint=fakes.ENDPOINT, id=flavor['id']),
                json={'extra_specs': {}})

        flavor = self.cloud.get_flavor_by_ram(ram=250)
        self.assertEqual(fakes.STRAWBERRY_FLAVOR_ID, flavor['id'])

    def test_get_flavor_by_ram_and_include(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': fakes.FAKE_FLAVOR_LIST})
        for flavor in fakes.FAKE_FLAVOR_LIST:
            self.register_uri(
                'GET', '{endpoint}/flavors/{id}/os-extra_specs'.format(
                    endpoint=fakes.ENDPOINT, id=flavor['id']),
                json={'extra_specs': {}})
        flavor = self.cloud.get_flavor_by_ram(ram=150, include='strawberry')
        self.assertEqual(fakes.STRAWBERRY_FLAVOR_ID, flavor['id'])

    def test_get_flavor_by_ram_not_found(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': []})
        self.assertRaises(
            shade.OpenStackCloudException,
            self.cloud.get_flavor_by_ram,
            ram=100)

    def test_get_flavor_string_and_int(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': [fakes.make_fake_flavor('1', 'vanilla')]})
        self.register_uri(
            'GET', '{endpoint}/flavors/1/os-extra_specs'.format(
                endpoint=fakes.ENDPOINT),
            json={'extra_specs': {}})
        self.register_uri(
            'GET', '{endpoint}/flavors/detail?is_public=None'.format(
                endpoint=fakes.ENDPOINT),
            json={'flavors': [fakes.make_fake_flavor('1', 'vanilla')]})
        self.register_uri(
            'GET', '{endpoint}/flavors/1/os-extra_specs'.format(
                endpoint=fakes.ENDPOINT),
            json={'extra_specs': {}})

        flavor1 = self.cloud.get_flavor('1')
        self.assertEqual('1', flavor1['id'])
        flavor2 = self.cloud.get_flavor(1)
        self.assertEqual('1', flavor2['id'])

    def test_set_flavor_specs(self):
        extra_specs = dict(key1='value1')
        self.register_uri(
            'POST', '{endpoint}/flavors/{id}/os-extra_specs'.format(
                endpoint=fakes.ENDPOINT, id=1),
            json=dict(extra_specs=extra_specs))

        self.op_cloud.set_flavor_specs(1, extra_specs)
        self.assert_calls()

    def test_unset_flavor_specs(self):
        keys = ['key1', 'key2']
        for key in keys:
            self.register_uri(
                'DELETE',
                '{endpoint}/flavors/{id}/os-extra_specs/{key}'.format(
                    endpoint=fakes.ENDPOINT, id=1, key=key))

        self.op_cloud.unset_flavor_specs(1, keys)
        self.assert_calls()

    def test_add_flavor_access(self):
        self.register_uri(
            'POST', '{endpoint}/flavors/{id}/action'.format(
                endpoint=fakes.ENDPOINT, id='flavor_id'),
            json={
                'flavor_access': [{
                    'flavor_id': 'flavor_id',
                    'tenant_id': 'tenant_id',
                }]},
            validate=dict(
                json={
                    'addTenantAccess': {
                        'tenant': 'tenant_id',
                    }}))

        self.op_cloud.add_flavor_access('flavor_id', 'tenant_id')
        self.assert_calls()

    def test_remove_flavor_access(self):
        self.register_uri(
            'POST', '{endpoint}/flavors/{id}/action'.format(
                endpoint=fakes.ENDPOINT, id='flavor_id'),
            json={'flavor_access': []},
            validate=dict(
                json={
                    'removeTenantAccess': {
                        'tenant': 'tenant_id',
                    }}))

        self.op_cloud.remove_flavor_access('flavor_id', 'tenant_id')
        self.assert_calls()

    def test_list_flavor_access(self):
        self.register_uri(
            'GET', '{endpoint}/flavors/vanilla/os-flavor-access'.format(
                endpoint=fakes.ENDPOINT),
            json={
                'flavor_access': [{
                    'flavor_id': 'vanilla',
                    'tenant_id': 'tenant_id',
                }]})
        self.op_cloud.list_flavor_access('vanilla')
        self.assert_calls()
