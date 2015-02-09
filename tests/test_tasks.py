
from anchor import setup_application
from datetime import datetime
from dateutil.relativedelta import relativedelta
from uuid import uuid4


import unittest
import anchor
import uuid
import json
import re
import mock


class AnchorCeleryTests(unittest.TestCase):
    def setUp(self):
        self.app, self.db = setup_application.create_app('True')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.client.get('/')

        self.tasks = anchor.tasks
        if not re.search('_test', self.tasks.config.MONGO_DATABASE):
            self.tasks.config.MONGO_DATABASE = (
                '%s_test' % self.tasks.config.MONGO_DATABASE
            )

        self.tasks.config.BROKER_URL = 'memory://'
        self.tasks.config.CELERY_RESULT_BACKEND = 'cache'
        self.tasks.config.CELERY_CACHE_BACKEND = 'memory'
        self.tasks.db = self.db

    def tearDown(self):
        self.db.sessions.remove()
        self.db.settings.remove()
        self.db.accounts.remove()
        self.db.forms.remove()

    def setup_user_login(self, sess):
        sess['username'] = 'test'
        sess['csrf_token'] = 'csrf_token'
        sess['role'] = 'logged_in'
        sess['_permanent'] = True
        sess['ddi'] = '654846'
        sess['cloud_token'] = uuid4().hex

    def setup_admin_login(self, sess):
        sess['username'] = 'oldarmyc'
        sess['csrf_token'] = 'csrf_token'
        sess['role'] = 'administrators'
        sess['_permanent'] = True
        sess['ddi'] = '654846'
        sess['cloud_token'] = uuid4().hex

    def setup_useable_admin(self):
        self.db.settings.update(
            {}, {
                '$push': {
                    'administrators': {
                        'admin': 'test1234',
                        'admin_name': 'Test Admin'
                    }
                }
            }
        )

    def setup_useable_account(self):
        data = {
            'host_servers': [
                'f0ab54576022b02c128b9516ef23a9947c73a8564ca79c7d1debb015',
            ],
            'region': 'iad',
            'cache_expiration': datetime.now() + relativedelta(days=1),
            'servers': [
                {
                    'state': 'active',
                    'name': 'test-server',
                    'created': '2015-02-04T14:11:09Z',
                    'host_id': (
                        'f0ab54576022b02c128b9516ef23a99'
                        '47c73a8564ca79c7d1debb015'
                    ),
                    'flavor': 'general1-1',
                    'id': '00000000-1111-2222-3333-444444444444',
                    'private': [
                        '10.10.10.10'
                    ],
                    'public': [
                        '162.162.162.162',
                        '2001:2001:2001:102:2001:2001:2001:2001'
                    ]
                },
            ],
            'token': 'd6ffb5c691a644a4b527f8ddc64c180f',
            'account_number': '123456'
        }
        self.db.accounts.insert(data)

    def setup_cloud_server_details_single_return(self):
        return {
            'server': {
                'OS-EXT-STS:task_state': None,
                'addresses': {
                    'public': [
                        {
                            'version': 4,
                            'addr': '104.104.104.104'
                        }, {
                            'version': 6,
                            'addr': '2001:2001:2001:104:2001:2001:2001:2001'
                        }
                    ],
                    'private': [
                        {
                            'version': 4,
                            'addr': '10.10.10.10'
                        }
                    ]
                },
                'links': [
                    {
                        'href': (
                            'https://iad.servers.api.rackspacecloud.com/v2/123'
                            '456/servers/11111111-2222-3333-4444-55555555555'
                        ),
                        'rel': 'self'
                    }, {
                        'href': (
                            'https://iad.servers.api.rackspacecloud.com/123'
                            '456/servers/11111111-2222-3333-4444-55555555555'
                        ),
                        'rel': 'bookmark'
                    }
                ],
                'image': {
                    'id': '99999999-8888-7777-6666-555555555555',
                    'links': [
                        {
                            'href': (
                                'https://iad.servers.api.rackspacecloud.com/12'
                                '3456/images/99999999-8888-7777-6666-'
                                '555555555555'
                            ),
                            'rel': 'bookmark'
                        }
                    ]
                },
                'OS-EXT-STS:vm_state': 'active',
                'flavor': {
                    'id': 'performance1-2',
                    'links': [
                        {
                            'href': (
                                'https://iad.servers.api.rackspacecloud.com/'
                                '123456/flavors/performance1-2'
                            ),
                            'rel': 'bookmark'
                        }
                    ]
                },
                'id': '11111111-2222-3333-4444-55555555555',
                'user_id': '284275',
                'OS-DCF:diskConfig': 'MANUAL',
                'accessIPv4': '104.104.104.104',
                'accessIPv6': '2001:2001:2001:104:2001:2001:2001:2001',
                'progress': 100,
                'OS-EXT-STS:power_state': 1,
                'config_drive': '',
                'status': 'ACTIVE',
                'updated': '2014-12-04T16:49:37Z',
                'hostId': (
                    '16cde3191df1e6c9fa4dad65eacd4dc7c90d60bca3589ac48f55aae8'
                ),
                'name': 'test_server_awesome',
                'created': '2015-01-01T16:06:05Z',
                'tenant_id': '123456',
            }
        }

    def setup_servers_details_return(self):
        return {
            'servers': [
                {
                    'OS-EXT-STS:task_state': None,
                    'addresses': {
                        'public': [
                            {
                                'version': 4,
                                'addr': '104.104.104.104'
                            }, {
                                'version': 6,
                                'addr': (
                                    '2001:2001:2001:104:2001:2001:2001:2001'
                                )
                            }
                        ],
                        'private': [
                            {
                                'version': 4,
                                'addr': '10.10.10.10'
                            }
                        ]
                    },
                    'links': [
                        {
                            'href': (
                                'https://iad.servers.api.rackspacecloud.com'
                                '/v2/123456/servers/11111111-2222-3333-4444'
                                '-55555555555'
                            ),
                            'rel': 'self'
                        }, {
                            'href': (
                                'https://iad.servers.api.rackspacecloud.'
                                'com/123456/servers/11111111-2222-3333-4444-'
                                '55555555555'
                            ),
                            'rel': 'bookmark'
                        }
                    ],
                    'image': {
                        'id': '99999999-8888-7777-6666-555555555555',
                        'links': [
                            {
                                'href': (
                                    'https://iad.servers.api.rackspacecloud.'
                                    'com/123456/images/99999999-8888-7777-6666'
                                    '-555555555555'
                                ),
                                'rel': 'bookmark'
                            }
                        ]
                    },
                    'OS-EXT-STS:vm_state': 'active',
                    'flavor': {
                        'id': 'performance1-2',
                        'links': [
                            {
                                'href': (
                                    'https://iad.servers.api.rackspacecloud.'
                                    'com/123456/flavors/performance1-2'
                                ),
                                'rel': 'bookmark'
                            }
                        ]
                    },
                    'id': '11111111-2222-3333-4444-55555555555',
                    'user_id': '284275',
                    'OS-DCF:diskConfig': 'MANUAL',
                    'accessIPv4': '104.130.6.172',
                    'accessIPv6': '2001:4802:7802:104:c573:b34f:8ae3:abd0',
                    'progress': 100,
                    'OS-EXT-STS:power_state': 1,
                    'config_drive': '',
                    'status': 'ACTIVE',
                    'updated': '2014-12-04T16:49:37Z',
                    'hostId': (
                        '16cde3191df1e6c9fa4dad65eacd4dc7'
                        'c90d60bca3589ac48f55aae8'
                    ),
                    'name': 'test_server_awesome',
                    'created': '2015-01-01T16:06:05Z',
                    'tenant_id': '123456',
                }, {
                    'OS-EXT-STS:task_state': None,
                    'addresses': {
                        'public': [
                            {
                                'version': 4,
                                'addr': '104.104.104.104'
                            }, {
                                'version': 6,
                                'addr': (
                                    '2020:2020:2020:104:2020:2020:2020:2020'
                                )
                            }
                        ],
                        'private': [
                            {
                                'version': 4,
                                'addr': '10.11.11.11'
                            }
                        ]
                    },
                    'links': [
                        {
                            'href': (
                                'https://iad.servers.api.rackspacecloud.com'
                                '/v2/123456/servers/11111111-2222-3333-4444'
                                '-55555555555'
                            ),
                            'rel': 'self'
                        }, {
                            'href': (
                                'https://iad.servers.api.rackspacecloud.'
                                'com/123456/servers/11111111-2222-3333-4444-'
                                '55555555555'
                            ),
                            'rel': 'bookmark'
                        }
                    ],
                    'image': {
                        'id': '99999999-8888-7777-6666-555555555555',
                        'links': [
                            {
                                'href': (
                                    'https://iad.servers.api.rackspacecloud.'
                                    'com/123456/images/99999999-8888-7777-6666'
                                    '-555555555555'
                                ),
                                'rel': 'bookmark'
                            }
                        ]
                    },
                    'OS-EXT-STS:vm_state': 'active',
                    'flavor': {
                        'id': 'performance1-2',
                        'links': [
                            {
                                'href': (
                                    'https://iad.servers.api.rackspacecloud.'
                                    'com/123456/flavors/performance1-2'
                                ),
                                'rel': 'bookmark'
                            }
                        ]
                    },
                    'id': '22222222-3333-4444-5555-66666666666',
                    'user_id': '284275',
                    'OS-DCF:diskConfig': 'MANUAL',
                    'accessIPv4': '104.130.130.130',
                    'accessIPv6': '2020:2020:2020:104:2020:2020:2020:2020',
                    'progress': 100,
                    'OS-EXT-STS:power_state': 1,
                    'config_drive': '',
                    'status': 'ACTIVE',
                    'updated': '2014-12-04T16:49:37Z',
                    'hostId': (
                        'b4631f368e35d06bef81053b66e5'
                        '40c95836fc0eb796176dc624a2cd'
                    ),
                    'name': 'test_server',
                    'created': '2015-01-01T16:06:05Z',
                    'tenant_id': '123456',
                }

            ]
        }

    def test_celery_add_server_to_cache(self):
        self.setup_useable_account()
        account_data = self.db.accounts.find_one()
        cloud_return = self.setup_cloud_server_details_single_return()
        with self.app.test_client() as c:
            with c.session_transaction() as sess:
                self.setup_user_login(sess)

            with mock.patch(
                'anchor.tasks.config.CELERY_ALWAYS_EAGER',
                True,
                create=True
            ):
                with mock.patch('requests.get') as patched_get:
                    patched_get.return_value.content = json.dumps(cloud_return)
                    task = self.tasks.check_add_server_to_cache(
                        uuid.uuid4().hex,
                        'iad',
                        '123456',
                        '11111111-2222-3333-4444-55555555555',
                        account_data
                    )
                    assert not task, (
                        'Expecting false to be returned, but got true instead'
                    )

        updated_account = self.db.accounts.find_one()
        self.assertEquals(
            len(updated_account.get('servers')),
            len(account_data.get('servers')) + 1,
            'Expected an additional server added to the cache'
        )

    def test_celery_add_server_to_cache_bad_uuid(self):
        self.setup_useable_account()
        account_data = self.db.accounts.find_one()
        with self.app.test_client() as c:
            with c.session_transaction() as sess:
                self.setup_user_login(sess)

            with mock.patch(
                'anchor.tasks.config.CELERY_ALWAYS_EAGER',
                True,
                create=True
            ):
                with mock.patch('requests.get') as patched_get:
                    patched_get.return_value.content = None
                    task = self.tasks.check_add_server_to_cache(
                        uuid.uuid4().hex,
                        'iad',
                        '123456',
                        '11111111-2222-3333-4444-55555555555',
                        account_data
                    )
                    assert task is None, (
                        'Expecting task to return None instead of a value'
                    )

        updated_account = self.db.accounts.find_one()
        self.assertEquals(
            account_data,
            updated_account,
            'Data was changed and should not have been from the original data'
        )

    def test_celery_generate_data(self):
        cloud_return = self.setup_servers_details_return()
        with self.app.test_client() as c:
            with c.session_transaction() as sess:
                self.setup_user_login(sess)

            with mock.patch(
                'anchor.tasks.config.CELERY_ALWAYS_EAGER',
                True,
                create=True
            ):
                with mock.patch('requests.get') as patched_get:
                    patched_get.return_value.content = json.dumps(cloud_return)
                    task = self.tasks.generate_account_server_list(
                        '123456',
                        uuid.uuid4().hex,
                        'iad'
                    )

        assert task is None, 'Data returned when it should have been stored'
        account = self.db.accounts.find_one()
        self.assertEquals(
            len(account.get('host_servers')),
            2,
            'Host servers should have two IDs'
        )
        self.assertEquals(
            len(account.get('servers')),
            2,
            'Servers should have two stored in the data'
        )
        assert account.get('region') == 'iad', 'Incorrect region stored'

    def test_celery_generate_data_for_web(self):
        cloud_return = self.setup_servers_details_return()
        with self.app.test_client() as c:
            with c.session_transaction() as sess:
                self.setup_user_login(sess)

            with mock.patch(
                'anchor.tasks.config.CELERY_ALWAYS_EAGER',
                True,
                create=True
            ):
                with mock.patch('requests.get') as patched_get:
                    patched_get.return_value.content = json.dumps(cloud_return)
                    task = self.tasks.generate_account_server_list(
                        '123456',
                        uuid.uuid4().hex,
                        'iad',
                        True
                    )

        account = self.db.accounts.find_one()
        self.assertEquals(
            len(account.get('host_servers')),
            2,
            'Host servers should have two IDs'
        )
        self.assertEquals(
            len(account.get('servers')),
            2,
            'Servers should have two stored in the data'
        )
        assert account.get('region') == 'iad', 'Incorrect region stored'
        assert str(account.get('_id')) == task, (
            'ID returned was not correct for the entry found'
        )

    def test_celery_generate_data_requests_exception(self):
        with self.app.test_client() as c:
            with c.session_transaction() as sess:
                self.setup_user_login(sess)

            with mock.patch(
                'anchor.tasks.config.CELERY_ALWAYS_EAGER',
                True,
                create=True
            ):
                with mock.patch('requests.get') as patched_get:
                    error = patched_get.side_effect = ValueError
                    patched_get.return_value = error
                    self.tasks.generate_account_server_list(
                        '123456',
                        uuid.uuid4().hex,
                        'iad'
                    )

        account = self.db.accounts.find_one()
        assert account, (
            'Account data was not found when it should have been'
        )
        assert len(account.get('host_servers')) == 0, (
            'Host servers listed when there should not have been'
        )
        assert len(account.get('servers')) == 0, (
            'Host servers listed when there should not have been'
        )