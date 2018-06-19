Past Exam Collection
====
You can see and download past exam collection  
You can upload and edit past exam collection  

## Requirement
python3.6.5  
pip 9.0.1 or latest  
Django==2.0.4  
django-toolbelt==0.0.1  
gunicorn==19.8.1  
whitenoise==3.3.1  
psycopg2==2.7.5  

## Install and Usage
$ git clone https://github.com/koshitake2m2/past_exam_collection  
$ cd past_exam_collection  
$ python3 -m venv myvenv 
$ source myvenv/bin/activate  
(myvenv) $ pip install --upgrade pip  
(myvenv) $ pip install django  
(myvenv) $ cd mysite  
(myvenv) $ mkdir pec/kakomon  
(myvenv) $ python manage.py migrate  
(myvenv) $ python manage.py shell  
 \>>> import pec.func.install as f  
 \>>> f.init_all()  
 \>>> ^D  
(myvenv) $ python manage.py runserver  

And access 'http://localhost:8000/pec' on your browser  

## Licence
Copyright (c) 2018 Takeru Koshimizu  
Released under the MIT license  
https://opensource.org/licenses/mit-license.phpj  

## Author
https://github.com/koshitake2m2/
