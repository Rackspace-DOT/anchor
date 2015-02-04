# Copyright 2014 Dave Kludt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import (
    g, render_template, request, redirect, url_for, flash, jsonify, session
)
from flask.ext.classy import FlaskView, route
from flask.ext.restful import Resource, reqparse
from bson.objectid import ObjectId
from models import Region
from anchor.adminbp.decorators import check_perms


import forms
import tasks
import helper


class BaseView(FlaskView):
    route_base = '/'

    def index(self):
        return render_template('index.html')


class LookupView(FlaskView):
    route_base = '/lookup'
    decorators = [check_perms(request)]

    def index(self):
        form = forms.DCSelect()
        form.data_center.choices = helper.gather_dc_choices()
        return render_template('lookup.html', form=form)

    @route('/servers', methods=['POST'])
    @route('/servers/<task_id>')
    def gather_servers(self, task_id=None):
        if request.method == 'POST':
            task = tasks.generate_account_server_list.delay(
                session.get('ddi'),
                session.get('cloud_token'),
                request.json.get('data_center'),
                True
            )
            return jsonify(task_id=task.task_id)
        else:
            status = tasks.check_task_state(task_id)
            if status == 'PENDING':
                return jsonify(state=status, code=204)
            elif status == 'SUCCESS':
                account_id = tasks.get_task_results(task_id)
                account_data = g.db.accounts.find_one(
                    {'_id': ObjectId(account_id)}
                )
                mismatch = False
                if (
                    len(account_data.get('servers')) !=
                    len(account_data.get('host_servers'))
                ):
                    mismatch = True

                return render_template(
                    '_host_breakdown.html',
                    data=account_data,
                    mismatch=mismatch
                )

            return jsonify(state=status, code=500)


class ManagementView(FlaskView):
    route_base = '/manage'
    decorators = [check_perms(request)]

    @route('/regions', methods=['GET', 'POST'])
    def define_available_regions(self):
        settings = g.db.settings.find_one()
        form = forms.RegionSet()
        if request.method == 'POST' and form.validate_on_submit():
            region = Region(request.form)
            if region:
                action, data = '$push', region.__dict__
                if not settings.get('regions'):
                    action, data = '$set', [data]

                g.db.settings.update(
                    {
                        '_id': settings.get('_id')
                    }, {
                        action: {
                            'regions': data
                        }
                    }
                )
                flash('Region successfully added to system', 'success')
                return redirect(
                    url_for(
                        'ManagementView:define_available_regions'
                    )
                )
            else:
                flash(
                    'There was an error with the data being setup correctly,'
                    ' please check the form and try again',
                    'error'
                )
        else:
            if request.method == 'POST':
                flash(
                    'There was a form validation error, please '
                    'check the required values and try again.',
                    'error'
                )

        return render_template(
            'manage/manage_regions.html',
            form=form,
            settings=settings
        )

    @route('/<key>/<action>/<value>')
    def managed_data_actions(self, key, action, value):
        actions = ['activate', 'deactivate', 'remove']
        maps = {
            'regions': {
                'search': 'regions.abbreviation',
                'status': 'regions.$.active',
                'redirect': '/manage/regions',
                'flash_title': value.upper()
            }
        }
        if maps.get(key):
            options = maps.get(key)
            if action in actions:
                found = g.db.settings.find_one(
                    {
                        options.get('search'): value
                    }
                )
                if found:
                    if action == 'remove':
                        keys = options.get('search').split('.')
                        change = {'$pull': {keys[0]: {keys[1]: value}}}
                    else:
                        if action == 'activate':
                            change = {'$set': {options.get('status'): True}}
                        elif action == 'deactivate':
                            change = {'$set': {options.get('status'): False}}

                    g.db.settings.update(
                        {options.get('search'): value},
                        change
                    )
                    flash(
                        '%s was %sd successfully' % (
                            options.get('flash_title'),
                            action
                        ),
                        'success'
                    )
                else:
                    flash(
                        '%s was not found so no action taken' % value.title(),
                        'error'
                    )
            else:
                flash('Invalid action given so no action taken', 'error')
            return redirect(options.get('redirect'))
        else:
            flash('Invalid data key given so no action taken', 'error')
            return redirect('/')


""" API Classes """


class AccountAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('region', type=str, location='json')
        self.reqparse.add_argument('task_id', type=str, location='json')
        super(AccountAPI, self).__init__()

    def get(self, account_id):
        token = helper.check_for_token(request)
        if not token:
            return helper.generate_error(
                'No authentication token provided',
                401
            )

        account_data = g.db.accounts.find_one(
            {
                'account_number': account_id,
                'cache_expiration': {
                    '$gte': helper.get_timestamp()
                }
            }, {
                '_id': 0,
                'servers': 1
            }
        )
        return jsonify(data=account_data)

    def post(self, account_id):
        args = self.reqparse.parse_args()
        token = helper.check_for_token(request)
        if not token:
            return helper.generate_error(
                'No authentication token provided',
                401
            )

        if args.task_id:
            return jsonify(task_status=tasks.check_task_state(args.task_id))

        if not args.region:
            return helper.generate_error(
                'No region specified',
                401
            )

        task_id = tasks.generate_account_server_list.delay(
            account_id,
            token,
            args.region
        )
        return jsonify(task_id=str(task_id))

    def delete(self, account_id):
        token = helper.check_for_token(request)
        if not token:
            return helper.generate_error(
                'No authentication token provided',
                401
            )

        try:
            g.db.accounts.remove({'account_number': account_id})
            return 'Request was successful', 204
        except:
            return helper.generate_error(
                'An error occured that prevented the delete to complete',
                500
            )


class ServerAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('region', type=str, location='json')
        super(ServerAPI, self).__init__()

    def put(self, account_id, server_id):
        """
            Update the account data with the new server, and return True
            or False as to whether the server is by itself on the hypervisor
            Save the data into cache as either way it will still reside on a
            host that has another server or by itself. The answer will be
            correct either way
        """
        args = self.reqparse.parse_args()
        token = helper.check_for_token(request)
        if not token:
            return helper.generate_error(
                'No authentication token provided',
                401
            )

        account_data = g.db.accounts.find_one({'account_number': account_id})
        if not account_data:
            return helper.generate_error(
                'You must initialize before checking a server',
                400
            )

        check_server = g.db.accounts.find_one({'servers.id': server_id})
        if check_server:
            return helper.generate_error(
                'Server has been catalogued already',
                400
            )

        response = tasks.check_add_server_to_cache(
            token,
            args.region,
            account_id,
            server_id,
            account_data
        )
        return jsonify(duplicate=response)