import requests
from bs4 import BeautifulSoup
import json
import os
import shutil
import configparser  # to access the configuration file

sess = requests.Session()  # session to store cookies and remain logged in
moodle_url = 'http://id.bits-hyderabad.ac.in/moodle/'
config = configparser.ConfigParser()
config.read('config.ini')


def login(user=None, pwd=None):
	"""Login to CMS."""
	if not user:
		user = config['CREDS']['username']
		pwd = config['CREDS']['password']
	url = moodle_url + 'login/index.php'
	payload = {'username': user, 'password': pwd, 'Submit': 'Login'}
	r = sess.post(url, data=payload)
	if(r.text.lower().find('invalid login') != -1):  # word only appears when login unsuccessful
		print("Incorrect username/password.")
	elif(r.text.lower().find('dashboard') != -1):  # word only appears when login is successful
		print("Login successful!")
	else:
		print("Error")



def get_attr(text, param, offset=0, end_ch='"'):
	"""Function to extract substring from a text."""
	x = text.find(param) + offset  # left index of the substring
	if x == offset - 1:
		raise EOFError  # in case the parameter is not found
	y = text[x:].find(end_ch)  # right index of the substring
	if y == -1:
		substring = text[x:]
	else:
		substring = text[x:][:y]
	return substring


def get_all_courses():
	"""Scrape CMS and return list of IDS of courses."""
	ids = []
	url = moodle_url + 'course/index.php?categoryid=5&browse=courses&perpage=5'
	print('Getting course IDS of all courses.', end=' ')
	for i in range(0, 168):
		r = sess.get(url, params={'page': str(i)})
		soup = BeautifulSoup(r.text, 'html.parser')
		courses = soup.find_all('div', {'class': 'coursename'})
		for course in courses:
			link = course.a['href']
			c_id = get_attr(link, '=', 1)
			ids.append(c_id + '\n')

	with open('all_ids.txt', 'w') as f:  # store in file to avoid having to scrape everytime
		f.writelines(ids)
	print('Done.')


def get_enrol_payload(c, c_id):
	"""Create POST data for Enrollment."""
	inst = get_attr(c.text, 'instance', 31)
	sesskey = get_attr(c.text, 'sesskey', 10)
	self_enrol = '_qf__{}_enrol_self_enrol_form'.format(inst)
	isexp = 'mform_isexpanded_id_selfheader'
	payload = {
		'id': c_id,
		'instance': inst,
		'sesskey': sesskey,
		self_enrol: 1,
		isexp: 1,
		'submitbutton': 'Enrol me'
	}
	return payload


def course_enrol(c_id):
	"""Enrol into a course."""
	c_url = moodle_url + 'course/view.php'
	form_url = moodle_url + 'enrol/index.php'
	c = sess.get(c_url, params={'id': c_id})
	if c.text[77:84] == 'Course:':
		print('Already enrolled to', c_id)
		return 1
	payload = get_enrol_payload(c, c_id)
	code = sess.post(form_url, data=payload)
	if code.text.lower().find('course:') is -1:
		print('Enrollment unsuccessful for', c_id)
		return -1
	else:
		print('Enrolled to', c_id)
		return 0


def course_unenrol(c_id):
	"""Unenrol from a course."""
	print("Unenrolling from", c_id, end='. ')
	course_url = moodle_url + 'course/view.php'
	c = sess.get(course_url, params={'id': c_id})
	if c.text[77:84] != 'Course:':
		print('Not enrolled to', c_id)
		return
	enrolid = get_attr(c.text, 'enrolid', 8)
	sesskey = get_attr(c.text, 'sesskey', 10)
	unenrol_url = moodle_url + 'enrol/self/unenrolself.php'
	payload = {
		'enrolid': enrolid,
		'confirm': '1',
		'sesskey': sesskey
	}
	sess.post(unenrol_url, data=payload)
	print('Done.')


def fold_contents(fold_url):
	"""Browse a folder and get the download links."""
	f = sess.get(fold_url)
	soup = BeautifulSoup(f.text, 'html.parser')
	contents = get_folders(soup)  # look for sub-directories
	files = soup.find_all('span', {'class': 'fp-filename-icon'})
	for file in files:
		link = file.find('a')  # find the link tag
		file_name = link.find('span', {'class': 'fp-filename'}).text
		file_data = {'name': file_name, 'type': 'file', 'url': link['href']}
		contents.append(file_data)
	return contents


