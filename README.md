<<<<<<< HEAD
=======
# genotox_db_2
Initial repository with the Django app developed in the first 3 months. Second attempt.

>>>>>>> a0ae60c77b496b4b1e4b4842a8ba23c502697559
# genotox_db_query
Initial repository with the Django app developed in the first 3 months 


<<<<<<< HEAD
## template 
the basic HTML template is stored at: myproject/myapp/templates
it's a very basic HTML code to have an initial GUI
the point is to create an user frendly GUI to have as input CAS and details, as output a collection of tables and not the excel file I download right now

## script
The python script that runs the backend is in: myproject/myapp/views.py
=======
# template
the basic HTML template is stored at: myfullapp/myapp/templates
it's a very basic HTML code to have an initial GUI
the point is to create an user frendly GUI to have as input CAS and details, as output a collection of tables and not the excel file I download right now

# script
The python script that runs the backend is in: myfullapp/myapp/views.py
>>>>>>> a0ae60c77b496b4b1e4b4842a8ba23c502697559
The script is organized like this:
- imports
- db in local upload (you have to modify the working directory)
- import/cleaning functions
- db specific modifying functions
- query functions of db imported and cleaned
- django main function called query_view() function

<<<<<<< HEAD
## urls
the urls are specified in: myproject/myapp/urls.py

## runs
to run it in admin mode the command line is "python manage.py runserver"

## media
DB have been updated. They are not confidential.

## Por Adrian
Pequeno tutorial para darle un run a la app:
1) cambia la "working direcory" en la primera linea del script in "views.py" (wd= "C:/Users/s265626/Desktop/Trasferimento_dati_BB") con la directory en la cual has descargado la directory "myproject";
2) descarga y instala las packages de python para la run de la app, usando anaconda (o algo similar) y dandole la line de comando: pip install -r /<working_directory>/myproject/requirements.txt;
3) para darle un run usa el comando "python manage.py runserver" despues de ser entrado en la directory "myproject";
4) puedes ver la app en el sito "http://127.0.0.1:8000/myapp/query/" y se llama GenoTox DataBase Query (GTDBQ);
5) el path del template HTML es: "myapp/templates/myapp/query.html";

Por qualquier cosa me puedes escribir o ne hablaremos cuando nos vemos en la oficina.
Gracias amigo! :DD
=======
# urls
the urls are specified in: myfullapp/myapp/urls.py

# runs
to run it in admin mode the command line is manage.py runserver

# media
DB have been updated. They are not confidential.
>>>>>>> a0ae60c77b496b4b1e4b4842a8ba23c502697559
