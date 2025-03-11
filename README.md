# genotox_db_query
Initial repository with the Django app developed in the first 3 months 


# template
the basic HTML template is stored at: myfullapp/myapp/templates
it's a very basic HTML code to have an initial GUI
the point is to create an user frendly GUI to have as input CAS and details, as output a collection of tables and not the excel file I download right now

# script
The python script that runs the backend is in: myfullapp/myapp/views.py
The script is organized like this:
- imports
- db in local upload (you have to modify the working directory)
- import/cleaning functions
- db specific modifying functions
- query functions of db imported and cleaned
- django main function called query_view() function

# urls
the urls are specified in: myfullapp/myapp/urls.py

# runs
to run it in admin mode the command line is manage.py runserver

# media
DB have been updated. They are not confidential.
