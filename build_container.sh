#!/usr/bin/env bash

#Sæt variablenavne. Dem bruger vi senere
imgname=stregsystem-container
authorname=FRITFIT
workdir=/home/stregsystemet

#Gem navnet på containeren. Kan også bygges fra bunden af, men så skal man til at bruge
#sin egen package manager til at bootstrappe billedet
#(wink wink nudge nudge til de archtrolde der nu findes i fit)
container=$(buildah from fedora)
#installer dependencies
buildah run $container dnf install python3-pip gcc python3-devel python3.6 -y
#slet midlertidige filer fra package manager
buildah run $container dnf clean all
#lav lokal folder til stregsystemet
buildah run $container mkdir $workdir
#kopier alle stregsystemets filer. TODO: Kopier kun dem, der er nødvendige
buildah add $container ./ $workdir
#sæt workingdir så vi ikke bliver sindssyge af at skulle indeksere den rigtige folder
buildah config --workingdir $workdir $container
#Lav venv
buildah run $container python3.6 -m venv venv
#installer deps fra requirements.txt
buildah run $container /bin/bash -c "source venv/bin/activate && pip install -r requirements.txt"
#Kør migrations
buildah run $container /bin/bash -c "source venv/bin/activate && python manage.py migrate"
#Åben port til stregsystemet
buildah config --port 8000 $container
#Sæt entrypoint
buildah config --cmd '[ "/bin/bash", "-c", "source venv/bin/activate && python manage.py runserver 0:8000" ]' $container
#sæt anden god information
buildah config --author $authorname --label name=$imgname $container
#Commit til et image
buildah commit $container $imgname

#Husk at rydde op efter os selv
buildah rm $container

