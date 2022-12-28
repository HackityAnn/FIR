from django.urls import include, re_path
from rest_framework import routers
from rest_framework.authtoken import views as token_views

from fir_api import views

app_name='fir_api'

# automatic URL routing for API
# include login URLs for the browsable API.
router = routers.DefaultRouter(trailing_slash=False)

router.register(r'users', views.UserViewSet)
router.register(r'incidents', views.IncidentViewSet)
router.register(r'artifacts', views.ArtifactViewSet)
router.register(r'files', views.FileViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'labels', views.LabelViewSet)
router.register(r'attributes', views.AttributeViewSet)
router.register(r'businesslines', views.BusinessLinesViewSet)
router.register(r'incident_categories', views.IncidentCategoriesViewSet)
router.register(r'nuggets', views.NuggetViewSet)

# urls for core FIR components
urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'^token/', token_views.obtain_auth_token),
]
