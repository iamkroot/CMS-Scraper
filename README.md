# CMS-Scraper
Scrapes all contents of the Moodle CMS for BITS Pilani Hyderabad Campus. The main working is made up of two parts:
1. `update_db`, which builds up the database for each file, getting its download link and other metadata.
2. `download`, which is responsible for downloading the files in proper folder heirarchy.

## Installation
1. The external libraries used are `requests`, `BeautifulSoup4` and `rarfile`. Use `pip install` to install them.
2. Rename the `sample_config.ini` to `config.ini` and edit the necessary variables in it.
	1. `root` refers to the directory where the contents have to be downloaded.
	2. Set the `unrar_path` to the location of UnRAR.exe after installing [Winrar](https://www.rarlab.com/download.htm). (Generally found at `C:\Program Files (x86)\WinRAR\UnRAR.exe` for Windows)
	3. The `[CREDS]` section should have your login id and password for the CMS.
