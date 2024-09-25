{pkgs, py}:

py.buildPythonPackage {
    pname = "Django-Select2";
    version = "8.1.2";
    src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/7f/af/2fc371e1dea6686b588ab9cd445e55b63248a525f8c90550767a42dd77bb/django_select2-8.1.2.tar.gz";
        sha256 = "sha256-9EaF7hw5CQqt4B4+vCVnAvBWIPPHijwmhECtmmYHCHY=";
    };
    format = "pyproject";
    doCheck = false;
    buildInputs = [];
    checkInputs = [];
    nativeBuildInputs = [];
    propagatedBuildInputs = [
        py.django-appconf
        py.flit-scm
    ];
}

