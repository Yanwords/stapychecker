#!/bin/bash

#echo "yyy" -S | scp yyy@114.212.87.143:/home/yyy/NamingProject/PyProb/*.py ./
#echo "yyy" -S | scp yyy@114.212.87.143:/home/yyy/NamingProject/PyProb/builtins/*.py ./builtins/
#echo "yyy" -S | scp yyy@114.212.87.143:/home/yyy/NamingProject/PyProb/coordinator/*.py ./coordinator/


sshpass -p "yyy" scp yyy@114.212.87.143:/home/yyy/NamingProject/PyProb/*.py ./
sshpass -p "yyy" scp yyy@114.212.87.143:/home/yyy/NamingProject/PyProb/builtins/*.py ./builtins/
sshpass -p "yyy" scp yyy@114.212.87.143:/home/yyy/NamingProject/PyProb/coordinator/*.py ./coordinator/

#git add -A
#echo -n "Please input the git comments:"
#read comments
#echo "$comments"
#git commit -m "$comments"
#git push origin master