def get_folders(src):
	"""Get all folders, with their contents, from a course/folder."""
	folders = src.find_all('li', {'class': 'activity folder modtype_folder '})
	folds = []
	for fold in folders:
		link = fold.find('a')
		fold_name = link.span.find(text=True, recursive=False)
		fold_url = link['href']
		contents = fold_contents(fold_url)
		folder = {
			'name': fold_name,
			'type': 'folder',
			'contents': contents
		}
		folds.append(folder)
	return folds


def get_course_links(c_id):
	"""Get link of each file for a course."""
	c_url = moodle_url + 'course/view.php'
	r = sess.get(c_url, params={'id': c_id})
	soup = BeautifulSoup(r.text, 'html.parser')
	course_name = soup.find('h3', {'class': 'page-subtitle'}).text
	course = {
		'name': course_name,
		'type': 'course',
		'id': int(c_id),
		'downloaded': False,
		'remain enrolled': 0,
		'contents': []
	}
	course['contents'].extend(get_folders(soup))  # the folders in a course are traversed here

	files = soup.find_all('li', {'class': 'activity resource modtype_resource '})
	for file in files:
		link = file.find('a')
		name = link.span.find(text=True, recursive=False)
		file_data = {'name': name, 'type': 'file', 'url': link['href']}
		course['contents'].append(file_data)
	return course


def download_file(file, folder):
	"""Where the actual downloading happens."""
	file_url = file['url']
	r = sess.get(file_url, stream=True)
	try:
		file_name = get_attr(r.headers['Content-Disposition'], '="', 2, '"')
	except KeyError:
		print('Unable to access file. Check if you are logged in and enrolled.')
		return
	print(f"Downloading {file_name}.", end=' ')
	file['real_name'] = file_name
	file_path = os.path.join(folder, file_name)
	if os.path.isfile(file_path):  # in case the file already exists
		print('Already exists.')
		return
	# with open(file_path, 'wb') as f:
	# 	shutil.copyfileobj(r.raw, f)

	print('Done.')


def download_contents(contents, fold):
	"""Download files of a course/folder."""
	if not os.path.isdir(fold):
		os.makedirs(fold)
		print("Created", fold)

	for content in contents:
		if content['type'] == 'folder':
			new_fold = os.path.join(fold, content['name'])
			download_contents(content['contents'], new_fold)  # Recursively traverse the folders in case of sub-directories.
		elif content['type'] == 'file':
			download_file(content, fold)


def download():
	root_fold = config['DEFAULT']['root']
	if not os.path.isfile('courses_db.json'):
		print("courses_db.json doesn't exist. Run update_db.")
		return
	with open('courses_db.json', 'r') as f:
		data = f.read()
		if not data:
			print('JSON file is empty! Populate it with links first.')
			return
		courses = json.loads(data)

	for course in courses:
		if course['downloaded']:  # To avoid redownloading the course.
			print(f"Already downloaded {course['name']}.")
			continue
		print(f"Getting contents of {course['name']}.")
		fold = os.path.join(root_fold, course['name'])  # folder will be course name.
		download_contents(course['contents'], fold)
		course['downloaded'] = True
		if not course['remain enrolled']:
			course_unenrol(course['id'])

	with open('courses_db.json', 'w') as f:
		f.write(json.dumps(courses, indent=4))


def read_database(ids=[]):
	"""Read courses_db and create a dict from it."""
	if not os.path.isfile('courses_db.json'):
		return [[], ids]
	with open('courses_db.json', 'r') as f:
		data = f.read()
		if not data:  # in case the database is empty
			return [[], ids]
		db = json.loads(data)
		for course in db:
			if str(course['id']) in ids:  # skip courses already in database
				ids.remove(str(course['id']))
	return [db, ids]


def update_db():
	"""Get links for courses and update the courses_db."""
	if not os.path.isfile('all_ids.txt'):
		print("all_ids.txt doesn't exist. Run get_all_courses once.")
		exit(0)
	with open('all_ids.txt', 'r') as f:
		data = f.read()
		if not data:
			print('all_ids.txt is empty. Run get_all_courses once.')
			return
		ids = data.split('\n')
	db, ids = read_database(ids)

	for c_id in ids[215:235]:
		remain_enrolled = course_enrol(c_id)  #TODO: Break up enrolment into small groups.
		if remain_enrolled is -1:  # in case enrollment was unsuccessful
			continue
		course_data = get_course_links(c_id)
		course_data["remain enrolled"] = remain_enrolled
		db.append(course_data)  # add the new course links to the database
		# TODO: modify a previously existing course in case of new links.
		# For now, it just skips the course.

	with open('courses_db.json', 'w') as f:
		f.write(json.dumps(db, indent=4))

def main():
	update_db()
	download()


if __name__ == '__main__':
	login()
	# get_all_courses()  # required on first run
	main()
