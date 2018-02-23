from fabric.api import task, sudo, cd, prefix, settings


@task
def deploy():
    with cd("/data/stregsystem"):
        sudo("systemctl stop apache2.service")
        with settings(sudo_user='stregsystem'):
            sudo("git pull --ff-only")
            with prefix("source /data/stregsystem/venv/bin/activate"):
                sudo("pip install -rrequirements.txt")
                sudo("python manage.py collectstatic --noinput")
                sudo("python manage.py migrate")
        sudo("systemctl start apache2.service")
