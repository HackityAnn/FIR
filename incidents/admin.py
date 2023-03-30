from incidents.models import *
from django.contrib import admin
from django.contrib.auth import admin as auth_admin, get_user_model
from django.contrib.auth.forms import UserCreationForm, AdminPasswordChangeForm 
from django.core.exceptions import ValidationError
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

User = get_user_model()


class ACENestedAdmin(admin.TabularInline):
    model = AccessControlEntry

class PasswordlessUserCreationForm(UserCreationForm):
    """
    Class to overwrite UserCreationForm so we
    can put password to not required
    for passwordless accounts
    """

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].required = False
        self.fields['password2'].required = False

class AdminPasswordChangeFormNoUnusablePasswords(AdminPasswordChangeForm):
    """
    Do not allow admins to change passwords
    for accounts that are created with unusable passwords
    as this could lead to persistent accounts after
    disabling them in AD
    """

    def save(self, commit=True):
        """
        Only save the password if the user
        had usable password to begin with
        """
        if not self.user.has_usable_password():
            self.update_errors()
            raise ValidationError(
                self.error_messages[f'User {self.user.username} has unusable password set and cannot be reset'],
                code='unusable_password_cannot_be_reset'
            )

        """
        Original code for save
        ---------------------
        Save the new password.
        """
        password = self.cleaned_data["password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class UserAdmin(auth_admin.UserAdmin):
    """
    The UserAdmin class with some small changes
    compared to the normal UserAdmin
    """
    add_form = PasswordlessUserCreationForm
    change_password_form = AdminPasswordChangeFormNoUnusablePasswords
    inlines = [ACENestedAdmin, ]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')

    def save_model(self, request, obj, form, change):
        if not obj.has_usable_password():
            return
        if not form.cleaned_data['password1']:
            obj.set_unusable_password()
            obj.save()
            return
        else:
            obj.save()
            return


class BusinessLineAdmin(TreeAdmin):
    search_fields = ('name', )
    form = movenodeform_factory(BusinessLine)


class IncidentAdmin(admin.ModelAdmin):
    exclude = ("artifacts", )

admin.site.register(Incident, IncidentAdmin)
admin.site.register(BusinessLine, BusinessLineAdmin)
admin.site.register(BaleCategory)
admin.site.register(Comments)
admin.site.register(LabelGroup)
admin.site.register(Label)
admin.site.register(IncidentCategory)
admin.site.register(Log)
admin.site.register(Profile)
admin.site.register(IncidentTemplate)
admin.site.register(Attribute)
admin.site.register(ValidAttribute)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
