from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.db.models import Sum, Max, Min, Count
from django.contrib.staticfiles import finders
from django.db.models.functions import Cast
from django.core.paginator import Paginator
from django.core import management
from django.utils import timezone

from subprocess import Popen
from math import floor, ceil

import random
import copy
import os

from .models import *
from .forms import *
from .scripts import *
from .choices import *

# ========================
#   Auxiliary functions
# ========================

# Returns a nice paginator of the iterable for a give window size around the current page 
def getPaginator(request, iterable, pageSize = 20, windowSize = 3, maxNumberPages = 15):
	paginator = Paginator(iterable, pageSize)
	# Try to find the page number, default being 1
	try:
		page = int(request.GET.get('page'))
	except:
		page = 1
	# Check if the page is a valid one
	try:
		paginated = paginator.get_page(page)
	except PageNotAnInteger:
		paginated = paginator.page(1)
	except EmptyPage:
		paginated = paginator.page(paginator.num_pages)
	# Compute pages before and after the current one
	if paginator.num_pages > maxNumberPages + 1:
		pagesBefore = []
		if page - windowSize > 1:
			pagesBefore.append(1)
		if page - windowSize > 2:
			pagesBefore.append("...")
		pagesBefore.extend(iter(range(max(1, page - windowSize), page)))
		pagesAfter = list(range(page + 1, min(page + windowSize + 1, paginator.num_pages + 1)))
		if page + windowSize < paginator.num_pages - 1:
			pagesAfter.append("...")
		if page + windowSize < paginator.num_pages:
			pagesAfter.append(paginator.num_pages)
	else:
		# If there are few pages, we display them all
		pagesBefore = list(range(1, page))
		pagesAfter = list(range(page + 1, paginator.num_pages + 1))
	return (paginator, paginated, page, pagesBefore, pagesAfter)

# ============
#   Renderer  
# ============

def my_render(request, template, args = dict([])):
	args['DATACATEGORY'] = DATACATEGORY
	args['DATATYPES'] = DATATYPES
	args['loginNextUrl'] = request.get_full_path
	return render(request, template, args)

def error_render(request, template, status):
	args = dict([])
	args['DATACATEGORY'] = DATACATEGORY
	args['DATATYPES'] = DATATYPES
	return render(request, template, args, status = status)

def error_400_view(request, exception):
	return error_render(request,'400.html', 400)

def error_403_view(request, exception):
	return error_render(request,'403.html', 403)

def error_404_view(request, exception):
	return error_render(request,'404.html', 404)

def error_500_view(request):
	return error_render(request,'500.html', 500)

# =========
#   Views
# =========

def main(request):
	nbDataSet = DataSet.objects.count()
	nbDataFile = DataFile.objects.count()
	totalSize = DataFile.objects.aggregate(Sum('fileSize'))['fileSize__sum']
	if totalSize != None:
		totalSize = round(totalSize / 1000000000, 2)
	nbDataType = DataFile.objects.values('dataType').distinct().count()
	
	filesWithImages = DataFile.objects.filter(image__isnull = False, dataType__in = ['soc', 'soi', 'toc', 'toi', 'tog', 'mjg', 'wmg', 'pwg', 'wmd'])
	if filesWithImages.exists():
		randomFileWithImage = random.choice(filesWithImages)
	
	(paginator, papers, page, pagesBefore, pagesAfter) = getPaginator(request, Paper.objects.all(), pageSize = 15)
	
	return my_render(request, os.path.join('preflib', 'index.html'), locals())

# Data views
def data(request):
	return my_render(request, os.path.join('preflib', 'data.html'))

def dataFormat(request):
	return my_render(request, os.path.join('preflib', 'dataformat.html'))

def dataMetadata(request):
	metadataPerCategories = [(c[1], Metadata.objects.filter(isActive = True, category = c[0])) for c in METADATACATEGORIES]
	return my_render(request, os.path.join('preflib', 'datametadata.html'), locals())

def alldatasets(request, datacategory):
	(paginator, datasets, page, pagesBefore, pagesAfter) = getPaginator(request, DataSet.objects.filter(category = datacategory).order_by('name'))
	title = findChoiceValue(DATACATEGORY, datacategory)
	return my_render(request, os.path.join('preflib', 'datasetall.html'), locals())

