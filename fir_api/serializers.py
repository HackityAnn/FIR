from django.contrib.auth.models import User
from rest_framework import serializers

from incidents.models import Incident, Artifact, Label, File, IncidentCategory, BusinessLine, Comments, Attribute
from fir_nuggets.models import Nugget


# serializes data from the FIR User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'groups')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:user-detail'}}


# FIR Artifact model
class ArtifactSerializer(serializers.ModelSerializer):
    incidents = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='api:incident-detail')

    class Meta:
        model = Artifact
        fields = ('id', 'type', 'value', 'incidents')
        read_only_fields = ('id',)


# FIR File model

class AttachedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'description', 'url')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:file-detail'}}


class FileSerializer(serializers.ModelSerializer):
    incident = serializers.HyperlinkedRelatedField(read_only=True, view_name='api:incident-detail')

    class Meta:
        model = File
        fields = ('id', 'description', 'incident', 'url', 'file')
        read_only_fields = ('id',)
        extra_kwargs = {'url': {'view_name': 'api:file-download'}}
        depth = 2

# FIR Comment Model

class CommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ('id', 'comment', 'incident', 'opened_by', 'date', 'action')
        read_only_fields = ('id', 'opened_by')


# FIR Label Model

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'name', 'group')
        read_only_fields = ('id',)


# FIR Incident model

class IncidentSerializer(serializers.ModelSerializer):
    detection = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='detection'))
    actor = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='actor'))
    plan = serializers.PrimaryKeyRelatedField(queryset=Label.objects.filter(group__name='plan'))
    file_set = AttachedFileSerializer(many=True, read_only=True)
    comments_set = CommentsSerializer(many=True, read_only=True)

    class Meta:
        model = Incident
        exclude = ['main_business_lines', 'artifacts']
        read_only_fields = ('id', 'opened_by', 'main_business_lines', 'file_set')


# FIR attribute model

class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ('id', 'name', 'value', 'incident')
        read_only_fields = ('id', )

class BusinessLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ('id', 'name')
        read_only_fields = ('id', 'name')

class IncidentCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentCategory
        fields = ('id', 'name', 'is_major')
        read_only_fields = ('id', 'name', 'is_major')

# FIR Nugget model
class NuggetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nugget
        fields = ('raw_data', 'source', 'start_timestampe', 'end_timestamp', 'interpretation', 'incident')
        read_only_fields = ('id', 'found_by')