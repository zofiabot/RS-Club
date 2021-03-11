obj.__abstractmethods__ = frozenset()
obj.__class__ = <class 'discord.member.Member'>
obj.__delattr__ = <method-wrapper '__delattr__' of Member object at 0x7f0c112c3200>
obj.__dir__ = <built-in method __dir__ of Member object at 0x7f0c112c3200>
obj.__doc__ = "Represents a Discord member to a :class:`Guild`.\n\n    This implements a lot of the functionality of :class:`User`.\n\n    .. container:: operations\n\n        .. describe:: x == y\n\n            Checks if two members are equal.\n            Note that this works with :class:`User` instances too.\n\n        .. describe:: x != y\n\n            Checks if two members are not equal.\n            Note that this works with :class:`User` instances too.\n\n        .. describe:: hash(x)\n\n            Returns the member's hash.\n\n        .. describe:: str(x)\n\n            Returns the member's name with the discriminator.\n\n    Attributes\n    ----------\n    joined_at: Optional[:class:`datetime.datetime`]\n        A datetime object that specifies the date and time in UTC that the member joined the guild.\n        If the member left and rejoined the guild, this will be the latest date. In certain cases, this can be ``None``.\n    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]\n        The activities that the user is currently doing.\n    guild: :class:`Guild`\n        The guild that the member belongs to.\n    nick: Optional[:class:`str`]\n        The guild specific nickname of the user.\n    pending: :class:`bool`\n        Whether the member is pending member verification.\n\n        .. versionadded:: 1.6\n    premium_since: Optional[:class:`datetime.datetime`]\n        A datetime object that specifies the date and time in UTC when the member used their\n        Nitro boost on the guild, if available. This could be ``None``.\n    "
obj.__eq__ = <bound method Member.__eq__ of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.__format__ = <built-in method __format__ of Member object at 0x7f0c112c3200>
obj.__ge__ = <method-wrapper '__ge__' of Member object at 0x7f0c112c3200>
obj.__getattribute__ = <method-wrapper '__getattribute__' of Member object at 0x7f0c112c3200>
obj.__gt__ = <method-wrapper '__gt__' of Member object at 0x7f0c112c3200>
obj.__hash__ = <bound method Member.__hash__ of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.__init__ = <bound method Member.__init__ of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.__init_subclass__ = <built-in method __init_subclass__ of ABCMeta object at 0x235d2c0>
obj.__le__ = <method-wrapper '__le__' of Member object at 0x7f0c112c3200>
obj.__lt__ = <method-wrapper '__lt__' of Member object at 0x7f0c112c3200>
obj.__module__ = 'discord.member'
obj.__ne__ = <bound method Member.__ne__ of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.__new__ = <built-in method __new__ of type object at 0x7f0c2c4b1260>
obj.__reduce__ = <built-in method __reduce__ of Member object at 0x7f0c112c3200>
obj.__reduce_ex__ = <built-in method __reduce_ex__ of Member object at 0x7f0c112c3200>
obj.__repr__ = <bound method Member.__repr__ of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.__setattr__ = <method-wrapper '__setattr__' of Member object at 0x7f0c112c3200>
obj.__sizeof__ = <built-in method __sizeof__ of Member object at 0x7f0c112c3200>
obj.__slots__ = ('_roles', 'joined_at', 'premium_since', '_client_status', 'activities', 'guild', 'pending', 'nick', '_user', '_state')
obj.__str__ = <bound method Member.__str__ of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.__subclasshook__ = <bound method User.__subclasshook__ of <class 'discord.member.Member'>>
obj._abc_impl = <_abc_data object at 0x7f0c20d1fe40>
obj._client_status = {None: 'offline'}
obj._copy = <bound method Member._copy of <class 'discord.member.Member'>>
obj._from_message = <bound method Member._from_message of <class 'discord.member.Member'>>
obj._from_presence_update = <bound method Member._from_presence_update of <class 'discord.member.Member'>>
obj._get_channel = <bound method Member._get_channel of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj._presence_update = <bound method Member._presence_update of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj._roles = SnowflakeList('Q')
obj._state = <discord.state.ConnectionState object at 0x7f0c22968730>
obj._try_upgrade = <bound method Member._try_upgrade of <class 'discord.member.Member'>>
obj._update = <bound method Member._update of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj._update_from_message = <bound method Member._update_from_message of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj._update_inner_user = <bound method Member._update_inner_user of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj._update_roles = <bound method Member._update_roles of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj._user = <User id=760987693944537149 name='Zo' discriminator='2244' bot=False>
obj.activities = ()
obj.activity = None
obj.add_roles = <bound method Member.add_roles of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.avatar = '5c851bc0575d2ac193c4f69a0cf88106'
obj.avatar_url = <Asset url='/avatars/760987693944537149/5c851bc0575d2ac193c4f69a0cf88106.webp?size=1024'>
obj.avatar_url_as = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.ban = <bound method Member.ban of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.block = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.bot = False
obj.color = <Colour value=0>
obj.colour = <Colour value=0>
obj.create_dm = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.created_at = datetime.datetime(2020, 9, 30, 22, 13, 24, 704000)
obj.default_avatar = <DefaultAvatar.red: 4>
obj.default_avatar_url = <Asset url='/embed/avatars/4.png'>
obj.desktop_status = <Status.offline: 'offline'>
obj.discriminator = '2244'
obj.display_name = 'Zo'
obj.dm_channel = None
obj.edit = <bound method Member.edit of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.fetch_message = <bound method Messageable.fetch_message of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.guild = <Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>
obj.guild_permissions = <Permissions value=37080640>
obj.history = <bound method Messageable.history of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.id = 760987693944537149
obj.is_avatar_animated = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.is_blocked = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.is_friend = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.is_on_mobile = <bound method Member.is_on_mobile of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.joined_at = datetime.datetime(2021, 3, 11, 3, 59, 55, 474632)
obj.kick = <bound method Member.kick of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.mention = '<@760987693944537149>'
obj.mentioned_in = <bound method Member.mentioned_in of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.mobile_status = <Status.offline: 'offline'>
obj.move_to = <bound method Member.move_to of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.mutual_friends = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.name = 'Zo'
obj.nick = None
obj.pending = False
obj.permissions_in = <bound method Member.permissions_in of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.pins = <bound method Messageable.pins of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.premium_since = None
obj.profile = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.public_flags = <PublicUserFlags value=0>
obj.raw_status = 'offline'
obj.relationship = None
obj.remove_friend = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.remove_roles = <bound method Member.remove_roles of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.roles = [<Role id=814878102630170685 name='@everyone'>]
obj.send = <bound method Messageable.send of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.send_friend_request = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.status = <Status.offline: 'offline'>
obj.system = False
obj.top_role = <Role id=814878102630170685 name='@everyone'>
obj.trigger_typing = <bound method Messageable.trigger_typing of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.typing = <bound method Messageable.typing of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.unban = <bound method Member.unban of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.unblock = <bound method flatten_user.<locals>.generate_function.<locals>.general of <Member id=760987693944537149 name='Zo' discriminator='2244' bot=False nick=None guild=<Guild id=814878102630170685 name='Copy Club' shard_id=None chunked=True member_count=8>>>
obj.voice = None
obj.web_status = <Status.offline: 'offline'>
