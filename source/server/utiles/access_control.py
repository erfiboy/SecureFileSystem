from .log import logger


class ACL(object):
    def __init__(self):
        self._action_types = ["R", "W", "D"]
        self._roles = {}
        self._users = {}
        self._resources = {}
        self._allowed = {}
        self._denied = {}

    def add_role(self, role, actions=[]):
        if not actions:
            return

        for action in actions:
            if action not in self._action_types:
                return

        self._roles.setdefault(role, set())
        self._roles[role].update(actions)

    def remove_role(self, role, actions=[]):
        if not actions:
            return

        for action in actions:
            if action not in self._action_types:
                return

        try:
            del self._roles[role]
        except:
            return

    def allow(self, role, action_type, resources=[]) -> None:
        if not (role or role in self._roles):
            return
        if not (action_type or action_type in self._action_types):
            return

        for resource in resources:
            if not (resource or resource in self._resources):
                continue

            self._allowed[role, action_type.upper(), str(resource)] = True

    def deny(self, role, action_type, resources=[]) -> None:
        if not (role or role in self._roles):
            return
        if not (action_type or action_type in self._action_types):
            return

        for resource in resources:
            if not (resource or resource in self._resources):
                continue

            self._denied[role, action_type.upper(), str(resource)] = True

    def add_user(self, user, roles=[]):
        for role in roles:
            if not (role or role in self._roles):
                return

        self._users.setdefault(user, set())
        self._users[user].update(roles)

    def delete_user_role(self, user, role):
        if not (role or role in self._roles):
            return

        try:
            self._users[user].remove(role)

        except:
            logger.info(f"Error: No role: {role} for user: {user}")

    def add_resource(self, resource, parents=[]):
        self._resources.setdefault(resource, set())
        self._resources[resource].update(parents)

    def is_allowed(self, user, action_type, resource):

        if not (user or user in self._users):
            return
        if not (resource or resource in self._resources):
            return

        roles = self._users[user]
        role = None

        if len(roles) == 1:
            role = list(roles)[0]
        if len(roles) > 1:
            for role in roles:
                if role == "admin":
                    break

        try:
            if self._denied[role, action_type.upper(), str(resource)]:
                logger.info(
                    f"Error: Permission denied. User: {user} has no {action_type} access to resource: {resource}"
                )
                return False
        except:
            pass

        try:

            if self._allowed[role, action_type.upper(), str(resource)]:
                logger.info(
                    "user: {0} has {1} access to " "resource: {2}".format(user, action_type, resource)
                )
                return True
        except Exception:
            logger.info(
                f"Error: Permission denied. {user} has no {action_type} access to resource: {resource}"
            )

            return None