def dataset(request, datacategory, dataSetNum):
	dataset = get_object_or_404(DataSet, category = datacategory, seriesNumber = dataSetNum)
	(paginator, patches, page, pagesBefore, pagesAfter) = getPaginator(request, DataPatch.objects.filter(dataSet = dataset).order_by("name"))
	allFiles = DataFile.objects.filter(dataPatch__dataSet = dataset)
	nbFiles = allFiles.count()
	totalSize = allFiles.aggregate(Sum('fileSize'))['fileSize__sum']
	if totalSize != None:
		totalSize = round(totalSize / 1000, 2)
	allTypes = allFiles.order_by('dataType').values_list('dataType').distinct()
	zipfilepath = os.path.join(
		'data',
		datacategory,
		str(dataset.abbreviation),
		f'{str(dataset.abbreviation)}.zip',
	)

	return my_render(request, os.path.join('preflib', 'dataset.html'), locals())

def datapatch(request, datacategory, dataSetNum, dataPatchNum):
	dataSet = get_object_or_404(DataSet, category = datacategory, seriesNumber = dataSetNum)
	dataPatch = get_object_or_404(DataPatch, dataSet = dataSet, seriesNumber = dataPatchNum)
	dataFiles = DataFile.objects.filter(dataPatch = dataPatch).order_by('-modificationType')
	metadataPerCategories = [(c[1], Metadata.objects.filter(isActive = True, isDisplayed = True, category = c[0])) for c in METADATACATEGORIES]
	filesAndMetadata = []
	for file in dataFiles:
		tmp = []
		for (category, metadata) in metadataPerCategories:
			if tmp2 := [
				(m, DataProperty.objects.get(metadata=m, dataFile=file).getTypedValue())
				for m in metadata
				if DataProperty.objects.filter(metadata=m, dataFile=file).exists()
			]:
				tmp.append((category, tmp2))
		filesAndMetadata.append((file, tmp))

	return my_render(request, os.path.join('preflib', 'datapatch.html'), locals())

def datatypes(request):
	return my_render(request, os.path.join('preflib', 'datatypes.html'))

