#!/bin/bash
rm /home/ghar/code/python/cmdb/whooshv2_index/* -rf && mysql -u root -p automation -e "drop database automation;create database automation;" && rm -r migrations/ && python manage.py db init && python manage.py db migrate && python manage.py db upgrade && python manage.py deploy 
