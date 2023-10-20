


from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q, F
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from authentication.models import User
from djangoProject import settings
from vacancies.models import Vacancy, Skill
from vacancies.permissions import VacancyCreatePermissions
from vacancies.serializer import VacancyListSerializer, VacancyDetailSerializer, VacancyCreateSerializer, \
    VacancyUpdateSerializer, VacancyDestroySerializer, SkillSerializer


def hello(request):
    return HttpResponse('Hello World!')


class SkillsViewSet(ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


class VacancyView(ListAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancyListSerializer

    #     list(map(lambda x: setattr(x, 'username', x.users.username if x.users else None), page_obj))
    # cложные запросы в базу данных (по вхождению слова)
    def get(self, request, *args, **kwargs):
        vacancy_text = request.GET.get('text', None)
        if vacancy_text:
            self.queryset = self.queryset.filter(
                text__icontains=vacancy_text
            )
        # поиск по связанным таблицам
        # + фильтр на сайтах
        skills = request.GET.getlist('skill', None)
        skills_q = None
        for skill in skills:
            if skills_q is None:
                # Q класс, как обёртка для skills__name__icontains
                skills_q = Q(skills__name__icontains=skill)
            else:
                skills_q |= Q(skills__name__icontains=skill)
        if skills_q:
            self.queryset = self.queryset.filter(skills_q)

        return super().get(request, *args, **kwargs)


class VacancyDetailView(RetrieveAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancyDetailSerializer
    permission_classes = [IsAuthenticated]


class VacancyCreateView(CreateAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancyDetailSerializer
    permission_classes = [IsAuthenticated, VacancyCreatePermissions]


class VacancyUpdateView(UpdateAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancyUpdateSerializer


class VacancyDeleteView(DestroyAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancyDestroySerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_vacancies(request):
    # группировка 2
    user_qs = User.objects.annotate(vacancies=Count('vacancy'))

    paginator = Paginator(user_qs, settings.TOTAL_ON_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    users = []
    for user in page_obj:
        users.append({
            'id': user.id,
            'name': user.username,
            'vacancies': user.vacancies
        })

    response = {
        'items': users,
        'total': paginator.count,
        'num_page': paginator.num_pages,
        # группировка 1
        'avg': user_qs.aggregate(avg=Avg('vacancies'))['avg']
    }

    return JsonResponse(response)


# подсчёт количества запросов 
class VacancyLikeView(UpdateAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancyDetailSerializer

    def put(self, request, *args, **kwargs):
        # класс F теперь представляет собой текущее поле записи
        Vacancy.objects.filter(pk__in=request.data).update(likes=F('likes') + 1)

        return JsonResponse(
            VacancyDetailSerializer(Vacancy.objects.filter(pk__in=request.data), many=True).data,
            safe=False
        )