def dataSearch(request):
	categories = copy.deepcopy(DATACATEGORY)
	types = copy.deepcopy(DATATYPES)
	types.remove(('dat', 'extra data file'))
	types.remove(('csv', 'comma-separated values'))
	allMetadata = Metadata.objects.filter(isActive = True, isDisplayed = True)

	metadataSliderValues = {}
	removeMetadata = []
	# We compute the max and min values of the slider for each metadata
	for m in allMetadata:
		if m.searchWidget == "range":
			props = DataProperty.objects.filter(metadata = m).annotate(floatValue = Cast('value', models.FloatField()))
			maxValue = ceil(props.aggregate(Max('floatValue'))['floatValue__max'])
			minValue = floor(props.aggregate(Min('floatValue'))['floatValue__min'])
			intermediateValue = floor((maxValue - minValue) * 0.3) if maxValue > 30 else floor((maxValue - minValue) * 0.5)
			metadataSliderValues[m] = (minValue, intermediateValue, maxValue)
			# If the min and max are equal, filtering on that metadata is useless so we remove it
			if maxValue == minValue:
				removeMetadata.append(m)
	for m in removeMetadata:
		allMetadata = allMetadata.exclude(pk = m.pk)

	# This is to save the POST data when we change to a different page of the results
	if (
		request.method != 'POST'
		and 'page' in request.GET
		and 'searchDataFilesPOST' in request.session
	):
		request.POST = request.session['searchDataFilesPOST']
		request.method = 'POST'

	allFiles = DataFile.objects.filter(dataType__in = [t[0] for t in types])
	if request.method == 'POST':
		request.session['searchDataFilesPOST'] = request.POST

		categoryFilter = [cat[0] for cat in categories]
		for cat in categories:	
			if request.POST.get(f'{cat[0]}selector') == "no":
				if cat[0] in categoryFilter: categoryFilter.remove(cat[0])
			elif request.POST.get(f'{cat[0]}selector') == "yes":
				categoryFilter = [c for c in categoryFilter if c == cat[0]]
		allFiles = allFiles.filter(dataPatch__dataSet__category__in = categoryFilter)

		dataTypeFilter = [t[0] for t in types]
		for t in types:
			if request.POST.get(f'{t[0]}selector') == "no":
				if t[0] in dataTypeFilter: dataTypeFilter.remove(t[0])
			elif request.POST.get(f'{t[0]}selector') == "yes":
				dataTypeFilter = [x for x in dataTypeFilter if x == t[0]]
		allFiles = allFiles.filter(dataType__in = dataTypeFilter)

		for m in allMetadata:
			if m.searchWidget == "ternary":
				if request.POST.get(f'{m.shortName}selector') == "no":
					propretyQuery = DataProperty.objects.filter(metadata = m, value = True)
					allFiles = allFiles.exclude(dataproperty__in = models.Subquery(propretyQuery.values('pk')))
				elif request.POST.get(f'{m.shortName}selector') == "yes":
					propretyQuery = DataProperty.objects.filter(metadata = m, value = True)
					allFiles = allFiles.filter(dataproperty__in = models.Subquery(propretyQuery.values('pk')))

			elif m.searchWidget == "range":
				propretyQueryMin = (
					DataProperty.objects.filter(metadata=m)
					.annotate(floatValue=Cast('value', models.FloatField()))
					.filter(
						floatValue__lt=float(
							request.POST.get(f'{m.shortName}SliderValueMin')
						)
					)
				)

				allFiles = allFiles.exclude(dataproperty__in = models.Subquery(propretyQueryMin.values('pk')))
				propretyQueryMax = (
					DataProperty.objects.filter(metadata=m)
					.annotate(floatValue=Cast('value', models.FloatField()))
					.filter(
						floatValue__gt=float(
							request.POST.get(f'{m.shortName}SliderValueMax')
						)
					)
				)


				allFiles = allFiles.exclude(dataproperty__in = models.Subquery(propretyQueryMax.values('pk')))

	allFiles = allFiles.order_by('fileName', 'dataType')
	(paginator, dataFiles, page, pagesBefore, pagesAfter) = getPaginator(request, allFiles, pageSize = 40)
	return my_render(request, os.path.join('preflib', 'datasearch.html'), locals())

# About views
def about(request):
	return my_render(request, os.path.join('preflib', 'about.html'))

# Tools views
def tools(request):
	return my_render(request, os.path.join('preflib', 'tools.html'))

# Tools views
def toolsIVS(request):
	return my_render(request, os.path.join('preflib', 'toolsivs.html'))

# Tools views
def toolsKDG(request):
	return my_render(request, os.path.join('preflib', 'toolskdg.html'))

# Tools views
def toolsCRIS(request):
	return my_render(request, os.path.join('preflib', 'toolscris.html'))

# Paper views
def papersView(request):
	(paginator, papers, page, pagesBefore, pagesAfter) = getPaginator(request, Paper.objects.all(), pageSize = 30)
	return my_render(request, os.path.join('preflib', 'papers.html'), locals())

# Archive views
def archive(request):
	return my_render(request, os.path.join('preflib', 'archive.html'))

# User stuff
def userLogin(request):
	print(request.POST)
	error = False
	# The variable that get the next page if there is one
	next = request.POST.get('next', request.GET.get('next', ''))
	if request.method == "POST":
		form = LoginForm(request.POST)
		if form.is_valid():
			# If the form is valid, try to authenticate the user
			username = form.cleaned_data["username"]
			password = form.cleaned_data["password"]
			if user := authenticate(username=username, password=password):
				# If the authentication is right, login the user and redirect to the next page if there is one
				login(request, user)
				if next:
					return HttpResponseRedirect(next)
			else:
				# Else there have been an error during the login
				error = True
	else:
		form = LoginForm()
	return my_render(request, os.path.join('preflib', 'userlogin.html'), locals())

def userLogout(request):
	if not request.user.is_authenticated:
		raise Http404
	logout(request)
	return redirect('preflibapp:main')

def userProfile(request):
	if not request.user.is_authenticated:
		raise Http404
	return my_render(request, os.path.join('preflib', 'userprofile.html'), locals())

