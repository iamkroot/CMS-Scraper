# CMS-Scraper
Scrapes all contents of the Moodle CMS for BITS Pilani Hyderabad Campus. The main working is made up of two parts:
1. `update_db`, which builds up the database for each file, getting its download link and other metadata.
2. `download`, which is responsible for downloading the files in proper folder heirarchy.

## Features
- Option to either scrape the entire cms (using `get_all_courses`) or the ones you are currently enrolled to (using `get_enrolled_courses`).
    - `get_all_courses` also stores the course ids to a text file, to avoid having to scrape them every time.
	- To manually scrape specific courses, edit the `ids` variable in `update_db` to a list of strings of required course ids.
- The entire database is stored in `courses_db.json`. 
- Download function also extracts all archives for ease of use.

## Installation
1. The external libraries used are `requests`, `BeautifulSoup4` and `rarfile`. Use `pip install -r requirements.txt` to install them.
2. Rename the `sample_config.ini` to `config.ini` and edit the necessary variables in it.
	1. `root` refers to the directory where the contents have to be downloaded, can be absolute or relative.
	2. Set the `unrar_path` to the location of UnRAR.exe after installing [Winrar](https://www.rarlab.com/download.htm). (Generally found at `C:\Program Files (x86)\WinRAR\UnRAR.exe` for Windows)
	3. The `[CREDS]` section should have your login id and password for the CMS.
