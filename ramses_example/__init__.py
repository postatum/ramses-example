import logging

from pyramid.config import Configurator
from ramses import registry

log = logging.getLogger(__name__)


def my_is_admin(cls, user):
    """ Example of overriding """
    log.info('Checking if user {} is admin'.format(user))
    return 'admin' in user.groups
registry.add('User.is_admin', classmethod(my_is_admin))


@registry.add
def user_self(ace, request, obj):
    """ Give 'update' permission to user that is being created. """
    from pyramid.security import Allow
    return [(Allow, str(obj.username), 'update')]


@registry.add
def item_owner(ace, request, obj):
    """ Give 'update' permission to item owner. """
    from pyramid.security import Allow
    owner = obj.owner
    if hasattr(owner, 'username'):
        owner = owner.username
    if owner is not None:
        return [(Allow, str(owner), 'update')]


@registry.add
def set_item_owner(event):
    """ Set owner of an item. """
    user = getattr(event.view.request, 'user', None)
    if 'owner' not in event.fields and user is not None:
        event.set_field_value('owner', user)


@registry.add
def lowercase(**kwargs):
    """ Make :new_value: lowercase (and stripped) """
    return (kwargs['new_value'] or '').lower().strip()


@registry.add
def encrypt(**kwargs):
    """ Crypt :new_value: if it's not crypted yet """
    import cryptacular.bcrypt
    new_value = kwargs['new_value']
    field = kwargs['field']
    min_length = field.params['min_length']
    if len(new_value) < min_length:
        raise ValueError(
            '`{}`: Value length must be more than {}'.format(
                field.name, field.params['min_length']))

    crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
    if new_value and not crypt.match(new_value):
        new_value = str(crypt.encode(new_value))
    return new_value


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include('ramses')
    config.scan('ramses_example')
    return config.make_wsgi_app()


# Serve loader.io verification file

import os
from pyramid.response import Response
from pyramid.view import view_config

VERIFICATION_FILE = 'loaderio-ab4b2ee8ceda72d10240d5d96860b921.txt'

_here = os.path.dirname(__file__)
_verification = open(os.path.join(_here, VERIFICATION_FILE)).read()
_verification_response = Response(
    content_type='text/plain',
    body=_verification)


@view_config(name=VERIFICATION_FILE)
def verification_view(context, request):
    return _verification_response
