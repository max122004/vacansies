from rest_framework.permissions import BasePermission

from authentication.models import User


class VacancyCreatePermissions(BasePermission):
    message = 'Adding vacancies for non ht user not allowed.'

    def has_permission(self, request, view):
        if request.user.role == User.HR:
            return True
        else:
            return False