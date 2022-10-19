from django import forms

from datetime import datetime

from .models import *

class SearchForm(forms.Form):
	dataSetExtension = forms.ChoiceField(choices = DATACATEGORY + [('all', 'all')])
	nbAlternativesMax = forms.IntegerField(label = "Maximal number of alternatives")
	nbAlternativesMin = forms.IntegerField(label = "Minimal number of alternatives")
	nbVotersMax = forms.IntegerField(label = "Maximal number of voters")
	nbVotersMin = forms.IntegerField(label = "Minimal number of voters")

class LoginForm(forms.Form):
	username = forms.CharField(label = "Username", max_length = 30)
	password = forms.CharField(label = "Password", widget = forms.PasswordInput)

class CreateUserForm(forms.Form):
	username = forms.CharField(label = "Username", max_length = 30)
	email = forms.EmailField(label = "Email")
	password1 = forms.CharField(min_length = 8, label = "Password", widget = forms.PasswordInput)
	password2 = forms.CharField(min_length = 8, label = "Password again", widget = forms.PasswordInput)

	# Re define __init__ so the label suffix is empty (by default there is a ':')
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('label_suffix', '')
		super(CreateUserForm, self).__init__(*args, **kwargs)

	def clean(self):
		cleaned_data = super(CreateUserForm, self).clean()
		pass1 = cleaned_data.get('password1')
		pass2 = cleaned_data.get('password2')
		email = cleaned_data.get('email')
		username = cleaned_data.get('username')

		if pass1 != pass2:
			raise forms.ValidationError("The two passwords should be the same !")
		if (User.objects.filter(email = email).exists()):
			raise forms.ValidationError("There is already an user using the email address !")
		# Check if the user name id not already used
		if (User.objects.filter(username = username).exists()):
			raise forms.ValidationError("This username is already used by some other user !")
		else:
			return cleaned_data

class EditProfileForm(forms.Form):
	pass

# News form
class PaperForm(forms.Form):
	title = forms.CharField(
		label = 'Title', 
		max_length = 1000,
		widget = forms.TextInput(attrs = {'style': 'width:100%;'}))

	authors = forms.CharField(
		label = 'Authors', 
		max_length = 1000,
		widget = forms.TextInput(attrs = {'style': 'width:100%;'}))

	publisher = forms.CharField(
		label = 'Publisher', 
		max_length = 1000,
		widget = forms.TextInput(attrs = {'style': 'width:100%;'}))

	url = forms.URLField(widget = forms.URLInput(attrs = {'style': 'width:100%;'}))
	year = forms.IntegerField()

	def __init__(self, *args, **kwargs):
		kwargs.setdefault('label_suffix', '')
		super(PaperForm, self).__init__(*args, **kwargs)
		now = datetime.now()
		self.fields['year'] = forms.IntegerField(
			initial = int(now.year),
			label = 'Year', 
			max_value = int(now.year),
			min_value = 2000)