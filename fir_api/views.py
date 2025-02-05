# for token Generation
import io

from django.conf import settings
from django.db.models.signals import post_save
from django.http import HttpResponse
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core.files import File as FileWrapper
from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import renderers

from fir_api.serializers import UserSerializer, IncidentSerializer, ArtifactSerializer, FileSerializer, CommentsSerializer, LabelSerializer, AttributeSerializer, BusinessLineSerializer, IncidentCategoriesSerializer, NuggetSerializer
from fir_api.permissions import IsIncidentHandler
from fir_artifacts.files import handle_uploaded_file, do_download
from incidents.models import Incident, Artifact, Comments, File, Label, Attribute, BusinessLine, IncidentCategory
from fir_nuggets.models import Nugget


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)


class IncidentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows creation of, viewing, and closing of incidents
    """
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def get_queryset(self):
         queryset = Incident.objects.all()
         id = self.request.query_params.get('id', None)
         category = self.request.query_params.get('category', None)
         subject = self.request.query_params.get('subject', None)
         description = self.request.query_params.get('description', None)
         bl = self.request.query_params.get('bl', None)
         status = self.request.query_params.get('status', None)
         q = Q()
         if id is not None:
            q = q & Q(id__exact=id)
         if category is not None:
             q = q & Q(category__name__icontains=category)
         if subject is not None:
             q = q & Q(subject__icontains=subject)
         if description is not None:
             q = q & Q(description__icontains=description)
         if bl is not None:
             q = q & (Q(concerned_business_lines__in=bl) | Q(main_business_lines__in=[bl]))
         if status is not None:
             q = q & Q(status=status)
         queryset = queryset.filter(q)
         return queryset

    def perform_create(self, serializer):
        instance = serializer.save(opened_by=self.request.user)
        instance.refresh_main_business_lines()
        instance.done_creating()

    def perform_update(self, serializer):
        Comments.create_diff_comment(self.get_object(), serializer.validated_data, self.request.user)
        instance = serializer.save()
        instance.refresh_main_business_lines()


class ArtifactViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    lookup_field = 'value'
    lookup_value_regex = '.+'
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def get_queryset(self):
         queryset = Artifact.objects.all()
         id = self.request.query_params.get('id', None)
         value = self.request.query_params.get('value', None)
         incidents = self.request.query_params.get('incidents', None)
         q = Q()
         if id is not None:
            q = q & Q(id__exact=id)
         if value is not None:
            q = q & Q(value__contains=value)
         if incidents is not None:
            q = q & Q(incidents__exact=incidents)
         queryset = queryset.filter(q)
         return queryset


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comments.objects.all()
    serializer_class = CommentsSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def get_queryset(self):
         queryset = Comments.objects.all()
         id = self.request.query_params.get('id', None)
         incident = self.request.query_params.get('incident', None)
         q = Q()
         if id is not None:
            q = q & Q(id__exact=id)
         if incident is not None:
            q = q & Q(incident__exact=incident)
         queryset = queryset.filter(q)
         return queryset

    def perform_create(self, serializer):
        serializer.save(opened_by=self.request.user)

class LabelViewSet(ListModelMixin, viewsets.GenericViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = (IsAuthenticated,)

class FileViewSet(ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def get_queryset(self):
         queryset = File.objects.all()
         id = self.request.query_params.get('id', None)
         incident = self.request.query_params.get('incident', None)
         q = Q()
         if id is not None:
            q = q & Q(id__exact=id)
         if incident is not None:
            q = q & Q(incident__exact=incident)
         queryset = queryset.filter(q)
         return queryset

    @action(detail=True, renderer_classes=[renderers.StaticHTMLRenderer])
    def download(self, request, pk):
        return do_download(request, pk)

    @action(detail=True, methods=["POST"])
    def upload(self, request, pk):
        files = request.data['files']
        incident = get_object_or_404(Incident, pk=pk)
        files_added = []
        for i, file in enumerate(files):
            file_obj = FileWrapper(io.StringIO(file['content']))
            file_obj.name = file['filename']
            description = file['description']
            f = handle_uploaded_file(file_obj, description, incident)
            files_added.append(f)
        resp_data = FileSerializer(files_added, many=True, context={'request': request}).data
        return HttpResponse(JSONRenderer().render(resp_data), content_type='application/json')


class AttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def perform_create(self, serializer):
        serializer.save()


class BusinessLinesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessLine.objects.all()
    serializer_class = BusinessLineSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)


class IncidentCategoriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IncidentCategory.objects.all()
    serializer_class = IncidentCategoriesSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

class NuggetViewSet(viewsets.ModelViewSet):
    queryset = Nugget.objects.all()
    serializer_class = NuggetSerializer
    permission_classes = (IsAuthenticated, IsIncidentHandler)

    def get_queryset(self):
        queryset = Nugget.objects.all()
        id = self.request.query_params.get('id', None)
        incident_id = self.request.query_params.get('incident_id', None)
        q = Q()
        if incident_id is not None:
           q = q & Q(incident_id__exact=incident_id)
        if id is not None:
           q = q & Q(id__exact=id)
        queryset = queryset.filter(q)
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(found_by=self.request.user)
        e = get_object_or_404(Incident.authorization.for_user(self.request.user, 'incidents.handle_incidents'), pk=instance.incident_id)
        e.refresh_artifacts(instance.raw_data)

    def perform_update(self, serializer):
        instance = serializer.save()
        e = get_object_or_404(Incident.authorization.for_user(self.request.user, 'incidents.handle_incidents'), pk=instance.incident_id)
        e.refresh_artifacts(instance.raw_data)

    def perform_destroy(self, serializer):
        serializer.delete()


# Token Generation ===========================================================

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
