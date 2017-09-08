from fabric.api import task, run, sudo, cd, env, prefix, settings

env.hosts = ["fklub.dk"]


@task
def deploy():
    with cd("/data/stregsystem"):
        sudo("systemctl stop apache2.service")
        with settings(sudo_user='stregsystem'):
            sudo("git pull --ff-only")
            with prefix("source /data/stregsystem/env/bin/activate"):
                sudo("pip install -rdeploy_requirements.txt")
                sudo("python manage.py collectstatic --noinput")
                sudo("python manage.py migrate")
        sudo("systemctl start apache2.service")
