# genotox_db_query
Initial repository with the Django app developed in the first 3 months 


<h2>template</h2> 
the basic HTML template is stored at: myproject/myapp/templates
it's a very basic HTML code to have an initial GUI
the point is to create an user frendly GUI to have as input CAS and details, as output a collection of tables and not the excel file I download right now

<h2>script</h2>
The python script that runs the backend is in: myproject/myapp/views.py
The script is organized like this:
- imports
- db in local upload (you have to modify the working directory)
- import/cleaning functions
- db specific modifying functions
- query functions of db imported and cleaned
- django main function called query_view() function

<h2>urls</h2>
the urls are specified in: myproject/myapp/urls.py

<h2>runs</h2>
to run it in admin mode the command line is "python manage.py runserver"

<h2>media</h2>
DB have been updated. They are not confidential.