def newAccount(request):
	form = CreateUserForm(request.POST or None)
	created = False
	if form.is_valid():
		User.objects.create_user(
			form.cleaned_data["username"], 
			form.cleaned_data["email"], 
			form.cleaned_data["password2"])
		created = True
	return my_render(request, os.path.join('preflib', 'usernewaccount.html'), locals())

# Admin views
def admin(request):
	if not request.user.is_authenticated:
		raise Http404
	return my_render(request, os.path.join('preflib', 'admin.html'))

def adminNews(request):
	if not request.user.is_authenticated:
		raise Http404
	created = False
	# The variable that get the next page if there is one
	if request.method == "POST":
		form = NewsForm(request.POST)
		if form.is_valid():
			now = timezone.now()
			News.objects.create(
				title=form.cleaned_data['title'],
				text=form.cleaned_data['text'],
				publicationDate=f'{str(now.year)}-{str(now.month)}-{str(now.day)}',
				author=request.user,
			)

			created = True
	else:
		form = NewsForm()
	return my_render(request, os.path.join('preflib', 'adminnews.html'), locals())

def adminPaper(request):
	if not request.user.is_authenticated:
		raise Http404
	created = False
	# The variable that get the next page if there is one
	if request.method == "POST":
		form = PaperForm(request.POST)
		if form.is_valid():
			Paper.objects.create(
				title = form.cleaned_data['title'],
				authors = form.cleaned_data['authors'],
				publisher = form.cleaned_data['publisher'],
				year = form.cleaned_data['year'],
				url = form.cleaned_data['url'])
			created = True
	else:
		form = PaperForm()
	return my_render(request, os.path.join('preflib', 'adminpaper.html'), locals())

def adminZip(request):
	if not request.user.is_authenticated:
		raise Http404

	logs = Log.objects.filter(logType = "zip")
	log = logs.latest("publicationDate") if len(logs) > 0 else None
	if (
		request.method == "POST"
		and "zip" in request.POST
		and request.POST['zip'] == "True"
	):
		if finders.find(os.path.join("data", "zip.lock")) is None:
			threaded_management_command("generateZipFiles")
			launchedText = """The script regenerating the zip files has been launched, it will take several 
				minutes to complete, come here to see the log once it will be available. You will be redirected 
				in 5 seconds to the admin panel."""
		else:
			launchedText = """The script regenerating the zip files <strong>has not been launched</strong>, another is already 
				running. You will be redirected in 5 seconds to the admin panel."""

	return my_render(request, os.path.join('preflib', 'adminzip.html'), locals())

def adminAddDataset(request):
	if not request.user.is_authenticated:
		raise Http404

	logs = Log.objects.filter(logType = "dataset")
	log = logs.latest("publicationDate") if len(logs) > 0 else None
	if request.method == "POST":
		if finders.find(os.path.join("datatoadd", "dataset.lock")) is None:
			args = []
			if "all" in request.POST:
				dataDir = finders.find("datatoadd/")
				args.extend(
					str(filename)
					for filename in os.listdir(dataDir)
					if filename.endswith(".zip")
				)

			else:
				args.extend(str(zipFile) for zipFile in request.POST.getlist('dataset'))
			if not args:
				launchedText = """The script adding datasets <strong>has not been launched</strong>, you have not selected any 
				dataset to be added. Please select at least one."""
				noArgs = True
			else:
				threaded_management_command("addDataset", {"file": args})
				launchedText = """The script adding datasets has been launched, it could take some time to proceed, come here 
				to see the log once it will be available. You will be redirected in 5 seconds to the admin panel."""
		else:
			launchedText = """The script adding datasets <strong>has not been launched</strong>, another is already 
			running. You will be redirected in 5 seconds to the admin panel."""
	else:
		dataDir = finders.find("datatoadd")
		files = [
			(filename, os.path.getsize(os.path.join(dataDir, filename)) / 1000)
			for filename in os.listdir(dataDir)
			if filename.endswith(".zip")
		]

		files.sort()

	return my_render(request, os.path.join('preflib', 'adminadddataset.html'), locals())

def adminLog(request, logtype, lognum):
	if not request.user.is_authenticated:
		raise Http404
	log = get_object_or_404(Log, logType = logtype, logNum = lognum)
	title = logtype.capitalize()
	return my_render(request, os.path.join('preflib', 'adminlog.html'), locals())